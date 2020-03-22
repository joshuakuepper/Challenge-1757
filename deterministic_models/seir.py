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

# TODO: This is just an example code block of how a time series with a change in R0
#       at day X can be modelled. This does not belong here and should be moved!
test_extended_seir = False
if test_extended_seir:
    # The following parameters very roughly reproduce the development in Germany.
    # Handfitted voodoo, DO NOT USE THESE NUMBERS!
    N = 83e6
    E0 = 1.e0 # start with a single exposed person, because why not?
    I0 = 0.e0

    R0 = 5. # I could otherwise not reproduce the abrupt increase in confirmed cases and deaths
    a  = 1/2.5 # from https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Modellierung_Deutschland.pdf?__blob=publicationFile
    gamma = 1/10. # also from RKI
    m = 0.0001 # since actual mortality is m/gamma, this amounts to 1 in 1000 infected dying
    theta_M = .8
    theta_E = .0033
    theta_I = .033 # since people are in this stage for about 10 days, about a third of infected people get detected in this model
    day_X = 65. # start curfew on day 65 after first person got exposed
    R0_other = .3 # actual estimate goes here

    solution1 = solve_ivp(
        fun= make_extended_seir_ode(
            N=N,
            R0=R0,
            a=a,
            gamma=gamma,
            m = m,
            theta_M = theta_M,
            theta_E = theta_E,
            theta_I = theta_I,
        ),
        t_span=(0.0, day_X),
        y0=[
            N - (E0 + I0),
            E0,
            I0,
            0.,
            0.,
            0.,
            0.,
            0.,
        ],
    )

    solution2 = solve_ivp(
        fun= make_extended_seir_ode(
            N=N,
            R0=R0_other,
            a=a,
            gamma=gamma,
            m = m,
            theta_M = theta_M,
            theta_E = theta_E,
            theta_I = theta_I,
        ),
        t_span=(day_X, 365.0), # run for a year
        y0=solution1.y[:,-1] # start from solution of uncontained spread
        ,
    )

    # mend arrays together
    y = np.zeros((8,solution1.y.shape[1]+solution2.y.shape[1]))
    y[:,:solution1.y.shape[1]] = solution1.y
    y[:,solution1.y.shape[1]:] = solution2.y

    t = np.zeros((solution1.t.shape[0]+solution2.t.shape[0]))
    t[:solution1.y.shape[1]] = solution1.t
    t[solution1.y.shape[1]:] = solution2.t

    # Plot all the stuff. Dashed lines are 'hidden' magnitudes which do not appear in any statistics.
    # Solid lines are reported numbers of deceased and infected people.
    # Detected magnitudes are shifted 4 days back to account for the time it takes to evaluate a test
    # (again, actual estimate goes here!). The reasoning behind this is the following: If a person gets
    # tested on day x, they will get quarantined at that same day and cannot infect any more people, so
    # they are part of ID already. Because it takes time to evaluate the test, however, they show up in
    # reports only some days later.
    import matplotlib.pyplot as plt

    delay_test = 4.
    plt.plot(t, y[1], '--', label='EU')
    plt.plot(t, y[2], '--', label='IU')
    plt.plot(t, y[3], '--', label='RU')
    plt.plot(t+delay_test, y[4]*100, '-', label='MD x 100') # inflate number of deceased by a factor of
                                                            # 100, because they would otherwise be
                                                            # too few to see. Two y axis labels would be
                                                            # more elegant here, admittedly.
    plt.plot(t+delay_test, y[5], '--', label='ID')
    plt.plot(t+delay_test, y[6], '--', label='RD')
    plt.plot(t, y[7]*100, '--', label='MU x 100')
    D_total = y[4] + y[5] + y[6]
    plt.plot(t+delay_test, D_total, label='D (total)')
    plt.ylim(0.,200000.) # adjust to personal taste
    plt.xlim(30.,80.)
    plt.plot([day_X, day_X],[0.,200000],color='k') # visually mark begin of curfew
    plt.legend(loc=2)
    plt.show()
