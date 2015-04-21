# bike-predict
Lightweight forecasting tool for city bikes availability. 

# Design 
The forecasting method used is a simple composite Holt-Winters forecasting
method (exp. smoothing), based on a limited number of recent bike/station spaces measurements.
This is to faciliate a sharded architecture, and reduce the overhead making
multiple predictions in parallel. 

The lookahead for the forecasting period is quite limited, as there is no 
account for typical/daily/weekly/seasonal trends in the bike data. 
