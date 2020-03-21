import numpy as np
from scipy.integrate import solve_ivp
from matplotlib import pyplot as plt


class CompartmentModel:
    def __init__(self, name: str, compartments):
        self.name = name
        self.compartments = compartments
        n = len(compartments)
        self.R = np.zeros(shape=(n, n))
        self.MR = np.zeros(shape=(n, n))
        self.MI = np.zeros(shape=(n, n))

        self.param_config = {}
        self.N = 1.0
        self.parameters = {}

    def add_transition(self, source: str, target: str, parameter: str, inhibitor: str = None):
        i = self.compartments.index(source)
        j = self.compartments.index(target)

        if inhibitor is None:
            self.param_config[parameter] = {'type': 'L', 'source': i, 'target': j}
        else:
            k = self.compartments.index(inhibitor)
            self.param_config[parameter] = {'type': 'Q', 'source': i, 'target': j, 'inhibitor': k}

    def set_parameters(self, parameters):
        n = len(self.compartments)
        self.R = np.zeros(shape=(n, n))
        self.MR = np.zeros(shape=(n, n))
        self.MI = np.zeros(shape=(n, n))

        self.parameters = parameters
        self.N = self.parameters["N"]

        for name, param in self.param_config.items():
            i = param['source']
            j = param['target']

            if param['type'] == 'L':
                self.R[i, i] -= parameters[name]
                self.R[j, i] += parameters[name]
            elif param['type'] == 'Q':
                k = param['inhibitor']

                self.MR[i, i] -= parameters[name]
                self.MR[j, i] += parameters[name]
                self.MI[i, k] += 1.0
                self.MI[j, k] += 1.0

    def simulate(self, t_span, initial_value, output_nsteps = 4*365):
        assert len(initial_value) == len(self.compartments)
        z0 = np.array(initial_value)

        def odefun(t, z):
            res =  self.R @ z + (self.MI @ z) * (self.MR @ z/self.N)
            return res

        solution = solve_ivp(odefun, t_span, z0)

        n = len(self.compartments)
        res = {self.compartments[i]: solution.y[i] for i in range(0, n)}
        res['t'] = solution.t
        res['name'] = self.name
        res['parameters'] = self.parameters
        res['compartments'] = self.compartments

        return res


def make_seir_model(N, R0, a, gamma):
    parameters = {"beta": gamma * R0, "a": a, "gamma": gamma, "N": N}
    model = CompartmentModel(name='SEIR_Model', compartments=["S", "E", "I", "R"])
    model.add_transition(source="E", target="I", parameter="a")
    model.add_transition(source="I", target="R", parameter="gamma")
    model.add_transition(source="S", target="E", inhibitor="I", parameter="beta")

    model.set_parameters(parameters)
    return model


def make_seird_model(N, R0, a, gamma, delta):
    parameters = {"beta": gamma * R0, "a": a, "gamma": gamma, "N": N, "delta": delta}
    model = CompartmentModel(name='SEIR_Model', compartments=["S", "E", "I", "R", "D"])
    model.add_transition(source="E", target="I", parameter="a")
    model.add_transition(source="I", target="R", parameter="gamma")
    model.add_transition(source="I", target="D", parameter="delta")
    model.add_transition(source="S", target="E", inhibitor="I", parameter="beta")

    model.set_parameters(parameters)
    return model


if __name__ == '__main__':
    model = make_seird_model(N=83e6, R0=4.0, a=1./5.5, gamma=1/9., delta=0.1)
    N = 83e6
    E0 = 0.0
    I0 = 1.0
    y0 = [N - (E0 + I0), E0, I0, 0., 0.]

    data = model.simulate(t_span=(0., 365.), initial_value=y0)

    time = data["t"]

    plot_opts = {"S": "k--", "E": "b--", "I": "m--", "R": "g", "D": "r"}

    for compartment in data["compartments"]:
        if plot_opts[compartment] is not None:
            plt.plot(time, data[compartment] / 1000000, plot_opts[compartment], label=compartment)

    plt.ylabel('population x 1´000´000')
    plt.xlabel('days')
    plt.legend()
    plt.show()

