library(deSolve)

seir_ode <- function(t,y,par){
  S <- y[1]
  E <- y[2]
  I <- y[3]
  R <- y[4]

  R0 <- par[1]
  a <- par[2]
  gamma <- par[3]
  N <- par[4]
  beta <- gamma*R0

  dS = -beta * S * I / N
  dE = beta * S * I / N - a * E
  dI = a * E - gamma * I
  dR = gamma * I

  list(c(dS,dE,dI,dR))
}

N = 83e6
E0 = 40e3
I0 = 10e3
times <- seq(0,150,by=1)
Y0 <- c(N-(E0-I0),E0,I0,0)
out <- ode(y=Y0,times=times,func=seir_ode,par=c(2.0,1/5.5,1/9,N))
