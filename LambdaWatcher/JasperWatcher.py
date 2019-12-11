import requests
import json 
import os 
import boto3
import time 
from botocore.exceptions import ClientError
from base64 import b64decode
'''
Pseudo code: 

Login to Jasper Wireless 

For every id in our searchlist:
    Get a JSON of matching unit data
    For each matching unit: 
        Get sim id 
        Get device id
        If the unit is in session:
            Get ip for the unit 
    
If there was any units in session:
    If email notification is on: 
        Email the device id, ip and iccid of units in session 
    If SMS notification is on: 
        SNS the device id, ip and iccid of units in session
'''

'''
Available notification types:
SNS - Simple Notification Service (SMS)
SES - Simple Email Service (Email) 
'''

SNS_NOTIFICATION = False
# Change to your number (Currently Isas number)
number = ""

SES_NOTIFICATION = True

fileHandler = open ("ICCIDs.txt", "r")
# Get list of all iccids in the file
listOfLines = fileHandler.readlines()
searchunits = [x.replace('\n', '') for x in listOfLines]

baseurl='https://tele2.jasperwireless.com/provision'

epochnow = int(time.time())

requestSession = requests.session()
encrypted_password = os.environ['password']
decrypted_password = boto3.client('kms').decrypt(CiphertextBlob=b64decode(encrypted_password))['Plaintext']

def login():
    
    data = {
      'j_username': os.environ['user'],
      'j_password': decrypted_password
    }
    
    response = requestSession.post(baseurl + '/j_acegi_security_check', data=data)
    return response

def get_unit_data(unit): 
    headers = {
        'Sec-Fetch-Mode': 'cors',
        'Referer': baseurl + '/ui/terminals/sims/sims.html',
    }
    
    params = (
        ('_dc', epochnow),
        ('page', '1'),
        ('limit', '50'),
        ('sort', 'deviceId'),
        ('dir', 'ASC'),
        ('search', '[{"property":"oneBox","type":"CONTAINS","value":"*' + unit + '*","id":"oneBox"}]'),
    )
    
    response = requests.get(baseurl + '/api/v1/sims', headers=headers, params=params, cookies=requestSession.cookies)
    return response_content_to_json(response)

def in_session(unitData): 
    return unitData['data'][0]['inSession']
    
def get_ip(unit, simId): 
    params = (
        ('_dc', epochnow),
        ('page', '1'),
        ('limit', '50'),
        ('search', '[{"property":"simId","type":"LONG_EQUALS","value":"' + str(simId) + '","id":"' + str(simId) + '"}]'),
    )
    
    response = requests.get(baseurl + '/api/v1/sims/searchDetails', params=params, cookies=requestSession.cookies)
    json_resp = response_content_to_json(response)
    return json_resp['data'][0]['currentSessionInfo']['deviceIpAddress']
    
    
def response_content_to_json(response): 
    return json.loads(response.content)
    
def send_SNS_notification(units): 
    session = boto3.Session(
        region_name="us-east-1"
    )
    
    unitsInSession = ""
    for k,v in units.items(): 
        unitsInSession += k + " : " + v + "\n" 
    
    sns_client = session.client('sns')
    try: 
        response = sns_client.publish(
            PhoneNumber=number,
            Message='A unit you are watching is in session!\n' + unitsInSession,
            MessageAttributes={
                'AWS.SNS.SMS.SenderID': {
                    'DataType': 'String',
                    'StringValue': 'DMS'
                },
                'AWS.SNS.SMS.SMSType': {
                    'DataType': 'String',
                    'StringValue': 'Promotional'
                }
            }
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("SMS sent!")

def send_SES_notification(units): 
    SENDER = "DMS JasperWatcher <dms@tritech.se>"
    RECIPIENT = "urban.rossang@tritech.se"
    AWS_REGION = "eu-west-1"
    SUBJECT = "A unit you are watching is in session!"    
    
    body = "" 
    for k,v in units.items(): 
        body += k + " : " + v + "\n"
        
    BODY_TEXT = (body)
    CHARSET = "UTF-8"

    client = boto3.client('ses',region_name=AWS_REGION)
    
    try:
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
    
    
def lambda_handler(event, context):

    login()
    unitsInSession = {}
    
    for unit in searchunits: 
        unitData = get_unit_data(unit)
        for i in range (0, len(unitData['data'])): 
            simId = unitData['data'][i]['simId']
            deviceId = unitData['data'][i]['deviceId']
            iccid = unitData['data'][i]['iccid']
            ip = get_ip(unit, simId)
            if ip != None:
                unitsInSession[deviceId] = get_ip(unit, simId) + ', ' + iccid

    if len(unitsInSession) > 0: 
        if SNS_NOTIFICATION: 
            send_SNS_notification(unitsInSession)
        if SES_NOTIFICATION: 
            send_SES_notification(unitsInSession)

    return {
        'statusCode': 200,
        'body': json.dumps("Jasperwatcher is ok")
    }
