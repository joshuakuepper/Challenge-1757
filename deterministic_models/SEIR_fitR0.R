library(deSolve)
library(R0)
library(mongolite)
library(jsonlite)
# Load Data
db <- mongo(collection = "cases", db = "jhu", url = "mongodb://root:challenge1757@bene.gridpiloten.de:27017/")
cases <- db$find('{}')
# Convert times
dates <- as.Date(as.POSIXct(cases$date, origin="1970-01-01"))
cases$time <- dates
# Convert Areas
cases$cnt <- cases$area
lscnt <- unlist(cases$cnt)
idx <- seq(1,2*length(cases$area),by=2)
ar <- lscnt[idx]
cnt <- lscnt[idx+1]
cases$country <- cnt
cases$prov <- ar

seir_ode <- function(t,y,par){
  S <- y[1]
  E <- y[2]
  I <- y[3]
  R <- y[4]

  a <- par[1]
  gamma <- par[2]
  N <- par[3]
  tm <- as.integer(round(t))
  beta <- gamma*R0[tm+1]
  dS = -beta * S * I / N
  dE = beta * S * I / N - a * E
  dI = a * E - gamma * I
  dR = gamma * I
  list(c(dS,dE,dI,dR))
}


## R0 estimator for present data
## NOT IMPLEMENTED YET: POPULATION SIZE
## NOT WORKUNG: US
## WORKS WHEN Infected > 20, starts there // should be with diff(Inf)
## R0 ESTIMATOR CANNOT WORK FOR diff(Infected) <= 0 Is set to 1
## USES R0=2 after Data
repro_rate <- function(country){
  cnt_data <- cases[cases$country==country,]
  cnt_data <- cnt_data[cnt_data$prov=="",]
  cnt_data <- cnt_data[!is.na(cnt_data$date),]
  cnt_data <- cnt_data[order(cnt_data$date),]
  GT.flu <- generation.time("gamma", c(2.6,1))
  inff <- as.numeric(cnt_data$infected)
  dinf <- diff(inff)
  dinf[dinf<=0]<-1
  res.G <- estimate.R(dinf, GT=GT.flu, methods=c("EG","ML","SB","TD"))
  #plot(res.G)
  r0<-res.G$estimates$TD$R
  r0 <- r0[1:(length(r0)-1)]
  R0 <- c(as.numeric(r0),rep(2,500))
  N = 80e6
  E0 = 10e3
  I0 = 40
  ts <- which(inff==max(inff[inff<I0]))
  times <- seq(ts,365,by=1)
  Y0 <- c(S=N-(E0-I0),E=E0,I=I0,R=0)
  out <- ode(y=Y0,times=times,func=seir_ode,par=c(1/5.5,1/3,N))
  out.df <- as.data.frame(out)
  out.df[,c(2,3,4,5)]<-out.df[,c(2,3,4,5)]
  #plo <- ggplot(out.df,aes=(x=time)) +geom_line(aes(x=time,y=S,colour="Susceptible"))+geom_line(aes(x=time,y=E,colour="Exposed"))+ geom_line(aes(x=time,y=I,colour="Infected"))  + geom_line(aes(x=time,y=R,colour="Recovered"))
  #plo
  plt<-plot(out.df$I,type="l",log="y",main=paste(country,"Cases (log)"),ylab="Inf.",xlab="t")
  plt<-plt+points(inff[inff>(I0-1)])
  #plt
}
