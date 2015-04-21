import datetime
import hashlib
import smtplib
import sys
import time
import traceback
import os.path
LOG_VERBOSE = True

class AlertEmailer:

	def __init__(self):
		self.alertHash = {}
		if os.path.exists('notifications.txt'):
			# Load the notifications list
			self.addAlerts('notifications.txt')
		else :
			print "Can't find notifications.txt file, exiting..."
			exit(1)

	def addAlerts(self, filename):
		file = open(filename, "r")
		for line in file:
			tokens = line.rstrip().split(",")
			key = self.getHashKey(tokens[0], tokens[1], tokens[2])
			email = tokens[3]
			self.addEmail(key, email)
		file.close()

	def addEmail(self, key, email):
		try:
			emailList = self.alertHash[key]
			emailList.append(email)
			self.alertHash[key] = emailList
		except KeyError, err:
			emailList = []
			emailList.append(email)
			self.alertHash[key] = emailList

	def getHashKey(self, idx, timeInt, type):
		keyString = '{0}-{1}-{2}'.format(idx, timeInt, type)
		key = hashlib.md5(keyString).hexdigest()
		return key

	def checkNotifications(self, alertList, messageList):
		counter = 0
		for index, key in enumerate(alertList):
			try:
				emailList = self.alertHash[key]
				message = messageList[index]
				for email in emailList:
					self.sendEmail(email, message)
			except KeyError, err:
				counter += 1	

	def sendEmail(self, email, message):
            gmail_user = "youremailname@youremailprovider.com"
            gmail_pwd = "yourpassword"
            FROM = 'me@youremailprovider.com'
            TO = [email]
            SUBJECT = "BikePredict Alert"
            TEXT = message

            # Prepare actual message
            message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
            """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
            try:
                #server = smtplib.SMTP(SERVER) 
                server = smtplib.SMTP("smtp.gmail.com", 587) #or port 465 doesn't seem to work!
                server.ehlo()
                server.starttls()
                server.login(gmail_user, gmail_pwd)
                server.sendmail(FROM, TO, message)
                #server.quit()
                server.close()
            except:
                print "Failed to send email"
