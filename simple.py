#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 21 10:46:58 2020

@author: ortmann_j
"""

import numpy as np
import matplotlib.pyplot as plt

N = 83e6

m = 13.3
p  = 0.33/(97000/7290)

I = [10]
S = [N-I[0]]
R = [0]

L = np.log(2)/5/10 # the median of an exp(L) is ln(2)/L and we have 5 days median



time_length = 300
time_span=range(time_length)



for t in time_span:
    A = np.random.binomial(N*m/2, S[-1]*I[-1]*p/(N**2))
    B = np.random.binomial(I[-1], 1-np.exp(-L))

    S.append(S[-1]-A)
    I.append(I[-1]+A-B)
    R.append(R[-1]+B)    


plt.figure()
plt.title("Very simple model, 13.3 contacts per day, p = {}".format(p))
plt.xlabel("Days since outbreak")
plt.ylabel("Number of cases")
plt.plot(S,'b-',label="susceptible")
plt.plot(I,'r-',label="infected")
plt.plot(R,'k-',label="removed")
plt.legend()

plt.savefig("very-simple.png")