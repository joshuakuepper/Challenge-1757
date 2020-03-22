const Integrators = {
    Euler    : [[1]],
    Midpoint : [[.5,.5],[0, 1]],
    Heun     : [[1, 1],[.5,.5]],
    Ralston  : [[2/3,2/3],[.25,.75]],
    K3       : [[.5,.5],[1,-1,2],[1/6,2/3,1/6]],
    SSP33    : [[1,1],[.5,.25,.25],[1/6,1/6,2/3]],
    SSP43    : [[.5,.5],[1,.5,.5],[.5,1/6,1/6,1/6],[1/6,1/6,1/6,1/2]],
    RK4      : [[.5,.5],[.5,0,.5],[1,0,0,1],[1/6,1/3,1/3,1/6]],
    RK38     : [[1/3,1/3],[2/3,-1/3,1],[1,1,-1,1],[1/8,3/8,3/8,1/8]]
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
  
  function predict(model, model_para, simulation_para, population_para, InterventionTime, InterventionDuration, InterventionAmt)
  {
    if (model === "seird")
    {
      return predict_seird(simulation_para, model_para, population_para, InterventionTime, InterventionDuration, InterventionAmt);
    }
    else if(model === "seird_extended")
    {
      return predict_seird_ext(simulation_para, model_para, population_para, InterventionTime, InterventionDuration, InterventionAmt);
    }
    else // fallback: seir with default para
    {
      console.log("Wrong Model!");
      return predict_seird(simulation_para, model_para, population_para, InterventionTime, InterventionDuration, InterventionAmt);
    }
  }



  function predict_seird(simulation_para, model_para, population_para, InterventionTime, InterventionDuration, InterventionAmt)
  {
    const interpolation_steps = 40;
    const fullsteps = Math.ceil(simulation_para.t_final / simulation_para.dt);
    let steps = fullsteps*interpolation_steps;
    console.log(steps);
    const dt = simulation_para.dt/interpolation_steps;
    const sample_step = interpolation_steps;
    const method = Integrators["RK4"];

    function odefun(t, x)
    {
      // SEIRD ODE
      let beta;
      if (t > InterventionTime && t < InterventionTime + InterventionDuration){
        beta = (InterventionAmt)/(model_para.D_infectious);
      } else if (t > InterventionTime + InterventionDuration) {
        beta = 0.5*model_para.R0/(model_para.D_infectious);
      } else {
        beta = model_para.R0/(model_para.D_infectious);
      }
      const a     = 1/model_para.D_incubation;
      const gamma = 1/model_para.D_infectious;

      const S        = x[0]; // Susceptible
      const E        = x[1]; // Exposed
      const I        = x[2]; // Infectious
      const F        = x[3]; // Fatal
      // var R       = x[4] // Recovered

      const p_fatal  = model_para.cfr;

      const dS        = -beta*I*S;
      const dE        =  beta*I*S - a*E;
      const dI        =  a*E - gamma*I;
      const dFatal    =  p_fatal*gamma*I;
      const dR        = (1 - p_fatal) * gamma * I;

      //      0   1   2   3      4
      return [dS, dE, dI, dFatal, dR]
    }

    let v = [1, 0, population_para.I0/(population_para.N-population_para.I0), 0, 0];

    let t = 0;
    let PI  = [];
    let PR  = [];
    let PD  = [];
    let TI = [];

    while (steps--)
    {
      if ((steps+1) % (sample_step) === 0)
      {
        PI.push(population_para.N * v[2]);  // Infected
        PR.push(population_para.N * v[4]);  // Recovered
        PD.push(population_para.N * v[3]);  // Dead

        TI.push(population_para.N*(1-v[0]))
      }
      v =integrate(method,odefun,v,t,dt);
      t+=dt
    }
    return {
      "Infected": PI,
      "Recovered": PR,
      "Dead": PD,
      "total_deaths": population_para.N*v[3],
      "total_infected": TI
    }
  }

  function predict_seird_ext(simulation_para, model_para, population_para, InterventionTime, InterventionDuration, InterventionAmt)
  {
    const interpolation_steps = 40;
    const fullsteps = Math.ceil(simulation_para.t_final / simulation_para.dt);
    console.log(fullsteps);
    let steps = fullsteps*interpolation_steps;
    const dt = simulation_para.dt/interpolation_steps;
    const sample_step = interpolation_steps;
    const method = Integrators["RK4"];

    function odefun(t, x)
    {
      // SEIR ODE
      let beta;
      if (t > InterventionTime && t < InterventionTime + InterventionDuration){
        beta = (InterventionAmt)/(model_para.D_infectious);
      } else if (t > InterventionTime + InterventionDuration) {
        beta = 0.5*model_para.R0/(model_para.D_infectious);
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
      const Fatal    = x[6]; // Recovering (Fatal)
      // var R_Mild   = x[7] // Recovered
      // var R_Severe = x[8] // Recovered
      // var R_Fatal  = x[9] // Dead

      const p_severe = model_para.p_severe;
      const p_fatal  = model_para.cfr;
      const p_mild   = 1 - p_severe - p_fatal;

      const dS        = -beta*I*S;
      const dE        =  beta*I*S - a*E;
      const dI        =  a*E - gamma*I;
      const dMild     =  p_mild*gamma*I   - (1/model_para.D_recovery_mild)*Mild;
      const dSevere   =  p_severe*gamma*I - (1/model_para.D_hospital_lag)*Severe;
      const dSevere_H =  (1/model_para.D_hospital_lag)*Severe - (1/model_para.D_recovery_severe)*Severe_H;
      const dFatal    =  p_fatal*gamma*I  - (1/model_para.D_death)*Fatal;
      const dR_Mild   =  (1/model_para.D_recovery_mild)*Mild;
      const dR_Severe =  (1/model_para.D_recovery_severe)*Severe_H;
      const dR_Fatal  =  (1/model_para.D_death)*Fatal;
      //      0   1   2   3      4        5          6       7        8          9
      return [dS, dE, dI, dMild, dSevere, dSevere_H, dFatal, dR_Mild, dR_Severe, dR_Fatal]
    }

    let v = [1, 0, population_para.I0/(population_para.N-population_para.I0), 0, 0, 0, 0, 0, 0, 0];
    let t = 0;
    let PI  = [];
    let PR  = [];
    let PD  = [];
    let TI = [];

    while (steps--) {
      if ((steps+1) % (sample_step) === 0)
      {
        PI.push(population_para.N * v[2]);           // Infected
        PR.push(population_para.N * (v[7] + v[8]));  // Recovered
        PD.push(population_para.N * v[9]);           // Dead

        TI.push(population_para.N*(1-v[0]))
      }
      v =integrate(method,odefun,v,t,dt);
      t+=dt
    }
    return {
      "Infected": PI,
      "Recovered": PR,
      "Dead": PD,
      "total_deaths": population_para.N*v[6],
      "total_infected": TI
    }
  }
