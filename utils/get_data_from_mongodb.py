# get data from mongodb

#!pip3 install pymongo pandas

import pandas as pd
import pymongo


class DBConnection:
  USER_NAME = "root"
  PASSWORD = "challenge1757"

  @staticmethod
  def getConnection():
    return pymongo.MongoClient("mongodb://" + DBConnection.USER_NAME + ":" + DBConnection.PASSWORD + "@bene.gridpiloten.de:27017/")

  @staticmethod
  def getStatisticDB():
    return DBConnection.getConnection()["jhu"]


collections = [
    'cases',
    'mesures',
]
conn = DBConnection()
statsdb = conn.getStatisticDB()

data = [
    pd.DataFrame(list(statsdb[col].find({})))
    for col in collections
]
cases, measures = data
# cases.to_csv('cases.csv', index=False)