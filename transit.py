from __future__ import print_function
from dateutil import parser

import datetime
import math
import requests
import xml.etree.ElementTree

API_KEY = "your key here"
CTA_BASE_URL = "http://www.ctabustracker.com/bustime/api/v1/"

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    if (event['session']['application']['applicationId'] !=
            "amzn1.echo-sdk-ams.app.39daee81-19a7-4dfe-9880-2c950b6da2ed"):
        raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


def on_session_started(session_started_request, session):
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
    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "GetBusPredictionIntent":
        return default_response(intent, session)
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here

# --------------- Functions that control the skill's behavior ------------------


def default_response(intent, session):
    session_attributes = {}

    if ('Direction' in intent['slots']) and ('value' in intent['slots']['Direction']):
        direction = intent['slots']['Direction']['value']
        minutes = get_prediction(direction)
        speech_output = "The next " + direction + " 8 bus will arrive in " + minutes + " minutes."
        return build_response(session_attributes, build_speechlet_response(speech_output, True))
    else:
        speech_output = "Which direction are you going?"
        return build_response(session_attributes, build_speechlet_response(speech_output, False))


# --------------- Helpers that build all of the responses ----------------------

def get_prediction(direction):
    if 'northbound' == direction:
        stop_id = "16050"
    elif 'southbound' == direction:
        stop_id = "17157"
    else:
        raise Exception("Invalid Direction")

    resp = cta_request("getpredictions", "&rt=8&stpid=" + stop_id)
    tree = xml.etree.ElementTree.fromstring(resp.content)
    next_bus_time = parser.parse(tree.find("prd").find("prdtm").text)

    timeresp = cta_request("gettime")
    now = parser.parse(xml.etree.ElementTree.fromstring(timeresp.content).find("tm").text)

    delta = (next_bus_time - now).total_seconds() / 60
    return str(int(math.floor(delta)))


def cta_request(action, params=""):
    return requests.get(CTA_BASE_URL + action + "?key=" + API_KEY + params)

def build_speechlet_response(output, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }