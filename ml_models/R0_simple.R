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
  filter(source=="JHU"|source=="RKI")

measures.df <- measures.df %>%
  filter(is.na(region1)|region1=="nan"|region1=="")

measures.df$country <- as.character(measures.df$country)
cases.df$country <- as.character(cases.df$country)

####
#   earliest.measures <- my.measures %>%
####

measures_long <- measures.df %>%
  select(-region1, -region2) %>%
  gather("measure","event", 2:9)

earliest.measures <- measures_long %>%
  filter(event) %>%
  group_by(country, measure) %>%
  summarize(earliest=min(date)) %>%
  filter(country!="")




####
# Join tables
####

#manual join due to dates

schools <- earliest.measures %>%
  filter(measure=="schools_closed") %>%
  select(-measure)

lockdown <- earliest.measures %>%
  filter(measure=="lockdown") %>%
  select(-measure)

cases.df.schools <- left_join(cases.df,schools)
cases.df.schools <- cases.df.schools %>%
  rename(earliest_school=earliest)

cases.df.schools <- cases.df.schools %>%
  mutate(is_school_closed=(date>=earliest_school))

cases.df.lockdown <- left_join(cases.df,lockdown)
cases.df.lockdown <- cases.df.lockdown %>%
  rename(earliest_lockdown=earliest)

cases.df.lockdown <- cases.df.lockdown %>%
  mutate(is_lockdown=(date>=earliest_lockdown))

cases.df.schools %>%
  filter(country=="DE") %>%
  arrange(date)
cases.df.lockdown %>%
  filter(country=="DE") %>%
  arrange(date)

cases.df <- cases.df.schools
cases.df$is_lockdown <- cases.df.lockdown$is_lockdown
cases.df$earliest_lockdown <- cases.df.lockdown$earliest_lockdown

####
# R0 formula
####

Min_filter <- 10

cases_work <- cases.df %>%
  arrange(country, region1, region2, date) %>%
  group_by(country, region1, region2, date) %>%
  distinct() %>%
  filter(row_number()==n()) %>% #RKI has interday data, we only take the End-Of-Day entry
  ungroup() %>%
  arrange(country, region1, region2, date) %>%
  group_by(country, region1, region2) %>%
  mutate(date_no=as.numeric(date-as.Date("2020-01-01"))) %>%
  mutate(infected_min=lag(infected,1), infected_max=lead(infected,1), time_frame_lag=as.numeric(lead(date_no,1)-lag(date_no,1))) %>% 
  mutate(R0=((infected_min+(infected_max-infected_min)/time_frame_lag*10)/((infected_max+infected_min)/2))) %>%
  filter(!is.na(R0)) %>%
  filter(infected_min>Min_filter) %>%  
  ungroup() %>%
  mutate(R0=pmax(R0,0))

##Kill known problems
cases_work <- cases_work %>%
  filter(region1!="Bavaria")

ggplot(cases_work %>% filter(R0<quantile(cases_work$R0,0.95)),aes(R0)) +
  geom_density(kernel="gaussian")

median(cases_work$R0)
mean(cases_work$R0)

#Now we have R0 for each day. Lets Lag it by 6 days and compute difference. If no value available take next one
#not very high performing
testday_shift <- 6

cases_work <- cases_work %>%
  group_by(country, region1, region2) %>%
  mutate(coun_string=paste0(country,";",region1,";",region2)) %>%
  mutate(R0_shift=NA)

unique(cases_work$coun_string)
cases_work$R0_shift_lockdown <- NA

for(i in 1:nrow(cases_work)){
  my_date <- cases_work$date[i]
  wan_date <-cases_work$date[i] + testday_shift
  my_coun <- cases_work$coun_string[i]
  
  j <- i+1
  while(TRUE){
    if(j>nrow(cases_work)){
      break
    }
    if(my_coun!=cases_work$coun_string[j]){
      break
    }
    if(wan_date<=cases_work$date[j]){
      cases_work$R0_shift[i] <- cases_work$R0[j]
      cases_work$date_R0_shift[i] <- as.Date(as.POSIXct(cases_work$date[j], origin="1970-01-01"))
      if(!is.na(cases_work$date_R0_shift[i]) && !is.na(cases_work$earliest_school[i])){
        if(cases_work$is_school_closed[i] && cases_work$date_R0_shift[i]<=cases_work$earliest_school[i]+8){
          cases_work$R0_shift_school_change[i] <- TRUE
        } else {
          cases_work$R0_shift_school_change[i] <- FALSE
        }
      }
      if(!is.na(cases_work$date_R0_shift[i]) && !is.na(cases_work$earliest_lockdown[i])){
        if(cases_work$is_lockdown[i] && cases_work$date_R0_shift[i]<=cases_work$earliest_lockdown[i]+8){
          cases_work$R0_shift_lockdown[i] <- TRUE
        } else {
          cases_work$R0_shift_lockdown[i] <- FALSE
        }
      }
      break
    }
    j <- j+1
  }
}

View(cases_work %>%
  filter(country=="DE") %>%
  arrange(date))


cases_work <- cases_work %>%
  mutate(R0_diff=R0_shift-R0)

ggplot(cases_work,aes(R0_diff)) +
  geom_density()

finite_R0 <- cases_work %>%
  filter(!is.na(R0_diff)) %>%
  filter(!is.na(R0_shift_school_change))

finite_R0_lock <- cases_work %>%
  filter(!is.na(R0_diff)) %>%
  filter(!is.na(R0_shift_lockdown))

finite_R0$R0_shift_school_change
finite_R0_lock$R0_shift_lockdown

mean(finite_R0$R0_diff[!finite_R0$R0_shift_school_change])
mean(finite_R0$R0_diff[finite_R0$R0_shift_school_change])

summary(lm(R0_shift~R0+dead+infected+recovered+R0_shift_lockdown+R0_shift_school_change+is_school_closed+is_lockdown,data=finite_R0))
summary(lm(R0_shift~R0+dead+infected+recovered+is_school_closed+is_lockdown,data=finite_R0))
summary(lm(R0_diff~R0+infected+is_school_closed+is_lockdown,data=finite_R0))
summary(lm(R0_diff~infected+is_school_closed+is_lockdown,data=finite_R0))
summary(lm(R0_diff~infected+R0_shift_lockdown+R0_shift_school_change,data=finite_R0))
stargazer(lm(R0_diff~infected+R0_shift_lockdown+R0_shift_school_change,data=finite_R0), type="text")
stargazer(lm(R0_diff~R0*(is_lockdown+is_school_closed),data=finite_R0), type="text")



plot(finite_R0$infected,finite_R0$tested)

sd(finite_R0$R0_diff[!finite_R0$R0_shift_school_change])
sd(finite_R0$R0_diff[finite_R0$R0_shift_school_change])

school_effect <- mean(finite_R0$R0_diff[finite_R0$R0_shift_school_change])-mean(finite_R0$R0_diff[!finite_R0$R0_shift_school_change])
lockdown_effect <- mean(finite_R0_lock$R0_diff[finite_R0_lock$R0_shift_lockdown])-mean(finite_R0_lock$R0_diff[!finite_R0_lock$R0_shift_lockdown])

data.frame(school_effect,lockdown_effect)
