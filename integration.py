##!/usr/bin/env python
import http.client
import json
from hashlib import sha1
import hmac
import binascii
import requests 
import imp
#import the private information such as webhookUrl, dev id and key
integrationId = imp.load_compiled("integrationId", "./integrationId.cpython-34.pyc")
from integrationId import integrationId


########################
####   FUNCTIONS   #####
########################

#function to obtain the id associated to the route
def getRouteId(routeName):
    requestStr ='/v3/routes?route_name=' + routeName
    requestStr = requestStr + ('&' if ('?' in requestStr) else '?')
    requestStr = requestStr + 'devid={0}'.format(devId)
    key_bytes  = bytes(key , 'latin-1')
    requestStr_bytes = bytes(requestStr, 'latin-1')
    hashed     = hmac.new(key_bytes, requestStr_bytes, sha1)
    
    signature = hashed.hexdigest()
    connection.request('GET',requestStr + '&signature={1}'.format(devId, signature))
    response  = connection.getresponse()
    routeInfo = json.loads(response.read().decode('utf-8'))
    routeId   = routeInfo['routes'][0]['route_id']
    return routeId

#Function to check if there is any disruption associated to the route.
#It extracts information about route disruptions from the Public Transport Victoria API. 
def get_disruptions(route_id):
    requestStr ='/v3/disruptions/route/'+str(route_id)
    requestStr = requestStr + ('&' if ('?' in requestStr) else '?')
    requestStr = requestStr + 'devid={0}'.format(devId)
    keyBytes   = bytes(key , 'latin-1')
    requestStrBytes = bytes(requestStr, 'latin-1')
    hashed     = hmac.new(keyBytes, requestStrBytes, sha1)
    
    signature = hashed.hexdigest()
    connection.request('GET',requestStr + '&signature={1}'.format(devId, signature))
   
    response     = connection.getresponse()
    responseJson = json.loads(response.read().decode('utf-8'))
    statusStr    = responseJson['disruptions']['metro_train'][0]['disruption_status']
    titleStr     = responseJson['disruptions']['metro_train'][0]['title']
    
    return [statusStr,titleStr]

#Send a message in Slack to public transport users when their train line have disrupted services.
def sendMessageInSlack(text,channel):
	payload={'username': 'disruption', 'text':text, 'channel': '@' + channel}

	try:
		res = requests.post(integrationId.webhookUrl, data = json.dumps(payload))
	except Exception as e:
		sys.stderr.write('An error occurred when trying to deliver the message:\n  {0}'.format(e.message))
		return 2

	if not res.ok:
		sys.stderr.write('Could not deliver the message. Slack says:\n  {0}'.format(res.text))
	return 0

def main():
    #Collect the routes for which information is required
    route = []
    for i in range(0,len(customerRoute)):
        if customerRoute[i][1] not in route:
           route.append(customerRoute[i][1])
         
    #Alert customers
    for i in route:
        routeId = getRouteId(i)
        res = get_disruptions(routeId)
        for j in range(0,len(customerRoute)):
             if(res[0] == 'Current') and (customerRoute[j][1] == i): sendMessageInSlack(res[1],customerRoute[j][0])
    


    return 0

###################################
####   API integration project ####
###################################

#Connection to the Public Transport Victoria API
connection = http.client.HTTPConnection("timetableapi.ptv.vic.gov.au", timeout=2)

#Import the devID and key 
devId = integrationId.devId
key   = integrationId.key

#customerRoute=[('Barry','Belgrave'),('Harry','Hurstbridge'),('Wally','Werribee'),('Freddy','Frankston')]

#My examples with existing slack accounts 
customerRoute=[('jules','Pakenham'),('anna','Pakenham')]

main()
connection.close()
      