import numpy as np
from scipy.integrate import solve_ivp


def make_ode(N: float, R0: float, a:float, gamma:float):
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


N = 83e6
E0 = 40e3
I0 = 10e3

solution = solve_ivp(
    fun= make_ode(
        N=83_000_000,
        R0=2.0,
        a=1/5.5,
        gamma=1/9.
    ),
    t_span=(0.0, 365.0),
    y0=[
        N - (E0 + I0),
        E0,
        I0,
        0.,
    ],
)

# import matplotlib.pyplot as plt
# plt.plot(solution.t, solution.y[2])
