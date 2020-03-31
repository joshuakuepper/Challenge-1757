// JS Implementation inspited by https://github.com/gabgoh/epcalc
// Last edited: 2020-03-30 by Dominik Linn (dominik.linn@itwm.fraunhofer.de)

const Integrators = {
    Euler    : [[1]],
    Midpoint : [[.5,.5],[0, 1]],
    Heun2    : [[1, 1],[.5,.5]],
    Heun3    : [[1/3,1/3],[2/3, 0, 2/3], [1/4, 0, 3/4]],
    Simpson  : [[1/2,1/2],[1, -1, 2], [1/6, 2/3, 1/6]],
    RK4      : [[.5,.5],[.5,0,.5],[1,0,0,1],[1/6,1/3,1/3,1/6]],
  };

  // f is a func of time t and state y
  // y is the initial state, t is the time, h is the timestep
  // updated y is returned.
  const integrate=(m,f,y,t,h)=>{
    let _y;
    let k;
    for (k=[],ki=0; ki<m.length; ki++) {
      _y=y.slice();
      const dt=ki?((m[ki-1][0])*h):0;
      for (let l=0; l<_y.length; l++) for (let j=1; j<=ki; j++) _y[l]=_y[l]+h*(m[ki-1][j])*(k[ki-1][l]);
      k[ki]=f(t+dt,_y,dt);
    }
    let r;
    for (r=y.slice(),l=0; l<_y.length; l++) for (let j=0; j<k.length; j++) r[l]=r[l]+h*(k[j][l])*(m[ki-1][j]);
    return r;
  };


  function predict(model_para, simulation_para, population_para, InterventionTime, InterventionDuration, InterventionR0, AfterInterventionR0)
  {
    const interpolation_steps = 48; // perform 30 min steps
    const fullsteps = Math.ceil(simulation_para.t_final / simulation_para.dt);

    let steps = fullsteps*interpolation_steps;
    const dt = simulation_para.dt/interpolation_steps;
    const sample_step = interpolation_steps;
    const method = Integrators["RK4"];

    function odefun(t, x)
    {
      // SEIR ODE
      let beta;
      if (t > InterventionTime && t < InterventionTime + InterventionDuration){
        beta = (InterventionR0)/(model_para.D_infectious);
      } else if (t >= InterventionTime + InterventionDuration) {
        beta = AfterInterventionR0/(model_para.D_infectious);
      } else {
        beta = model_para.R0/(model_para.D_infectious);
      }
      const a     = 1/model_para.D_incubation;
      const gamma = 1/model_para.D_infectious;

      const S        = x[0]; // Susectable
      const E        = x[1]; // Exposed
      const I        = x[2]; // Infectious
      const Mild     = x[3]; // Recovering (Mild)
      const Severe   = x[4]; // Recovering (Severe at home)
      const Severe_H = x[5]; // Recovering (Severe in hospital)
      const Fatal    = x[6]; // Dying (Fatal)
      // const R     = x[7]  // Recovered
      // const D     = x[8]  // Deceased

      const p_severe = model_para.p_severe;
      const p_fatal  = model_para.cfr;
      const p_mild   = 1 - p_severe - p_fatal;

      const dS        = -beta*I*S;
      const dE        =  beta*I*S - a*E;
      const dI        =  a*E - gamma*I;
      const dMild     =  p_mild*gamma*I   - (1/model_para.D_recovery_mild)*Mild;
      const dSevere   =  p_severe*gamma*I - (1/model_para.D_hospital_lag)*Severe;
      const dH        =  (1/model_para.D_hospital_lag)*Severe - (1/model_para.D_recovery_severe)*Severe_H;
      const dF        =  p_fatal*gamma*I  - (1/model_para.D_death)*Fatal;
      const dR        =  (1/model_para.D_recovery_mild)*Mild + (1/model_para.D_recovery_severe)*Severe_H;
      const dD        =  (1/model_para.D_death)*Fatal;

      //      0   1   2   3      4        5   6   7   8
      return [dS, dE, dI, dMild, dSevere, dH, dF, dR, dD]
    }

    let v = [1, 0, population_para.I0/(population_para.N-population_para.I0), 0, 0, 0, 0, 0, 0];
    let t = 0;
    let PI  = [];
    let PR  = [];
    let PD  = [];
    let TI = [];
    let PH = [];

    while (steps--) {
      if ((steps+1) % (sample_step) === 0)
      {
        PI.push(population_para.N * v[2]); // Infectious
        PH.push(population_para.N * v[5]); // Hospitalized
        PR.push(population_para.N * v[7]); // Recovered
        PD.push(population_para.N * v[8]); // Deceased

        TI.push(population_para.N*(1-v[0])) // Total infected (cumulative)
      }
      v =integrate(method,odefun,v,t,dt);
      t+=dt
    }
    return {
      "Infectious": PI,
      "Hospitalized": PH,
      "Recovered": PR,
      "Deceased": PD,
      "total_deaths": v[8],
      "cumulative_infected": TI
    }
  }
