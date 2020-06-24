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

class pycal:

    def __init__(self):
        self.file = None
        self.dict = {'events': []}

    def parsefile(self, file):
        self.file = file
        fh = open(self.file)
        lst = []
        strtrans = str.maketrans('', '', '\r\n')
        for l in fh.readlines():
            l = l.translate(strtrans)
            l = l.replace('\,', ',')
            l = l.replace('\\n', ' ')
            lst.append(l)
        fh.close()
        return self.parse(lst)

    def parse(self, lst):
        insideevt = False
        evtdict = {}
        for l in lst:
            # l = l.translate(None, '\r\n')
            # l = l.replace('\,', ',')
            # l = l.replace('\\n', ' ')
            if l[0] == ' ':
                evtdict[k] = evtdict[k] + l[1:]
            else:
                ll = l.split(':')
                if len(ll) < 2:
                    print("error")
                else:
                    k = ll[0]
                    v = ':'.join(ll[1:])
                    if insideevt:
                        if k == 'END' and v == 'VEVENT':
                            self.dict['events'].append(evtdict)
                            evtdict = {}
                            insideevt = False
                        else:
                            evtdict[k] = v
                    elif k == 'BEGIN' and v == 'VEVENT':
                        insideevt = True
                    elif k == 'END' and v == 'VCALENDAR':
                        break
                    else:
                        self.dict[k] = v

        return self.dict


def parsefile(file):
    return pycal().parsefile(file)

def parse(lst):
    return pycal().parse(lst)
