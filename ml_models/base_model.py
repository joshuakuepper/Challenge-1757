import sys
sys.path.insert(1, "../")

from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn import svm
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import Imputer

import pandas as pd
import numpy as np

def prepare_data(df, rm_col=["adm", "gender", "ageRange", "area1", "area2", "_id", "source", "Unnamed: 0"]):
    # get only countries
    df["area1"] = df["area1"].astype(str)
    df = df[df["area1"] == 'nan']

    # remove not needed cols
    for col in rm_col:
        del df[col]
    return df

def get_data(df, get_col=["date", "infected", "dead", "recovered", "population"], y_col="inf_-10_R0"):
    x = []
    for index, row in df.iterrows():
        tmp_row = []
        for col in get_col:
            tmp_row.append(row[col])
        x.append(tmp_row)
    y = df[y_col].values

    return x, y


#data = get_data()
data = pd.read_csv("../resources/data/db_data_ml.csv")

print(prepare_data(data))

# preprocess dataset, split into training and test part

X, y = get_data(data)
X, X_imp_t, y, y_imp_t = train_test_split(X, y, test_size=.1, random_state=42)

imp_X = Imputer(missing_values=np.nan, strategy='mean')
imp_X.fit(X_imp_t)
X = imp_X.transform(X)

del_idx = []
for idx, v in enumerate(y):
    if str(v) == "nan":
        del_idx.append(idx)

X = np.delete(X, del_idx, axis=0)
y = np.delete(y, del_idx)

X = StandardScaler().fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.4, random_state=42)

# iterate over classifiers
clf = svm.SVR()
clf.fit(X_train, y_train)
prediction = clf.predict(X_test)
plt.plot(range(len(prediction)), prediction, 'o')
plt.plot(range(len(y_test)), y_test, 'o')
plt.show()
