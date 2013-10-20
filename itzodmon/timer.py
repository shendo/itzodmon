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

from threading import Thread, Event
import time

class Timer(Thread):
    def __init__(self, interval, target, args=()):
        super(Timer, self).__init__()
        self.status = Event()
        self.interval = interval
        self.target = target
        self.args = args
        self.daemon = True

    def stop(self):
        self.status.set()

    @property
    def stopped(self):
        return self.status.isSet()
    
    def run(self):
        while True:
            if self.stopped:
                return
            start = time.time()
            self.task()
            last = time.time() - start
            self.status.wait(max(0, self.interval - last))

    def task(self):
        if not self.target:
            raise NotImplementedError
        self.target(*self.args)
        