"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function
import datetime
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

userID = ""
eventList = {}
dbQueried = False
possibleEvents = {}
currentlyCheckingEvent = ""
currentlyCheckingDate = ""
yesNoActivity = ""

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Event Countdown Welcome"
    speech_output = "Welcome to Event Countdown. " \
                    "You can add an event with a name and date, list all events, " \
                    "or countdown to an event"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please say add an event, list events, or " \
                    "ask how long until a specific event."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Goodbye from Event Countdown"
    speech_output = "Thank you for trying Event Countdown by Adventures with Anthony. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def create_event_attributes(event, date):
    try:
        global userID
        global eventList
        global dbQueried
        if dbQueried:
            eventList[event.lower()] = date
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('EventCountdown')
        response = table.put_item(
            Item={
                'UserID': userID,
                'EventName': event.lower(),
                'StartDate': date
            }
        )
    except ClientError as e:
        print(e.response)
        return e.response['Error']['Code']
    
    return {"eventName": event, "startDate": date}


def set_event_in_session(intent, session):
    """ Sets the event name and date in the session and prepares the speech to reply to the
    user.
    """

    card_title = "Adding a New Event"
    session_attributes = {}
    should_end_session = False

    if 'event' in intent['slots'] and 'date' in intent['slots']:
        if 'value' in intent['slots']['event']:
            event_name = intent['slots']['event']['value']
            if 'value' in intent['slots']['date']:
                start_date = intent['slots']['date']['value']
                session_attributes = create_event_attributes(event_name, start_date)
                speech_output = "I now know your event on " + start_date + "is named " + \
                            event_name + \
                            ". You can ask me how long to this event by saying, " \
                            "how long until " + event_name + "?"
                reprompt_text = "You can ask me how long to this event by saying, " \
                            "how long until " + event_name + "?"
            else:
                event_name = intent['slots']['event']['value']
                session_attributes = create_event_attributes(event_name, "")
                speech_output = "I now know your event is named " + \
                            event_name + \
                            ". You can tell me when this is event by saying, " + \
                            event_name + " is on May Third, Twenty Nineteen."
                reprompt_text = "You can tell me when this is event by saying, " + \
                            event_name + " is on May Third, Twenty Nineteen."
        else:
            speech_output = "I'm sorry, I did not understand that event name. Please try again."
            reprompt_text = "You can create an event by saying add event Caribbean Cruise on June Fifth"
    elif 'event' in intent['slots']:
        if 'value' in intent['slots']['event']:
            event_name = intent['slots']['event']['value']
            session_attributes = create_event_attributes(event_name, "")
            speech_output = "I now know your event is named " + \
                            event_name + \
                            ". You can tell me when this is event by saying, " + \
                            event_name + " is on May Third, Twenty Nineteen."
            reprompt_text = "You can tell me when this is event by saying, " + \
                            event_name + " is on May Third, Twenty Nineteen."
        else:
            speech_output = "I'm sorry, I did not understand that event name. Please try again."
            reprompt_text = "You can create an event by saying add event Caribbean Cruise on June Fifth"                   
    else:
        speech_output = "I'm not sure what your event name is. " \
                        "Please try again."
        reprompt_text = "I'm not sure what your event name is. " \
                        "Please try again."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_events_from_session(intent, session):
    session_attributes = {}
    reprompt_text = None
    title = "Event List"
    
    try:
        events = ""
        global eventList
        global dbQueried
        if dbQueried:
            eventCount = len(eventList)
            if eventCount == 0:
                events = "You do not have any saved events. You can add a new event " + \
                "by saying Add Event Vacation on June 5th"
            else:
                i = 0
                for key, item in eventList.iteritems():
                    events += key + " on " + str(item)
                    if i == eventCount - 2:
                        events += " and "
                    else:
                        events += ", "
                    i = i + 1
        else:
            global userID
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.Table('EventCountdown')
            response = table.query(
                KeyConditionExpression=Key('UserID').eq(userID)
            )
            eventCount = len(response['Items'])
            dbQueried = True
            if eventCount == 0:
                events = "You do not have any saved events. You can add a new event " + \
                "by saying Add Event Vacation on June 5th"
            else:
                for idx, item in enumerate(response['Items']):
                    eventList[item['EventName']] = item['StartDate']
                    events += item['EventName'] + " on " + str(item['StartDate'])
                    if idx == eventCount - 2:
                        events += " and "
                    else:
                        events += ", "
        speech_output = "You have the following events: " + events + \
        "You can find out how many days to an event by asking how long until the event name"
        should_end_session = False
    except ClientError as e:
        print(e.response)
        if session.get('attributes', {}) and "eventName" in session.get('attributes', {}):
            eventName = session['attributes']['eventName']
            speech_output = "Your event name is " + eventName + \
                            ". Goodbye."
            should_end_session = True
        else:
            speech_output = "I'm not sure what your event name is. " \
                            "You can say, add event named Caribbean Cruise."
            should_end_session = False

    # Setting reprompt_text to None signifies that we do not want to reprompt
    # the user. If the user does not respond or says something that is not
    # understood, the session will end.
    return build_response(session_attributes, build_speechlet_response(
        title, speech_output, reprompt_text, should_end_session))
        
def set_date_in_session(intent, session):
    
    card_title = "Adding Date for Event"
    session_attributes = {}
    should_end_session = False

    if 'event' in intent['slots'] and 'date' in intent['slots']:
        event_name = intent['slots']['event']['value']
        card_title = "Adding Date for " + event_name
        start_date = intent['slots']['date']['value']
        session_attributes = create_event_attributes(event_name, start_date)
        speech_output = "I now know your event on " + start_date + "is named " + \
                        event_name + \
                        ". You can ask me how long to this event by saying, " \
                        "how long until " + event_name + "?"
        reprompt_text = "You can ask me how long to this event by saying, " \
                        "how long until " + event_name + "?"
    else:
        eventName = ""
        if session.get('attributes', {}) and "eventName" in session.get('attributes', {}):
            eventName = session['attributes']['eventName']
        speech_output = "I'm not sure when your " + eventName + " event is. " \
                        "Please try again."
        reprompt_text = "I'm not sure what your event is. " \
                        "Please try again."
                        
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        
def get_countdown_from_session(intent, session):
    
    card_title = "Countdown to Event"
    session_attributes = {}
    should_end_session = False
    
    curDate = datetime.datetime.now().date()
    eventName = ""
    startDate = ""
    if 'event' in intent['slots']:
        if 'value' in intent['slots']['event']:
            eventName = intent['slots']['event']['value']
            card_title = "Countdown to " + eventName
            try:
                global userID
                global eventList
                global dbQueried
                global possibleEvents
                global currentlyCheckingDate
                global currentlyCheckingEvent
                global yesNoActivity
                possibleEvents = {}
                posEvents = 0
                if dbQueried:
                    if eventName.lower() in eventList:
                        startDate = eventList[eventName.lower()]
                        posEvents = -1
                    else:
                        for key in eventList:
                            if eventName.lower() in key:
                                possibleEvents[key] = eventList[key]
                                posEvents = posEvents + 1
                                startDate = eventList[key]
                else:
                    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
                    table = dynamodb.Table('EventCountdown')
                    response = table.query(
                        KeyConditionExpression=Key('UserID').eq(userID)
                    )
                    dbQueried = True
                    print(eventName.lower())
                    eventCount = len(response['Items'])
                    for idx, item in enumerate(response['Items']):
                        if item['StartDate'] >= datetime.datetime.strftime(curDate, '%Y-%m-%d'):
                            eventList[item['EventName']] = item['StartDate']
                            if item['EventName'] == eventName.lower():
                                startDate = item['StartDate']
                                posEvents = -1
                            elif eventName in item['EventName']:
                                if posEvents >= 0:
                                    possibleEvents[item['EventName']] = item['StartDate']
                                    startDate = item['StartDate']
                                    posEvents = posEvents + 1
                if posEvents > 1:
                    yesNoActivity = "countdown"
                    currentlyCheckingEvent, currentlyCheckingDate = possibleEvents.popitem()
                    speech_output = "There are " + str(posEvents) + " possible events that match " + eventName + ". Did you mean " + currentlyCheckingEvent + "?"
                    reprompt_text = speech_output
                    return build_response(session_attributes, build_speechlet_response(
                        intent['name'], speech_output, reprompt_text, should_end_session))
            except ClientError as e:
                print(e.response)
    if startDate == "":
        if eventName == "":
            eventName = "Unknown Event Name"
        if session.get('attributes', {}) and "eventName" in session.get('attributes', {}):
            eventName = session['attributes']['eventName']
        if session.get('attributes', {}) and "startDate" in session.get('attributes', {}):
            startDate = session['attributes']['startDate']
        else:
            speech_output = "I don't know the date for your event. " \
                            "You can tell me the date by saying " + eventName + " is on May Fifth Twenty Eighteen"
            reprompt_text = "You can tell me the date by saying " + eventName + " is on May Fifth Twenty Eighteen"
            return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))
            
    startDate = datetime.datetime.strptime(startDate, '%Y-%m-%d').date()
    delta = startDate - curDate
    days = delta.days
    
    speech_output = "There are " + str(days) + " days until " + eventName
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, None, should_end_session))
        
def yes(intent, session):
    card_title = intent['name']
    session_attributes = {}
    should_end_session = False
    
    global currentlyCheckingEvent
    global currentlyCheckingDate
    global yesNoActivity
    global userID
    
    if currentlyCheckingEvent:
        if yesNoActivity == "countdown":
            curDate = datetime.datetime.now().date()
            
            startDate = datetime.datetime.strptime(currentlyCheckingDate, '%Y-%m-%d').date()
            delta = startDate - curDate
            days = delta.days
        
            speech_output = "There are " + str(days) + " days until " + currentlyCheckingEvent
            reprompt_text = None
            should_end_session = True
        elif yesNoActivity == "delete":
            try:
                dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
                table = dynamodb.Table('EventCountdown')
                response = table.delete_item(
                    Key={
                        'UserID': userID,
                        'EventName': currentlyCheckingEvent.lower()
                    }
                )
                if currentlyCheckingEvent.lower() in eventList:
                    eventList.pop(currentlyCheckingEvent.lower())
                speech_output = "The event " + currentlyCheckingEvent + " was successfully deleted."
                reprompt_text = None
                should_end_session = True
            except ClientError as e:
                print(e.response)
                speech_output = "There was a problem deleting " + eventName + ". Please try again."
                reprompt_text = speech_output
    else:
        speech_output = "I did not ask a yes or no question."
    return build_response(session_attributes, build_speechlet_response(
        "Answered Yes", speech_output, None, should_end_session))
    
def no(intent, session):
    card_title = intent['name']
    session_attributes = {}
    should_end_session = False
    
    global currentlyCheckingEvent
    global currentlyCheckingDate
    global possibleEvents
    
    if currentlyCheckingEvent:
        if possibleEvents:
            currentlyCheckingEvent, currentlyCheckingDate = possibleEvents.popitem()
            speech_output = "Ok. Did you mean " + currentlyCheckingEvent + "?"
            reprompt_text = "Did you mean " + currentlyCheckingEvent + "?"
        else:
            currentlyCheckingDate = ""
            currentlyCheckingEvent = ""
            speech_output = "That's all the matching events I found. Please try again."
            reprompt_text = "You can add an event, list all events, or countdown to a specific event"
    else:
        speech_output = "I did not ask a yes or no question."
        reprompt_text = "You can add an event, list all events, or countdown to a specific event"
    return build_response(session_attributes, build_speechlet_response(
        "Answered No", speech_output, None, should_end_session))   
        
def delete_event(intent, session):
    card_title = "Deleting Event"
    session_attributes = {}
    should_end_session = False
    
    global dbQueried
    global userID
    global eventList
    global possibleEvents
    global currentlyCheckingDate
    global currentlyCheckingEvent
    global yesNoActivity
    
    if 'event' in intent['slots'] and 'value' in intent['slots']['event']:
        eventName = intent['slots']['event']['value']
        card_title = "Deleting " + eventName
        if not dbQueried:
            populateEvents()
            
        posEvents = 0
        posEventName = ""
        if eventName.lower() not in eventList:
            for key, value in eventList.iteritems():
                if eventName.lower() in key:
                    posEvents = posEvents + 1
                    posEventName = key
                    possibleEvents[key] = eventList[key]
            if posEvents == 1:
                eventName = posEventName
            else:
                yesNoActivity = "delete"
                currentlyCheckingEvent, currentlyCheckingDate = possibleEvents.popitem()
                speech_output = "There are " + str(posEvents) + " possible events that match " + eventName + ". Did you mean " + currentlyCheckingEvent + "?"
                reprompt_text = speech_output
                return build_response(session_attributes, build_speechlet_response(
                    card_title, speech_output, reprompt_text, should_end_session))
        try:
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.Table('EventCountdown')
            response = table.delete_item(
                Key={
                    'UserID': userID,
                    'EventName': eventName.lower()
                }
            )
            if eventName.lower() in eventList:
                eventList.pop(eventName.lower())
            speech_output = "The event " + eventName + " was successfully deleted."
            reprompt_text = None
            should_end_session = True
        except ClientError as e:
            print(e.response)
            speech_output = "There was a problem deleting " + eventName + ". Please try again."
            reprompt_text = speech_output
    else:
        speech_output = "I'm sorry, I was unable to find that event. Please try again."
        reprompt_text = speech_output
        
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, None, should_end_session))   
        
def populateEvents():
    global userID
    global eventList
    
    try:
        curDate = datetime.datetime.now().date()
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('EventCountdown')
        response = table.query(
            KeyConditionExpression=Key('UserID').eq(userID)
        )
        dbQueried = True
        eventCount = len(response['Items'])
        for idx, item in enumerate(response['Items']):
            if item['StartDate'] >= datetime.datetime.strftime(curDate, '%Y-%m-%d'):
                eventList[item['EventName']] = item['StartDate']
    except ClientError as e:
        print(e.response)
    

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "AddIntent":
        return set_event_in_session(intent, session)
    elif intent_name == "ListIntent":
        return get_events_from_session(intent, session)
    elif intent_name == "CountdownIntent":
        return get_countdown_from_session(intent, session)
    elif intent_name == "DateIntent":
        return set_date_in_session(intent, session)
    elif intent_name == "YesIntent":
        return yes(intent, session)
    elif intent_name == "NoIntent":
        return no(intent, session)
    elif intent_name == "DeleteIntent":
        return delete_event(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    if (event['session']['application']['applicationId'] !=
             "amzn1.ask.skill.67911cf8-6056-46b0-94bf-7f1d7f454414"):
        raise ValueError("Invalid Application ID " + event['session']['application']['applicationId'])
    
    global userID
    userID = event['session']['user']['userId']

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
