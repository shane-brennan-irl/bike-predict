import datetime
import hashlib
import json
import math
import random
import requests
import smtplib
import sys
import time
import traceback
from engine.AlertEmailer import AlertEmailer
from scipy import stats
from numpy import arange, array, ones

# The URL providing the JSON for the city bikes data
API_URL = "http://blahblahblah.blah"

# Now for some forecasting/scheduling parameters
alpha = 0.5
beta = 0.5
maxListSize = 30
sigma = 1.0
forecastHorizon = 15
splitVariance = True
LOG_VERBOSE = True

class BikePredictEngine:

	def __init__(self):
		self.bikesHash = {}
		self.emailAlert = AlertEmailer()

	def start(self):
		""" The main function of the Bike Predict Engine. Gets the current/predicted time
		    and then gets the forecast. 
		"""
		previousTime = 0
		delayCounter = 1
		noneCounter = 0
		stationData = None

		while True:
			# Get the time as an int of the form HHMM
			currentDate = datetime.datetime.now()
			currentTime = (int(currentDate.hour) * 100) + int(currentDate.minute)

			# Get the day of week, 0-4 for Mon-Fri
			currentDay = currentDate.weekday()

			# Get the sample rate in minutes
			sampleRate = self.getSampleRate(currentTime)

			# Check every 20 seconds or so that it's a new minute
			if (currentTime != previousTime):
				
				# If the sample rate is 1 on a weekday, refresh the JSON each minute
				if sampleRate == 1 and currentDay < 5:
					stationData = self.getBikeData()
				# Otherwise use the same sample until refreshed
				else:
					if (stationData is None) or (delayCounter >= sampleRate):
						stationData = self.getBikeData()
						delayCounter = 1
					else:
						delayCounter += 1

				# If the CitiBikes API Breaks, don't send anything
				if stationData is not None:	
					# Update the data for each station
					self.updateBikeData(currentTime, stationData)

					# Iterate through the updated data and generate alerts
					alertList, alertMessage = self.getBikeForecast(currentDate)

					# Email if the alert matches
					self.emailAlert.checkNotifications(alertList, alertMessage)		

					# Reset the flag for a broke CitiBikes API
					noneCounter = 0
				else:
					noneCounter += 1
					if noneCounter > 100:
						print "Exiting - connection to CitiBikes API broken at",currentTime
						exit(1)

				previousTime = currentTime
			else:	
				sleepTime = random.randint(1, 20)	
				time.sleep(sleepTime)

        def getBikeData(self):
		""" Returns the raw City Bike data.
		"""
                try:
                        decoder = json.JSONDecoder()
                        station_json = requests.get(API_URL, proxies='')
                        station_data = decoder.decode(station_json.content)
                except:
			print traceback.format_exc()
			print "Sorry - couldn't retrieve Bike Data"
                        return None

                for ii in range(0, len(station_data)):
                        del station_data[ii]['lat']
                        del station_data[ii]['lng']
                return station_data

        def updateBikeData(self, currentTime, data):
		""" Gets the data from the raw JSON, parses this and adds 
		    it to a hashtable.
		"""
                for row in data:
			idx = int(row['idx'])
                        name = str(row['name'])
                        bikes = int(row['bikes'])
                        free = int(row['free'])

			keyString = '%s-%s'%(idx,name)
			key = hashlib.md5(keyString).hexdigest()

			try:
				# Get the existing data for this station
				bikesData = self.bikesHash[key]
				self.updateJSON(key, bikesData, currentTime, idx, name, bikes, free)
			except KeyError, err:
				self.createJSON(key, currentTime, idx, name, bikes, free)
	
	def updateJSON(self, key, bikesData, currentTime, idx, name, bikes, free):
		""" Update the bike data according to the provided key (idx + name), 
		    this assumes that the JSON exists. 
		"""
		timesList = bikesData['times']
		bikesList = bikesData['bikes']			
		freeList = bikesData['free']

		# Update the list of free/bike values
		timesList.append(currentTime)
		bikesList.append(bikes)
		freeList.append(free)

		# Limit the number of bikes/free to maxlen
		if len(bikesList) > maxListSize:
			timesList = timesList[-maxListSize:]
			bikesList = bikesList[-maxListSize:]
			freeList = freeList[-maxListSize:]

		# Add the station data to the hash
		bikesData['times'] = timesList
		bikesData['bikes'] = bikesList
		bikesData['free'] = freeList
		bikesData['idx'] = idx
		bikesData['name'] = name
				
		self.bikesHash[key] = bikesData


	def createJSON(self, key, currentTime, idx, name, bikes, free):
		""" Create the JSON document structure (lists/items) assuming that 
		    the key has not been created earlier. 
		"""
		bikesData = {}
		timesList = []
		bikesList = []
		freeList = []

		timesList.append(currentTime)
		bikesList.append(bikes)
		freeList.append(free)

		bikesData['times'] = timesList
		bikesData['bikes'] = bikesList
		bikesData['free'] = freeList
		bikesData['idx'] = idx
		bikesData['name'] = name

		self.bikesHash[key] = bikesData				

	
	def getBikeForecast(self, currentDate):
		""" This function gets the prediction based on the forecast horizon (e.g., 15 
		    minutes hence) for each bike station. 
		"""
		alertList = []
		messageList = []

		forecastDate = datetime.datetime.now() + datetime.timedelta(minutes=forecastHorizon)
                forecastTime = (int(forecastDate.hour) * 100) + int(forecastDate.minute)
                currentTime = (int(currentDate.hour) * 100) + int(currentDate.minute)

		for key in self.bikesHash.keys():
			bikesData = self.bikesHash[key]
			name = bikesData['name']
			idx = bikesData['idx']
			timesList = bikesData['times']
			bikesList = bikesData['bikes']			
			freeList = bikesData['free']

			bPoint, bTrend = self.getExpSmthForecast(bikesList)
			bForecast = bPoint + (float(forecastHorizon)*bTrend)
			if bForecast <= 1.0:
				key = self.getHashKey(idx, forecastTime, 'bikes')
				alertList.append(key)
				message1 = "Bike Availability Alert\n"
				message2 = "Predicting {0} ({1}) will have limited bikes at {2}, ".format(name, idx, forecastDate.strftime('%H:%M %d-%m-%Y'))
				message3 = "Currently {0} bikes are available.".format(bikesList[-1])
				message = message1+message2+message3
				messageList.append(message)
				
			fPoint, fTrend = self.getExpSmthForecast(freeList)
			fForecast = fPoint + (float(forecastHorizon)*fTrend)
			if fForecast <= 1.0:
				key = self.getHashKey(idx, forecastTime, 'free')
				alertList.append(key)
				message1 = "Bike Spaces Availability Alert\n"
				message2 = "Predicting {0} ({1}) will have limited free spaces at {2}, ".format(name, idx, forecastDate.strftime("%H:%M %d-%m-%Y"))
				message3 = "Currently {0} free spaces are available.".format(freeList[-1])
				message = message1+message2+message3
				messageList.append(message)

		return alertList, messageList

	def getHashKey(self, idx, timeInt, type):
		keyString = '{0}-{1}-{2}'.format(idx, timeInt, type)
		key = hashlib.md5(keyString).hexdigest()
		return key
	
	def getExpSmthForecast(self, dataList):
		""" A Holt-Winters Exponential Smoothing Model with a 
		    trend component. Returns the point forecast and trend as 
		    the output of the function. The forecast itself is the 
		    point forecast + (iterations x trend). 
		"""
		# Needs a list of at least two components.
		if len(dataList) < 1:
			return None, None
		elif len(dataList) < 2:
			return dataList[-1], 0.0
		# Performs the exp. smoothing list. 
		else:
			st1 = dataList[1]
			bt1 = dataList[1]-dataList[0]

			index = 2
			while index < len(dataList):
				xt = dataList[index]
				st2 = st1
				bt2 = bt1
				st1 = (alpha*xt) + ((1-alpha)*(st2+bt1))
				bt1 = (beta*(st1-st2)) + ((1-beta)*bt2)
				index += 1

			return st1, bt1
	
	def getSampleRate(self, currentTime):
		result = 5
		if currentTime > 700 and currentTime < 930:
			result = 1
		elif currentTime > 1630 and currentTime < 1759:
			result = 1
		return result
