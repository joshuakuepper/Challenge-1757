from typing import Callable

import numpy as np
from scipy.integrate import solve_ivp


def make_ode(N: float, R0: float, a: float, gamma: float) -> Callable:
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


N = 83e6   # Total number of people
E0 = 40e3  # Initial number of Exposed people
I0 = 10e3  # Initial number of Infectious people

solution = solve_ivp(
    fun= make_ode(
        N=N,
        R0=2.0,
        a=1/5.5,
        gamma=1/9.
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
