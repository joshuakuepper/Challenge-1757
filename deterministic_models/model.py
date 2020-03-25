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
        self.parameters = {"N": self.N}

    def add_transition(self, source: str, target: str, parameter: str, inhibitor: str = None):
        i = self.compartments.index(source)
        j = self.compartments.index(target)

        self.parameters[parameter] = 1.0

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

    def simulate(self, t_span, initial_value, output_nsteps):
        assert len(initial_value) == len(self.compartments)
        z0 = np.array(initial_value)

        def odefun(t, z):
            res =  self.R @ z + (self.MI @ z) * (self.MR @ z/self.N)
            return res

        solution = solve_ivp(odefun, t_span, z0)

        n = len(self.compartments)
        res = {self.compartments[i]: solution.y[i]/self.N*100 for i in range(0, n)}
        res['t'] = solution.t
        res['name'] = self.name
        res['parameters'] = self.parameters
        res['compartments'] = self.compartments

        return res


def generate_model(model_structure):
    compartments = model_structure["compartments"]
    connections = model_structure["connections"]
    name = model_structure["name"]

    model = CompartmentModel(name=name, compartments=compartments)
    for connection in connections:
        if "inhibitor" in connection.keys():
            model.add_transition(source=connection["source"], target=connection["target"],
                                 inhibitor=connection["inhibitor"],
                                 parameter=connection["parameter"])
        else:
            model.add_transition(source=connection["source"], target=connection["target"],
                                 parameter=connection["parameter"])

    return model


if __name__ == '__main__':

    seird = {"name": "SEIRD 1",
             "compartments": ["S", "E", "I", "R", "D"],
             "connections": [
                 {"source": "S", "target": "E", "inhibitor": "I", "parameter": "beta"},
                 {"source": "E", "target": "I", "parameter": "a"},
                 {"source": "I", "target": "R", "parameter": "gamma"},
                 {"source": "I", "target": "D", "parameter": "delta"}
             ]}
    model = generate_model(seird)
    para = model.parameters

    N = 83.0e6
    E0 = 0.0
    I0 = 18000
    y0 = [N - (E0 + I0), E0, I0, 0., 0.]

    gamma = 1./9.
    delta = 0.05
    a = 1./5.5
    R0 = 3.3

    t0 = 0.0
    t1 = 80.0
    t2 = 365.0

    para["N"] = 83e6
    para["beta"] = gamma * R0
    para["a"] = a
    para["gamma"] = gamma
    para["delta"] = delta

    model.set_parameters(para)

    print(model.R)
    print(model.MR)
    print(model.MI)
    data0 = model.simulate(t_span=(t0, t1), initial_value=y0, output_nsteps=8*int(t1-t0))

    S = data0["S"].tolist()
    E = data0["E"].tolist()
    I = data0["I"].tolist()
    R = data0["R"].tolist()
    D = data0["D"].tolist()

    time = data0["t"].tolist()

    scale = model.N / 100.0
    y1 = [S[-1]*scale, E[-1]*scale, I[-1]*scale, R[-1]*scale, D[-1]*scale]
    print(y1)
    para2 = model.parameters
    R0 = 1.0
    para2["beta"] = gamma * R0
    model.set_parameters(para2)

    data1 = model.simulate(t_span=(t1, t2), initial_value=y1, output_nsteps=8*int(t2-t1))

    S.extend(data1["S"].tolist()[1:])
    E.extend(data1["E"].tolist()[1:])
    I.extend(data1["I"].tolist()[1:])
    R.extend(data1["R"].tolist()[1:])
    D.extend(data1["D"].tolist()[1:])
    time.extend(data1["t"].tolist()[1:])

    plot_data = {
        "S": S,
        "E": E,
        "I": I,
        "R": R,
        "D": D
    }
    plot_opts = {"S": None, "E": "b-", "I": "m-", "R": "g", "D": "r-"}


    for compartment in model.compartments:
        if plot_opts[compartment] is not None:
            plt.plot(time, plot_data[compartment], plot_opts[compartment], label=compartment)

    plt.ylabel('population rel. %')
    plt.xlabel('days')
    plt.legend()
    plt.show()

