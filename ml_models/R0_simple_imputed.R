library(jsonlite)
library(readxl)
library(tidyverse)
library(httr)
library(lubridate)

####
# Get data
####


#Per API:
url  <- "http://bene.gridpiloten.de:4711"
path <- "/api/cases"
raw.result <- GET(url = url, path = path)
raw.result2 <- rawToChar(raw.result$content)
this.content <- fromJSON(raw.result2)

colnames(this.content)

cases.df <- data.frame(country=as.character(sapply(this.content$adm,FUN=function(x){return(x[1])})), region1=as.character(sapply(this.content$adm,FUN=function(x){return(x[2])})),region2=as.character(sapply(this.content$adm,FUN=function(x){return(x[3])})), date=as.Date(as.POSIXct(this.content$date, origin="1970-01-01")), dead=as.numeric(this.content$dead),infected=as.numeric(this.content$infected),recovered=as.numeric(this.content$recovered), tested=as.numeric(this.content$tested), source=this.content$source)


#Measures:
url  <- "http://bene.gridpiloten.de:4711"
path <- "/api/measures"
raw.result <- GET(url = url, path = path)
raw.result2 <- rawToChar(raw.result$content)
this.content <- fromJSON(raw.result2)

colnames(this.content)

measures.df <- data.frame(country=as.character(sapply(this.content$adm,FUN=function(x){return(x[1])})), region1=as.character(sapply(this.content$adm,FUN=function(x){return(x[2])})),region2=as.character(sapply(this.content$adm,FUN=function(x){return(x[3])})), schools_closed=as.logical(this.content$schools_closed), traveller_quarantine=as.logical(this.content$traveller_quarantine), border_control=as.logical(this.content$border_control),closure_leisureandbars=as.logical(this.content$closure_leisureandbars),lockdown=as.logical(this.content$lockdown),home_office=as.logical(this.content$home_office),primary_residence=as.logical(this.content$primary_residence),test_limitations=as.logical(this.content$test_limitations), date=as.Date(as.POSIXct(this.content$date, origin="1970-01-01")))

measures.df <- measures.df %>% replace(is.na(.), FALSE)

###
# Temporary Filter on Countrys to get calculate measures
###

cases.df <- cases.df %>%
  filter(is.na(region1)|region1=="nan"|region1=="") %>%
  filter(source=="JHU"|source=="RKI") %>%
  select(-region1,-region2)

measures.df <- measures.df %>%
  filter(is.na(region1)|region1=="nan"|region1=="") %>%
  select(-region1,-region2)

measures.df$country <- as.character(measures.df$country)
cases.df$country <- as.character(cases.df$country)

####
#   earliest.measures <- my.measures %>%
####

measures_long <- measures.df %>%
  gather("measure","event", 2:9)

earliest.measures <- measures_long %>%
  filter(event) %>%
  group_by(country, measure) %>%
  summarize(earliest=min(date)) %>%
  filter(country!="")

####
# Interpolate data
####

data_list <- list()
countries <- unique(cases.df$country)

for(i in 1:length(countries)){
  my.country <- countries[i]
  
  my.country.data <- cases.df %>%
    filter(country==my.country) %>%
    arrange(date) %>%
    group_by(country,date) %>%
    filter(row_number()==n()) %>%
    ungroup() 
  
  #  mutate(next_dead=lead(dead,1), next_infected=lead(infected,1), next_recovered=lead(recovered,1), next_tested=lead(tested,1),duration=as.vector(lead(date,1)-date))
  
  first_day <- min(my.country.data$date)
  last_day <- max(my.country.data$date)
  if(first_day==last_day) next
  
  days <- data.frame(date=as.Date(first_day:last_day,origin="1970-01-01"))
  my.country.data.full <- left_join(days,my.country.data)
  my.country.data.full$infected <- approxfun(1:nrow(my.country.data.full), my.country.data.full$infected)(1:nrow(my.country.data.full))
  my.country.data.full$dead <- approxfun(1:nrow(my.country.data.full), my.country.data.full$dead)(1:nrow(my.country.data.full))
  my.country.data.full$recovered <- approxfun(1:nrow(my.country.data.full), my.country.data.full$recovered)(1:nrow(my.country.data.full))
  my.country.data.full$tested <- approxfun(1:nrow(my.country.data.full), my.country.data.full$tested)(1:nrow(my.country.data.full))
  my.country.data.full$country <- my.country.data.full$country[1]
  my.country.data.full$source <- my.country.data.full$source[1]
  data_list[[i]] <- my.country.data.full
}

cases.df <- do.call(rbind,data_list)

####
# Without measures -> not of interes
####

cases.df <- cases.df %>%
  filter(country %in% earliest.measures$country)

####
# date until measure
####

earliest.measures_wide <- spread(earliest.measures,key="measure",value="earliest")

cases.df.measures <- left_join(cases.df,earliest.measures_wide)

cases.df <- cases.df.measures %>%
  mutate(days_since_school_closing = as.numeric(schools_closed-date)) %>%
  mutate(days_since_border_control = as.numeric(border_control-date)) %>%
  mutate(days_since_closure_leisureandbars = as.numeric(closure_leisureandbars-date)) %>%
  mutate(days_since_home_office = as.numeric(home_office-date)) %>%
  mutate(days_since_lockdown = as.numeric(lockdown-date)) %>%
  mutate(days_since_primary_residence = as.numeric(primary_residence-date)) %>%
  mutate(days_since_test_limitations = as.numeric(test_limitations-date)) %>%
  mutate(days_since_traveller_quarantine = as.numeric(traveller_quarantine-date)) %>%
  select(-border_control,-closure_leisureandbars,-home_office,-lockdown,-primary_residence,-schools_closed,-test_limitations,-traveller_quarantine)

####
# R0 formula
####

Min_filter <- 25

cases_work <- cases.df %>%
  arrange(country, date) %>%
  group_by(country) %>%
  mutate(date_no=as.numeric(date-as.Date("2020-01-01"))) %>%
  mutate(infected_min=lag(infected,1), infected_max=lead(infected,1), time_frame_lag=as.numeric(lead(date_no,1)-lag(date_no,1))) %>% 
  mutate(R0=((infected_min+(infected_max-infected_min)/time_frame_lag*10)/((infected_max+infected_min)/2))) %>%
  filter(!is.na(R0)) %>%
  filter(infected_min>Min_filter) %>%  
  ungroup() %>%
  mutate(R0=pmax(R0,0))

ggplot(cases_work %>% filter(R0<quantile(cases_work$R0,0.95)),aes(R0)) +
  geom_density(kernel="gaussian")

median(cases_work$R0)
mean(cases_work$R0)

#Plot vs number of cases
ggplot(cases_work, aes(x=infected,y=R0)) +
  geom_point() +
  geom_smooth(method=lm)

###
# Graphical Analysis
###

ggplot(cases_work,aes(x=days_since_school_closing,y=R0)) +
  geom_point() +
  geom_smooth()

ggplot(cases_work,aes(x=days_since_lockdown,y=R0)) +
  geom_point() +
  geom_smooth()

ggplot(cases_work,aes(x=days_since_border_control,y=R0)) +
  geom_point() +
  geom_smooth()
