import sys
sys.path.insert(1, "../../")

from utils.get_data_from_mongodb import DBConnection

import pandas as pd
import numpy as np


# https://towardsdatascience.com/social-distancing-to-slow-the-coronavirus-768292f04296
def base_seir_model(N, t_max=100, dt=0.1):
    # Define parameters
    t_max = 100
    dt = .1
    t = np.linspace(0, t_max, int(t_max / dt) + 1)
    N = 10000
    init_vals = 1 - 1 / N, 1 / N, 0, 0
    alpha = 0.2
    beta = 1.75
    gamma = 0.5
    params = alpha, beta, gamma

    S_0, E_0, I_0, R_0 = init_vals
    S, E, I, R = [S_0], [E_0], [I_0], [R_0]
    alpha, beta, gamma = params
    dt = t[1] - t[0]
    for _ in t[1:]:
        next_S = S[-1] - (beta*S[-1]*I[-1])*dt
        next_E = E[-1] + (beta*S[-1]*I[-1] - alpha*E[-1])*dt
        next_I = I[-1] + (alpha*E[-1] - gamma*I[-1])*dt
        next_R = R[-1] + (gamma*I[-1])*dt
        S.append(next_S)
        E.append(next_E)
        I.append(next_I)
        R.append(next_R)
    return R  #np.stack([S, E, I, R]).T

def preprocess_data(df):
    area_list = []
    for value in df["area"].values:
        if str(value) == 'nan':
            area_list.append(np.NaN)
            continue
        area_list.append(value[-1])

    R0_list = []
    for area in df["area"].values:
        if str(area) == 'nan':
                R0_list.append(np.NaN)
                continue
        if population[population["Country"] == str(area[-1])].empty:
            R0_list.append(np.NaN)
            continue
        else:
            R0_list.append(base_seir_model(N=population[population["Country"] == str(area[-1])]["Value"].values))
    df["base_RO"] = R0_list

    return df

# get data from mongodb
conn = DBConnection()
statsdb = conn.getStatisticDB()
collections = ['cases', 'mesures']
cases, measures = [pd.DataFrame(list(statsdb[col].find({}))) for col in collections]

# get oecd data
# https://stats.oecd.org/Index.aspx?DataSetCode=EDU_DEM
population = pd.read_csv("oecd.csv")
population = population[population['Year'] == 2017]
population = population[population['Sex'] == 'Total']
population = population[population['AGE'] == 'T']
population = population[['Country', 'Value']]
population = population[population['Value'] > 0.]

df = preprocess_data(cases)
print(df)
