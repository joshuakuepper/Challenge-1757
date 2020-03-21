from typing import Callable

import numpy as np
from scipy.integrate import solve_ivp


def make_seir_ode(N: float, R0: float, a: float, gamma: float) -> Callable:
    """
    Build a SEIR model that is solvable by scipy.integrate.solve_ivp()

    Note: Normal population birth- and death rates are ignored (i.e. assumed to be zero)

    Parameters
    ----------
    N
        Total number of people in population
    R0
        Basic reproduction number (https://en.wikipedia.org/wiki/Basic_reproduction_number)
    a
        Incubation rate (going from S -> E)
    gamma
        Recovery rate (going from I -> R)

    Returns
    -------
    Function that can be used as input to scipy.integrate.solve_ivp()
    """
    beta = gamma * R0

    def seir_ode(t, y, *f_args):
        S = y[0]
        E = y[1]
        I = y[2]
        R = y[3]

        dy = np.zeros_like(y)

        dy[0] = -beta * S * I / float(N)
        dy[1] = beta * S * I / float(N) - a * E
        dy[2] = a * E - gamma * I
        dy[3] = gamma * I
        return dy

    return seir_ode

def make_extended_seir_ode(N: float, R0: float, a: float, gamma: float, \
        m:float, theta_M:float, theta_E:float, theta_I:float) -> Callable:
    """
    Build an extended SEIR model that is solvable by scipy.integrate.solve_ivp()

    Note: Normal population birth- and death rates are ignored (i.e. assumed to be zero)

    Standard SEIR model is extended by the labels M (deceased), U (undetected),
    D (detected). It is assumed that mortality is equal for tested and untested
    persons, and that persons who have been tested positively are quarantined and
    cannot infect any further people.

    Parameters
    ----------
    N
        Total number of people in population
    R0
        Basic reproduction number (https://en.wikipedia.org/wiki/Basic_reproduction_number)
    a
        Incubation rate (going from S -> E)
    gamma
        Recovery rate (going from I -> R)
    m
        Mortality per day (going from I -> M)
        (overall mortality is given by m/gamma)
    theta_M
        Chance that a deceased person will be tested after death
    theta_E
        Chance that an exposed person will be tested per day
    theta_I
        Chance that an infectious person will be tested per day

    Returns
    -------
    Function that can be used as input to scipy.integrate.solve_ivp()
    """
    beta = gamma * R0

    def extended_seir_ode(t, y, *f_args):
        S  = y[0] # susceptible
        EU = y[1] # exposed and not tested
        IU = y[2] # infectious and not tested
        RU = y[3] # recovered and not tested
        MD = y[4] # deceased, positive test
                  # (test can be performed before or after death)
        ID = y[5] # quarantined, positive test
        RD = y[6] # recovered, positive test
        MU = y[7] # deceased and not tested

        dy = np.zeros_like(y)

        dy[0] = -beta * S * IU / float(N)
        dy[1] = beta * S * IU / float(N) - a * EU - theta_E * EU
        dy[2] = a * EU - gamma * IU - m * IU - theta_I * IU
        dy[3] = gamma * IU
        dy[4] = m * theta_M * IU + m * ID
        dy[5] = EU * theta_E + IU * theta_I - m * ID - gamma * ID
        dy[6] = gamma * ID
        dy[7] = m * (1-theta_M) * IU
        return dy

    return extended_seir_ode


N = 83e6   # Total number of people
E0 = 40e3  # Initial number of Exposed people
I0 = 10e3  # Initial number of Infectious people

solution = solve_ivp(
    fun= make_seir_ode(
        N=N,
        R0=2.0,
        a=1/5.5,
        gamma=1/3.
    ),
    t_span=(0.0, 365.0),  # Integration time range (days)
    y0=[
        N - (E0 + I0),  # Initial number of Susceptible people
        E0,
        I0,
        0.,  # Initial number of Recovered people
    ],
)

# import matplotlib.pyplot as plt
# plt.plot(solution.t, solution.y[2])  # plot the number of Infectious people vs time
# plt.plot(solution.t, solution.y[3])  # plot the number of Recovered people vs time
