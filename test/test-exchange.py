from icalendar import Calendar, prop
from datetime import datetime
import pytz

g = open('calendar.ics')
gcal = Calendar.from_ical(g.read())
g.close()

#print dir(gcal)

#print gcal.name,gcal.subcomponents[0]

tzdict = {'W. Europe Standard Time' : pytz.timezone('Europe/Zurich')}
tzutc = pytz.utc


data = {}

def icalConvert(v) :
    t = type(v)
    if t == prop.vText : return str(v)
    elif t == prop.vInt : return int(v)
    elif t == prop.vRecur : return dict(v)
    elif t == prop.vDDDTypes :
        d = {}
        d.update({'dt':v.dt})
        dtutc = None
        if not v.dt.tzinfo:
            if v.params:
                d.update(v.params)
                tzid = v.params.get('TZID')
                if tzdict.has_key(tzid) : dtutc = tzdict[tzid].localize(v.dt).astimezone(tzutc)
                else : dtutc = tzutc.localize(v.dt)
            else: dtutc = tzutc.localize(v.dt) # let's assume it's UTC
        else: dtutc = v.dt.astimezone(tzutc)
        d['dtutc'] = dtutc            
        return d
    elif t == prop.vUTCOffset : return v.td
    else :
        print type(v)
        return v

def walk(c,d) :
    if not d.has_key(c.name) : d[c.name] = []
    d[c.name].append({'attrs':{}})
    dp = d[c.name][-1]
    for k in c.keys() : dp['attrs'][k] = icalConvert(c[k])
    map(lambda x: walk(x,dp), c.subcomponents)

walk(gcal,data)

#print data['VCALENDAR'][0]['VTIMEZONE'][0]
#print
#print data['VCALENDAR'][0]['VTIMEZONE'][1]
#print
for ev in data['VCALENDAR'][0]['VEVENT'] :
    print
    print ev

# {'VCALENDAR': [
#     {'VTIMEZONE': [
#         {'attrs':{},
#          'DAYLIGHT': [
#              'attrs':{}
#          ],
#          'STANDARD': [
#              'attrs':{}
#          ]
#         }
#     ],
#      'VEVENT': [
#          {},
#          {}
#      ]
#     }
# ]
# }


#for c in gcal.walk() :
#    print c.name,c.subcomponents
    # if c.name == 'VEVENT' :
    #     for k in c.keys() :
    #         if k in ('DTSTART', 'DTEND') : print c[k].dt.utcoffset(), c[k].dt
    # else :
    #     print c.name, c.keys()
