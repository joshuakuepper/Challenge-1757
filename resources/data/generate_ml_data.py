import sys
sys.path.insert(1, "../../")

from utils.get_data_from_api import get_cases, get_measures

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import functools

def conjunction(*conditions):
    return functools.reduce(np.logical_and, conditions)

def preprocess_data(df, population):
    # calculate N3
    r0_values = dict({
        "inf_10": [],
        "inf_5": [],
        "inf_2": [],
        "inf_-10": [],
        "inf_-5": [],
        "inf_-2": [],
        "inf_10_R0": [],
        "inf_-10_R0": [],
        "inf_5_R0": [],
        "inf_-5_R0": [],
        "inf_2_R0": [],
        "inf_-2_R0": [],
        "inf_10_R0_lin": [],
        "inf_-10_R0_lin": [],
        "inf_5_R0_lin": [],
        "inf_-5_R0_lin": [],
        "inf_2_R0_lin": [],
        "inf_-2_R0_lin": [],
    })
    for index, row in df.iterrows():

        cur_df = df[df['area1'] == row['area1']]
        cur_df = cur_df[cur_df['area2'] == row['area2']]

        for time in [-10, -5, -2, 2, 5, 10]:
            if time > 0:
                cur_df = cur_df[cur_df['date'] >= row['date'] + time]
            else:
                cur_df = cur_df[cur_df['date'] <= row['date'] + time]
            if cur_df.empty:
                r0_values["inf_" + str(time)].append(np.NaN)
                r0_values["inf_" + str(time) + "_R0"].append(np.NaN)
                r0_values["inf_" + str(time) + "_R0_lin"].append(np.NaN)
                continue
            r0_values["inf_" + str(time)].append(cur_df.sort_values(by=['date']).iloc[0]['infected'])

            if str(row['infected']) == 'nan' or str(row['infected']) == '' or int(row['infected']) == 0 or \
                    cur_df.sort_values(by=['date']).iloc[0]['infected'] == 'nan' or \
                    cur_df.sort_values(by=['date']).iloc[0]['infected'] == '' or \
                    int(cur_df.sort_values(by=['date']).iloc[0]['infected'] )== 0:
                r0_values["inf_" + str(time) + "_R0"].append(np.NaN)
                r0_values["inf_" + str(time) + "_R0_lin"].append(np.NaN)
            else:
                inf_cur = int(row['infected'])
                inf_n_days = int(cur_df.sort_values(by=['date']).iloc[0]['infected'])
                if time > 0:
                    r0_values["inf_" + str(time) + "_R0"].append(inf_n_days / inf_cur)
                    r0_values["inf_" + str(time) + "_R0_lin"].append((inf_n_days - inf_cur) / abs(time) * 10)
                else:
                    r0_values["inf_" + str(time) + "_R0"].append(inf_cur / inf_n_days)
                    r0_values["inf_" + str(time) + "_R0_lin"].append((inf_cur - inf_n_days) / abs(time) * 10)

    dict_db = pd.DataFrame.from_dict(r0_values, orient='index').transpose()
    df = pd.concat([df, dict_db], axis=1)

    print(dict_db)
    print(df)

    population_list = []
    for area in df["area2"].values:
        if str(area) == 'nan':
                population_list.append(np.NaN)
                continue
        if population[population["Country Name"] == str(area)].empty:
            population_list.append(np.NaN)
            continue
        else:
            population_list.append(population[population["Country Name"] == str(area)][2018.0].values[0])
    df["population"] = population_list

    return df

def con_db():
    # get data from mongodb
    conn = DBConnection()
    statsdb = conn.getStatisticDB()
    collections = ['cases', 'mesures']
    cases, measures = [pd.DataFrame(list(statsdb[col].find({}))) for col in collections]

    # Convert Time into days in numbers from 2020-01-01
    cases['date'] = pd.to_datetime(cases['date'], unit='s')
    FMT = '%Y-%m-%d %H:%M:%S'
    date = cases['date']
    cases['date'] = date.map(lambda x: (datetime.strptime(str(x), FMT) - datetime.strptime("2020-01-01 00:00:00", FMT)).days)

    # get population data
    population = pd.read_excel("http://api.worldbank.org/v2/en/indicator/SP.POP.TOTL?downloadformat=excel", header=None)
    population = population.iloc[3:]
    headers = population.iloc[0]
    population = pd.DataFrame(population.values[1:], columns=headers)

    # convert array to str for now
    area1_list = []
    area2_list = []
    for value in cases.area.values.tolist():
        if str(value) == 'nan':
            area1_list.append(np.NaN)
            area2_list.append(np.NaN)
        else:
            area1_list.append(value[0])
            area2_list.append(value[1])
    cases['area1'] = area1_list
    cases['area2'] = area2_list
    del cases['area']

    # Get country mapping
    map_country = pd.read_csv("country_mapping.csv", sep=";")
    for index, row in map_country.iterrows():
        cases.loc[cases['area2'] == row['cases'], 'area2'] = row['world_bank']

    return cases[cases['source'] == 'JHU'], population

def get_data():
    cases, population = con_db()
    df = preprocess_data(cases, population)
    return df

def save_data():
    df = get_data()
    df.to_csv("db_data_ml.csv")

def get_simple_R0_data(not_needed_cols=None, measures_list=None, source=None):

    if not_needed_cols is None:
        not_needed_cols = ["Unnamed: 0", "_id", "sourceFull", "actions"]

    if measures_list is None:
        measures_list = ["schools_closed",
                         "traveller_quarantine",
                         "border_control",
                         "closure_leisureandbars",
                         "lockdown",
                         "home_office",
                         "primary_residence",
                         "test_limitations"]

    if source is None:
        source = ["JHU", "RKI"]

    cases = pd.read_csv("cases.csv")
    measures = pd.read_csv("measures.csv")

    # filter data shuffle around
    cases = cases[cases["source"].isin(source)]
    # convert array to str for now
    region_0 = []
    region_1 = []
    for value in cases.adm.values.tolist():
        if str(value) == 'nan':
            region_0.append(-999)
            region_1.append(-999)
            continue
        value = value.replace("]", "").replace("[", "").replace("\'", "").split(",")
        region_0.append(value[0])
        region_1.append(value[1])
    cases['region_0'] = region_0
    cases['region_1'] = region_1
    del cases['adm']

    # convert array to str for now
    region_0 = []
    region_1 = []
    region_2 = []
    for value in measures.adm.values.tolist():
        value = value.replace("]", "").replace("[", "").replace("\'", "").split(",")
        if value[0] == "":
            region_0.append(-999)
            region_1.append(-999)
            region_2.append(-999)
            continue
        region_0.append(value[0])
        region_1.append(value[1])
        region_2.append(value[1])
    measures['region_0'] = region_0
    measures['region_1'] = region_1
    measures['region_2'] = region_2
    del measures['adm']

    # convert time into days in numbers from 2020-01-01
    FMT = '%Y-%m-%d %H:%M:%S%z'
    for df in [cases, measures]:
        date = df['date']
        df['date'] = date.map(
            lambda x: (datetime.strptime(str(x), FMT) - datetime.strptime("2020-01-01 00:00:00+00:00", FMT)).days)

    # remove not needed columns
    for col in not_needed_cols:
        try:
            del cases[col]
        except:
            print("Column {} not in dataset cases".format(col))
        try:
            del measures[col]
        except:
            print("Column {} not in dataset measures".format(col))

    # filter data if there is no region
    cases = cases[cases["region_0"] != -999]
    measures = measures[measures["region_0"] != -999]

    # create empty columns
    for measure in measures_list:
        cases[measure + "_first_event"] = -999

    # # find date per country when measure was first taken
    # first_time_per_measure = []
    # for measure in measures_list:
    #     tmp_measure = []
    #     for idx, row in cases.iterrows():
    #         region_0_cut = measures["region_0"] == row["region_0"]
    #         measure_cut = measures[measure] == 1.0
    #         tmp_measure.append(np.min(measures[conjunction(region_0_cut, measure_cut)]["date"]))
    #     first_time_per_measure.append(tmp_measure)
    # np.save("first_time_per_measure", first_time_per_measure)
    first_time_per_measure = np.load("first_time_per_measure.npy")
    print(cases, measures, first_time_per_measure)

not_needed_cols=["Unnamed: 0", "_id", "sourceFull", "actions"]
measures_list=["schools_closed",
               "traveller_quarantine",
               "border_control",
               "closure_leisureandbars",
               "lockdown",
               "home_office",
               "primary_residence",
               "test_limitations"]
source = ["JHU"]

get_simple_R0_data(not_needed_cols, measures_list, source)



# get_cases().to_csv("cases.csv")
# get_measures().to_csv("measures.csv")