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

from datetime import timedelta
import glob
import os
import re
import time

import whisper

HOUR = 3600
DAY = timedelta(days=1).total_seconds()
WEEK = timedelta(days=7).total_seconds()
MONTH = timedelta(days=30).total_seconds() # close enough
YEAR = timedelta(days=365).total_seconds()

RETENTION = [ whisper.parseRetentionDef(x)
            for x in ["60:70", "10m:150", "1h:8d", "4h:31d", "1d:366d"] ]

def get_period(label):
    label = label.lower()
    if 'hour' in label:
        return HOUR
    elif 'week' in label: 
        return WEEK
    elif 'month' in label:
        return MONTH
    elif 'year' in label:
        return YEAR
    return DAY #default

class Datastore(object):
    
    def __init__(self, path):
        self.path = path
        self.workersprev = {}
        try:
            os.mkdir(path)
        except OSError:
            pass
    
    def addworkerstats(self, time, stats):
        for w in stats:
            name = w.get("username", "unknown")
            prev = self.workersprev.get(name, {})
            
            # gauges
            w_speed = w.get("w_speed", 0)
            # counters (delta from last period)
            if prev:
                shares_total = int(w['shares_total']) - int(prev["shares_total"])
                shares_accepted = int(w['shares_accepted']) - int(prev["shares_accepted"])
                shares_diff1_approx = int(w['shares_diff1_approx']) - int(prev["shares_diff1_approx"])
                shares_diff2 = int(w['shares_diff2']) - int(prev["shares_diff2"])
                shares_diff4 = int(w['shares_diff4']) - int(prev["shares_diff4"])
                shares_diff8 = int(w['shares_diff8']) - int(prev["shares_diff8"])
                shares_diff16 = int(w['shares_diff16']) - int(prev["shares_diff16"])
                shares_diff32 = int(w['shares_diff32']) - int(prev["shares_diff32"])
                shares_diff64 = int(w['shares_diff64']) - int(prev["shares_diff64"])
                shares_diff128 = int(w['shares_diff128']) - int(prev["shares_diff128"])
                shares_diff256 = int(w['shares_diff256']) - int(prev["shares_diff256"])
                shares_diff512 = int(w['shares_diff512']) - int(prev["shares_diff512"])
                
                # handle counter rollover / resets
                if shares_total < 0: shares_total = int(w['shares_total'])
                if shares_accepted < 0: shares_accepted = int(w['shares_accepted'])
                if shares_diff1_approx < 0: shares_diff1_approx = int(w['shares_diff1_approx'])
                if shares_diff2 < 0: shares_diff2 = int(w['shares_diff2'])
                if shares_diff4 < 0: shares_diff4 = int(w['shares_diff4'])
                if shares_diff8 < 0: shares_diff8 = int(w['shares_diff8'])
                if shares_diff16 < 0: shares_diff16 = int(w['shares_diff16'])
                if shares_diff32 < 0: shares_diff32 = int(w['shares_diff32'])
                if shares_diff64 < 0: shares_diff64 = int(w['shares_diff64'])
                if shares_diff128 < 0: shares_diff128 = int(w['shares_diff128'])
                if shares_diff256 < 0: shares_diff256 = int(w['shares_diff256'])
                if shares_diff512 < 0: shares_diff512 = int(w['shares_diff512'])
            
                shares_rejected = shares_total - shares_accepted
                self._addvalue(name, "shares.total", time, shares_total, 'sum')
                self._addvalue(name, "shares.rejected", time, shares_rejected, 'sum')
                self._addvalue(name, "shares.diff1a", time, shares_diff1_approx, 'sum')
                self._addvalue(name, "shares.diff2", time, shares_diff2, 'sum')
                self._addvalue(name, "shares.diff4", time, shares_diff4, 'sum')
                self._addvalue(name, "shares.diff8", time, shares_diff8, 'sum')
                self._addvalue(name, "shares.diff16", time, shares_diff16, 'sum')
                self._addvalue(name, "shares.diff32", time, shares_diff32, 'sum')
                self._addvalue(name, "shares.diff64", time, shares_diff64, 'sum')
                self._addvalue(name, "shares.diff128", time, shares_diff128, 'sum')
                self._addvalue(name, "shares.diff256", time, shares_diff256, 'sum')
                self._addvalue(name, "shares.diff512", time, shares_diff512, 'sum')
                
            self._addvalue(name, "speed", time, w_speed)
            self.workersprev[name] = w

            
    
    def _addvalue(self, worker, stat, time, value, aggmethod='average'):
        path = os.path.join(self.path, "%s.%s.db" % (worker, stat))
        if not os.path.exists(path):
            whisper.create(path, RETENTION, aggregationMethod=aggmethod)
        whisper.update(path, value, time)
    
    def _getvalues(self, worker, stat, start, end):
        path = os.path.join(self.path, "%s.%s.db" % (worker, stat))
        return whisper.fetch(path, end, start)
        
    def _getworkernames(self):
        return [ re.match(r".*[\\/]([\w_\-0-9]+)\.speed\.db", x).group(1) \
                for x in glob.glob(os.path.join(self.path, "*.speed.db")) ]
                
    def getworkerstats(self, period=DAY):
        start = time.time()
        end = start - period
        
        workerstats = {}
        for name in self._getworkernames():
            worker = {}
            tinfo, values = self._getvalues(name, "speed", start, end)
            
            worker['times'] = {'start': tinfo[0],
                               'end': tinfo[1],
                               'step': tinfo[2]}
            worker['speed'] = values
            worker['shares.total'] = self._getvalues(name, "shares.total", start, end)[1]
            worker['shares.rejected'] = self._getvalues(name, "shares.rejected", start, end)[1]
            worker['shares.diff1a'] = self._getvalues(name, "shares.diff1a", start, end)[1]
            worker['shares.diff2'] = self._getvalues(name, "shares.diff2", start, end)[1]
            worker['shares.diff4'] = self._getvalues(name, "shares.diff4", start, end)[1]
            worker['shares.diff8'] = self._getvalues(name, "shares.diff8", start, end)[1]
            worker['shares.diff16'] = self._getvalues(name, "shares.diff16", start, end)[1]
            worker['shares.diff32'] = self._getvalues(name, "shares.diff32", start, end)[1]
            worker['shares.diff64'] = self._getvalues(name, "shares.diff64", start, end)[1]
            worker['shares.diff128'] = self._getvalues(name, "shares.diff128", start, end)[1]
            worker['shares.diff256'] = self._getvalues(name, "shares.diff256", start, end)[1]
            worker['shares.diff512'] = self._getvalues(name, "shares.diff512", start, end)[1]
            
            workerstats[name] = worker
             
            
        return workerstats
    
    def gethashrate(self, period=DAY):
        if self.getworkerstats(period):
            _, val = self.getworkerstats(period).popitem()
            time = val['times']['start'] - val['times']['step']
            for x in val['speed']:
                if x:
                    x*= 1000000
                time += val['times']['step']
                yield time, x, val['times']['step']
    
    def getrejectrate(self, period=DAY):
        if self.getworkerstats(period):
            _, val = self.getworkerstats(period).popitem()
            time = val['times']['start'] - val['times']['step']
            for i, rej in enumerate(val['shares.rejected']):
                tot = val['shares.total'][i]
                speed = val['speed'][i]
                if rej and tot and speed:
                    rej = rej / tot * speed * 1000000
                elif rej:
                    rej = 0
                time += val['times']['step']
                yield time, rej, val['times']['step']
                
    def getdiffrate(self, diff, period=DAY):
        assert diff in [2, 4, 8, 16, 32, 64, 128, 256, 512]        
        if self.getworkerstats(period):
            _, val = self.getworkerstats(period).popitem()
            time = val['times']['start'] - val['times']['step']
            for x in val['shares.diff%i' % diff]:
                if x:
                    x*= pow(2, 32) * diff / val['times']['step']
                elif all( not v for v in val['shares.diff%i' % diff]):
                    x = None
                time += val['times']['step']
                yield time, x, val['times']['step']

