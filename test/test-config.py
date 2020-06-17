from ConfigParser import ConfigParser

f = open('calendar.cfg')

cfg = ConfigParser()

try : 
    cfg.readfp(f)
except Exception,e:
    print e

print cfg

f.close()

for sec in cfg.sections() :
    print sec, cfg.items(sec)


print cfg.get('Input', 'calendar_file')

from optparse import OptionParser


if __name__ == '__main__' :

    parser = OptionParser()
    parser.add_option('-t', '--test', dest="test_input", help="test with input file")
    parser.add_option('-c', '--config', dest="config_file", help="use different config file")

    (options, args) = parser.parse_args()

    print 'cfg',options.config_file
    print 'tst',options.test_input
    print options
    print args


    

