import sys
sys.path.insert(1, "../../")

from utils.get_data_from_mongodb import DBConnection

import pandas as pd
import numpy as np
from datetime import datetime,timedelta

def preprocess_data(df):
    # calculate N3
    N3 = []
    R0_list = []
    for index, row in df.iterrows():
        cur_df = df[df['area1'] == row['area1']]
        cur_df = cur_df[cur_df['area2'] == row['area2']]
        cur_df = cur_df[cur_df['date'] >= row['date'] + 10]
        if cur_df.empty:
            N3.append(np.NaN)
            R0_list.append(np.NaN)
            continue
        N3.append(cur_df.sort_values(by=['date']).iloc[0]['infected'])
        if str(row['infected']) == 'nan' or str(row['infected']) == '':
            R0_list.append(0)
        elif int(row['infected']) == 0:
            R0_list.append(0)
        else:
            R0_list.append(int(cur_df.sort_values(by=['date']).iloc[0]['infected']) / int(row['infected']))
    df["N3"] = N3
    df["cur_R0"] = R0_list

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
population  = pd.DataFrame(population.values[1:], columns=headers)

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

df = preprocess_data(cases)

print(df)
df.to_csv("db_data_ml.csv")

