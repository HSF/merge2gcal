import pytz
from datetime import datetime

tz1 = 'DTSTART;VALUE=DATE-TIME:20010613T130000Z'
tz2 = 'DTSTART;TZID=UTC:20160113T092500'
tz3 = 'DTSTART;TZID=W. Europe Standard Time:20160201T083000'

timeformat = '%Y%m%dT%H%M%SZ'
utctz = pytz.timezone('UTC')
tzdict = {'default' : pytz.timezone('Europe/Zurich'),
          'TZID=W. Europe Standard Time' : pytz.timezone('Europe/Zurich'),
          'VALUE=DATE-TIME' : pytz.timezone('Europe/Zurich'),
          'TZID=UTC' : pytz.timezone('UTC'),
}

def inUtc(timestr) :
    ret = None
    timestrl = timestr.split(':')
    tzinfo = timestrl[0]
    tminfo = timestrl[1]
    if len(timestrl) > 2 : print 'error, cannot decode time string', timestr

    if tminfo[-1] != 'Z' : tminfo += 'Z'

    tzdictkeys = tzdict.keys()
    if tzinfo in tzdictkeys :
        ret = tzdict[tzinfo].localize(datetime.strptime(tminfo,timeformat))
    else :
        try :
            timezone = pytz.timezone(tzinfo.split('=')[-1])
            print 'Using new timezone %s, pls add to config' % tzinfo
            ret = timezone.localize(datetime.strptime(tminfo, timeformat))
        except Exception,e:
            print 'Cannot use time zone info %s, because of: %s' % ( tzinfo, e)

    return ret, ret.astimezone(utctz).isoformat()


print inUtc(';'.join(tz1.split(';')[1:]))
print inUtc(';'.join(tz2.split(';')[1:]))
print inUtc(';'.join(tz3.split(';')[1:]))
