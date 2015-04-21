# bike-predict
Lightweight forecasting tool for city bikes availability. 

# Design 
The forecasting method used is a simple composite Holt-Winters forecasting
method (exp. smoothing), based on a limited number of recent bike/station spaces measurements.
This is to faciliate a sharded architecture, and reduce the overhead making
multiple predictions in parallel. 

The lookahead for the forecasting period is quite limited, as there is no 
account for typical/daily/weekly/seasonal trends in the bike data. 

The goal of the project was to have a set forecast window, typically 15 minutes to 1 hour
before a bike or a bike-space was required at a provided station. The notifications list maintained 
who (email-address) would like to be notified of what station/bike. This allows the master user list to 
be partitioned across nodes if required.

Similarly the data polling from the CitiBikes URL (hidden to prevent spamming here), has a variable 
frequency depending on busy periods, to prevent the data source getting flooded with requests. This in 
turn allows decoupling been the notifications list, the data repository (i.e., a database, DHT, Redis or Memcache) 
and the forecasting components. 
