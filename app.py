#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

@app.route('/webget', methods=['GET'])
def webget():
    print("Request:")
    
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    yql_query ="select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='newyork') limit 2"
    yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
    result = urlopen(yql_url).read()
    data = json.loads(result)
    res = makeWebhookResult(data,"Tomorrow")

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
    if req.get("result").get("action") != "yahooWeatherForecast":
        return {}
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    yql_query = makeYqlQuery(req)
    if yql_query is None:
        return {}
    yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
    result = urlopen(yql_url).read()
    data = json.loads(result)
    
    result = req.get("result")
    parameters = result.get("parameters")
    time = parameters.get("time")
    if time is None:
      time = ""
    else:
      if time == "tomorrow":
        time = " limit 2 "
      elif time > 1:
        time = " limit " + time + " "
      else:
        time = ""

    res = makeWebhookResult(data,time)
    return res


def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    if city is None:
        return None

    time = parameters.get("time")
    if time is None:
      time = ""
    else:
      if time == "tomorrow":
        time = " Tomorrow "
      elif time > 1:
        time = "After " + time + " days "
      else:
        time = ""

    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "') " + time


def makeWebhookResult(data,time):
    query = data.get('query')
    url = "failed"
    if query is None:
        return {
            "speech": "url",
            "displayText": url,
            # "data": data,
            # "contextOut": [],
            "source": "apiai-weather-webhook-sample"
        }
    result = query.get('results')
    if result is None:
        return {
            "speech": "url",
            "displayText": url,
            # "data": data,
            # "contextOut": [],
            "source": "apiai-weather-webhook-sample"
        }
    channel = result.get('channel')
    if channel is None:
        return {
            "speech": "url",
            "displayText": url,
            # "data": data,
            # "contextOut": [],
            "source": "apiai-weather-webhook-sample"
        }
    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))
 
    if time is None:
        speech = "Today in " + location.get('city') + ": " + condition.get('text') + \
             ", the temperature is " + condition.get('temp') + " " + units.get('temperature')
    else:
        forecast = item.get('forecast')
        speech =  time + " the forecast for " + location.get('city') + ": " + forecast[-1].get('text')+ \
             ", the temperature can range between " + forecast[-1].get('low') + units.get('temperature') + " to " + forecast[-1].get('high') + units.get('temperature')
    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
