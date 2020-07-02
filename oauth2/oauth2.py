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

from oauth2client.client import flow_from_clientsecrets
import os,sys

flow = flow_from_clientsecrets(os.path.realpath(os.curdir)+os.sep+'client_secrets.json',
                               scope='https://www.googleapis.com/auth/calendar',
                               redirect_uri='http://localhost')

uri = flow.step1_get_authorize_url()


print("Call this URL in a browser")
print(uri)

print()
print("Then input the 'code' in the return path here :")

code = sys.stdin.readline()[:-1]

cred = flow.step2_exchange(code)

print("The credentials are: ")
print()

print(cred.to_json())

