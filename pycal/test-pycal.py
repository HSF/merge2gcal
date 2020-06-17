from pycal import pycal

pc = pycal()
d = pc.parse('caldown/mnd/GDB.ics')
print d['events'][0]
