#!/usr/bin/env python3

# (c) Copyright 2015-2020 CERN
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Stefan Roiser (stefan.roiser@cern.ch)

import json
import httplib2
import icalendar
import urllib.request
import urllib.parse
import urllib.error
import time
import platform
import sys
import os
from oauth2client.client import OAuth2Credentials
from apiclient.discovery import build
from datetime import datetime, timedelta
from hashlib import md5
from optparse import OptionParser
from configparser import ConfigParser

# TODO
# - check moved events from all to wrk and "rename" - currently just delete
#   "all" event to regenerate wrk one

# HOWTO
# turn off the "all" calendar from sync'ing
# https://medium.com/@the_possibility/stop-shared-calendar-notifications-google-calendars-on-iphone-mac-d20704b4038e#.suduwhek5   # noqa: E501
# (on the phone still produces alarms otherwise :-( )


class Calmerge:

    def log_error(self, msg):
        self.log('ERROR', msg)

    def log(self, lvl, msg):
        print(sys.stdout.write('%s %s %s' % (sys.argv[0], lvl, msg)))

    def __init__(self, clean=False, cfg=None, tst=None):
        self.clean = clean

        self.cfg_file = cfg
        if not self.cfg_file:
            self.cfg_file = 'calendar.cfg'
        if not os.path.isfile(self.cfg_file):
            self.log_error('cannot find config file %s' % self.cfg_file)
            sys.exit(1)

        self.tst_file = tst

        f = open(self.cfg_file)
        cfg = ConfigParser()
        try:
            cfg.read_file(f)
        except Exception as e:
            self.log_error(
                'problem while processing config file %s, %s' % (self.cfg_file,
                                                                 e))
        f.close()

        f = open('calsecret.json')
        # self.calsecret = json.loads(f.read())
        self.calsecret = f.read()
        f.close()

        try:
            # linkfile = cfg.get('Input', 'calendar_file')
            f = open('calendar.links')
            self.calendarlinks = f.readlines()
            f.close()
        except Exception as e:  # NoOptionError:
            print(e)

        self.calcache = {}
        f = open('calcache.json')
        self.calcache = json.loads(f.read())
        f.close()

        # alphabetically ordered
        self.calexts = ['all2', 'vrk2']
        self.calendarids = {'all2': {'id': 'mh9up33b8s0m8ba6i4m3sanb08@group.calendar.google.com'},  # noqa: E501
                            'vrk2': {'id': 'jd5bdhh5eq2sigqtvg6q3l8el8@group.calendar.google.com'}   # noqa: E501
                            }

        self.calevtslist = []
        self.calevtslistids = {}
        self.calevts = None
        self.caldelevts = []

        now = datetime.now()
        self.midnight = datetime(now.year, now.month, now.day)

        f = open('calendar-filter.json')
        self.filter = json.loads(
            ''.join([x for x in f.readlines() if x[0] != '#']))
        f.close()

    def generateEvent(self, evt, reminders):
        params = {
            'id': evt['UID'],
            'summary': evt['SUMMARY'],
            'description': 'Event URL: %s\n\n%s' % (evt['URL'],
                                                    evt['DESCRIPTION']),
            'location': evt['LOCATION'],
            'start': {'timeZone': 'UTC'},
            'end': {'timeZone': 'UTC'},
            'source': {
                'title': 'Indico URL',
                'url': evt['URL']
            }
        }
        start = evt['DTSTART']
        end = evt['DTEND']
        if start.year == end.year and start.month == end.month and\
           start.day == end.day:
            params['start']['dateTime'] = start.isoformat()
            params['end']['dateTime'] = end.isoformat()
        else:
            params['description'] = 'Event from %s to %s\n\n%s' % (
                start, end, params['description'])
            # https://developers.google.com/google-apps/calendar/concepts/events-calendars # noqa: E501
            end += timedelta(days=1)
            params['start']['date'] = '%s-%s-%s' % (
                start.year, start.month, start.day)
            params['end']['date'] = '%s-%s-%s' % (end.year, end.month, end.day)
        if len(reminders):
            params['reminders'] = {}
            params['reminders']['overrides'] = []
            for rem in reminders[:min(5, len(reminders))]:
                params['reminders']['overrides'].append(
                    {'minutes': rem, 'method': 'popup'})
            params['reminders']['useDefault'] = False
        return params

    def prePublish(self):
        cred = OAuth2Credentials.from_json(self.calsecret)
        http = httplib2.Http()
        cred.refresh(http)
        cred.authorize(http)
        calsvc = build('calendar', 'v3', http=http)
        self.calevts = calsvc.events()
        mindate = (self.midnight - timedelta(31)).isoformat() + 'Z'

        for k in list(self.calendarids.keys()):
            req = self.calevts.list(calendarId=self.calendarids[k]['id'],
                                    singleEvents=True, maxResults=2500,
                                    timeMin=mindate)
            calevtsdict = req.execute()
#            for kx in [u'nextPageToken', u'kind', u'defaultReminders',
#                       u'description', u'updated', u'summary', u'etag',
#                       u'timeZone', u'accessRole']:
#                print kx, calevtsdict[kx]
#            print calevtsdict.keys()
            self.caldelevts += [x['id'] for x in calevtsdict['items']
                                if (x['start'].get('dateTime')
                                and datetime.strptime(x['start']  # noqa: W503
                                    .get('dateTime')
                                    .split('T')[0], "%Y-%m-%d") > self.midnight
                                or x['start'].get('date')  # noqa: W503
                                and datetime.strptime(x['start']  # noqa: W503
                                    .get('date'), "%Y-%m-%d") > self.midnight)
                                and x['id'][-4:] == k]  # noqa: W503
            self.calevtslist += calevtsdict.get('items')
            # self.calevtslistids[k] = [ x['iCalUID'].split('@')[0]
            # for x in calevtsdict['items'] ]
            self.calevtslistids[k] = [x['id'] for x in calevtsdict['items']]
            print('Google calendar %s items: %d' % (k,
                                                    len(self.calevtslistids[k])))  # noqa: E501
            # print self.calevtslistids[k]
        # print self.calevtslistids

    def cleanAllEvents(self):
        for k in list(self.calevtslistids.keys()):
            calid = self.calendarids[k]['id']
            for evtid in self.calevtslistids[k]:
                time.sleep(.2)
                print("try to clean event", evtid)
                try:
                    req = self.calevts.delete(calendarId=calid, eventId=evtid)
                    req.execute()
                except Exception as e:
                    print('Delete did not work because of', e)

    def filterEvent(self, cat, event):
        if cat in self.filter:
            if 'filter' in self.filter[cat]:
                for filter in self.filter[cat]['filter']:
                    if eval(filter):
                        return True
        return False

    def calIdTranslate(self, id):
        return id.translate(str.maketrans('', '', '-@.'))

    def publishEvents(self, indicoevts, cat, rems):
        ret = [0, 0]  # total, new events
        for event in indicoevts:
            ret[0] += 1
            evtinf = self.generateEvent(event, rems)
            evtid = self.calIdTranslate(evtinf['id'])
            # in vrk, in all -> publish both
            # in vrk, not in all -> moved from all to vrk -> publish both
            # not in vrk, in all -> not important -> publish all
            # not in vrk, not in all -> new event -> publish both
            evtidvrk = evtid + self.calexts[1]  # vrk2
            evtidall = evtid + self.calexts[0]  # all2
            for cid in self.calexts:
                gid = evtid + cid
                if gid in self.caldelevts:
                    self.caldelevts.remove(gid)
            # print evtidvrk, evtidall
            # print self.calevtslistids['vrk2']
            # print self.calevtslistids['all2']
            if evtidvrk not in self.calevtslistids['vrk2'] and\
               evtidall in self.calevtslistids['all2']:
                self.publishEvent('all2', evtidall, evtinf)
            else:
                if not self.filterEvent(cat, evtinf):
                    if evtidvrk not in self.calevtslistids['vrk2']:
                        ret[1] += 1
                    self.publishEvent('vrk2', evtidvrk, evtinf, True)
                self.publishEvent('all2', evtidall, evtinf)
        return ret

    def publishEvent(self, calext, evtid, params, alarm=False):
        time.sleep(.3)  # slow down here
        params['id'] = evtid
        if not alarm:
            params['reminders'] = {}
        # print params
        calid = self.calendarids[calext]['id']
        if evtid in self.calevtslistids[calext]:
            req = self.calevts.update(
                calendarId=calid, eventId=evtid, body=params)
            try:
                req.execute()
            except Exception as e:
                print('update except', e)
        else:
            req = self.calevts.insert(calendarId=calid, body=params)
            try:
                req.execute()
            except Exception as e:
                je = json.loads(e.content)
                if je['error']['code'] == 409:
                    req = self.calevts.get(calendarId=calid, eventId=evtid)
                    # r = req.execute()
                    req.execute()
                    req = self.calevts.update(
                        calendarId=calid, eventId=evtid, body=params)
                    req.execute()

    def downloadics(self, url):
        urld = urllib.request.urlopen(url)
        ics = icalendar.Calendar.from_ical(urld.read())
        events = []
        for component in ics.walk():
            if component.name == "VEVENT":
                event = {key: component.get(key, None) for key in ['UID',
                                                                   'SUMMARY',
                                                                   'DESCRIPTION',  # noqa: E501
                                                                   'LOCATION',
                                                                   'URL']}
                event.update({key: component.decoded(key) for key in ['DTSTART',
                                                                      'DTEND']})
                events.append(event)
                idt = self.calIdTranslate(component.get('UID'))
                for ext in self.calexts:
                    idtext = idt + ext
                    if idtext in self.caldelevts:
                        self.caldelevts.remove(idt + ext)
        return events

    def delEvents(self):
        sumdelevts = len(self.caldelevts)
        if sumdelevts:
            print(len(self.caldelevts), "events to delete:")
            reallydelete = True
            if sumdelevts > 100:
                # some safety net to not delete in case of mistake
                reallydelete = False
                print('More than 10 events to delete, dry run', sumdelevts)
            for evt in self.calevtslist:
                for delevt in self.caldelevts:
                    if delevt == evt['id']:
                        print('event:', evt)
                        if reallydelete:
                            try:
                                print('deleting event')
                                req = self.calevts.delete(
                                    calendarId=self.calendarids[delevt[-4:]]
                                                               ['id'],
                                    eventId=delevt)
                                req.execute()
                            except Exception as e:
                                print("Delete did not work because of", e)

    def run(self):
        self.prePublish()
        if self.clean:
            self.cleanAllEvents()
        stats = {'sumCals': 0, 'totEvts': 0, 'newEvts': 0}
        for line in self.calendarlinks:
            lline = line.split('#')
            if len(lline[0].strip()):
                stats['sumCals'] += 1
                name = lline[-1].strip()
                rems = [int(x) for x in [x for x in lline[-2].split(',')] if len(x.strip())]  # noqa: E501
                url = lline[0].strip()
                sys.stdout.write(name)
                ics = self.downloadics(url)
                if len(ics) == 0:
                    sys.stdout.write(', no events')
                    # sys.stdout.write(str(ics))
                cat = ''
                if url.find('/category/') != -1:
                    cat = url.split('/')[4]
                else:
                    cat = url.split('/')[-1].split('.')[0]
                calhash = md5(str(ics).encode('utf-8')).hexdigest()
                if self.calcache.get(cat) != calhash:
                    self.calcache[cat] = calhash
                    ret = self.publishEvents(ics, cat, rems)
                    stats['totEvts'] += ret[0]
                    stats['newEvts'] += ret[1]
                else:
                    sys.stdout.write(', cached')
                print()

        self.delEvents()

        f = open('calcache.json', 'w')
        f.write(json.dumps(self.calcache))
        f.close()

        return """
Calendars: %d
Events Total/New: %d/%d""" % (stats['sumCals'], stats['totEvts'],
                              stats['newEvts'])


def notify(title, subtitle, info_text, delay=0, sound=False, userinfo={}):
    if platform.system() == 'Darwin':
        import objc
        import Foundation
        # import AppKit
        nsusernotification = objc.lookUpClass('NSUserNotification')
        nsusernotificationcenter = objc.lookUpClass('NSUserNotificationCenter')
        ntf = nsusernotification.alloc().init()
        ntf.setTitle_(title)
        ntf.setSubtitle_(subtitle)
        ntf.setInformativeText_(info_text)
        # notification.setUserInfo_(userinfo)
        ntf.setHasActionButton_(True)
        if sound:
            ntf.setSoundName_("NSUserNotificationDefaultSoundName")
        ntf.setDeliveryDate_(Foundation.NSDate.
                             dateWithTimeInterval_sinceDate_(delay,
                                                             Foundation.NSDate.
                                                             date()))
        nsusernotificationcenter.defaultUserNotificationCenter(
        ).scheduleNotification_(ntf)
    print('%s\n%s\n%s' % (title, subtitle, info_text))


if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option('-t', '--test', dest="test_input",
                      help="test with input file")
    parser.add_option('-c', '--config', dest="config_file",
                      help="use different config file")

    (options, args) = parser.parse_args()

    if args:
        print(sys.argv[0], "- no arguments allowed")
        parser.print_usage()

    # calmerge().run()

    # Calmerge(clean=False, cfg=options.config_file,
    #          tst=options.test_input).run()

    try:
        notify('Calendar Merge', '', Calmerge(clean=False,
                                              cfg=options.config_file,
                                              tst=options.test_input).run())
    except Exception as e:
        print(e)
        notify('Calendar Merge', 'Exception', e)
