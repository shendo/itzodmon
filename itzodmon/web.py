#!/usr/bin/env python

# itzodmon - pool.itzod.ru bitcoin mining pool monitor
# Copyright (C) 2013 Steve Henderson
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import json
import logging
import sys
import time

from bottle import request, response, route, run, static_file
import requests

from datastore import Datastore, get_period
from timer import Timer

DATASTORE = None
URL = None
KEY = None

def poll():
    try:
        r = requests.get("%s?act=getworkerstats&key=%s" % (URL, KEY))
        r.raise_for_status()
        DATASTORE.addworkerstats(time.time(), r.json())
    except requests.exceptions.RequestException:
        pass

@route('/<filename:re:.*\.(js|html|css|png|ico)>')
def static(filename):
    return static_file(filename, root='html')

def jsonize(data):
    response.content_type = 'application/json'
    return json.dumps(data)
    
@route("/api/poolstats")
def poolstats():
    try:
        r = requests.get("%s?act=getpoolstats" % URL)
        r.raise_for_status()
        return r.json()        
    except:
        return {}
 
@route("/api/userstats")
def userstats():
    try:
        r = requests.get("%s?act=getuserstatsext&key=%s" % (URL, KEY))
        r.raise_for_status()
        stats = r.json().copy()
        stats['username'] = KEY.split('_')[0]
        return stats
    except:
        return {}
    
@route("/api/hashrate")
def hashrate():
    period = get_period(request.query.period or 'Day')
    return jsonize([ x for x in DATASTORE.gethashrate(period)])

@route("/api/rejectrate")
def rejectrate():
    # approximate based on percentage of shares
    period = get_period(request.query.period or 'Day')
    return jsonize([ x for x in DATASTORE.getrejectrate(period)])

@route("/api/diff2rate")
def diff2rate():
    period = get_period(request.query.period or 'Day')
    return jsonize([ x for x in DATASTORE.getdiffrate(2, period)])

@route("/api/diff4rate")
def diff4rate():
    period = get_period(request.query.period or 'Day')
    return jsonize([ x for x in DATASTORE.getdiffrate(4, period)])

@route("/api/diff8rate")
def diff8rate():
    period = get_period(request.query.period or 'Day')
    return jsonize([ x for x in DATASTORE.getdiffrate(8, period)])

@route("/api/diff16rate")
def diff16rate():
    period = get_period(request.query.period or 'Day')
    return jsonize([ x for x in DATASTORE.getdiffrate(16, period)])

@route("/api/diff32rate")
def diff32rate():
    period = get_period(request.query.period or 'Day')
    return jsonize([ x for x in DATASTORE.getdiffrate(32, period)])

@route("/api/diff64rate")
def diff64rate():
    period = get_period(request.query.period or 'Day')
    return jsonize([ x for x in DATASTORE.getdiffrate(64, period)])

@route("/api/diff128rate")
def diff128rate():
    period = get_period(request.query.period or 'Day')
    return jsonize([ x for x in DATASTORE.getdiffrate(128, period)])

@route("/api/diff256rate")
def diff256rate():
    period = get_period(request.query.period or 'Day')
    return jsonize([ x for x in DATASTORE.getdiffrate(256, period)])

@route("/api/diff512rate")
def diff512rate():
    period = get_period(request.query.period or 'Day')
    return jsonize([ x for x in DATASTORE.getdiffrate(512, period)])

def start():
    global DATASTORE, URL, KEY
    
    default_tmp = "/tmp/itzod"
    if sys.platform.startswith('win'):
        default_tmp = "C:\\temp\\itzod"
        
    parser = argparse.ArgumentParser()
    parser.add_argument("-H", "--host", help="Web server Host address to bind to", 
                        default="0.0.0.0", action="store", required=False)
    parser.add_argument("-p", "--port", help="Web server Port to bind to", 
                        default=8000, action="store", required=False)
    parser.add_argument("-k", "--key", help="Itzod User APIKey for accessing json urls",
                        action="store", required=True)
    parser.add_argument("-u", "--url", help="Base itzod URL for accessing api",
                        default="https://pool.itzod.ru/apiex.php",
                        action="store", required=False)
    parser.add_argument("-d", "--datadir", help="Data directory to store state",
                        default=default_tmp,
                        action="store", required=False)
    args = parser.parse_args()
    
    logging.basicConfig()
    DATASTORE = Datastore(args.datadir)
    URL = args.url
    KEY = args.key
    
    t = Timer(60, poll, ())
    t.start()
    
    run(host=args.host, port=args.port, reloader=True)
    
if __name__ == '__main__':
    start()
    