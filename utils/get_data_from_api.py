import pandas as pd

def get_cases():
    return pd.read_json("http://bene.gridpiloten.de:4711/api/cases")

def get_measures():
    return pd.read_json("http://bene.gridpiloten.de:4711/api/measures")

def get_mesures():
    return pd.read_json("http://bene.gridpiloten.de:4711/api/mesures")

def get_source():
    return pd.read_json("http://bene.gridpiloten.de:4711/api/source")

# print(get_cases())
# print(get_measures())
# print(get_mesures())
# print(get_source())