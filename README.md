# Merge2Cal

The merge2cal script collects information from indico agendas (e.g. https://indico.cern.ch/) and merges them into a single google calendar. The script is written in Python3 

## What it does

The script (calmerge.py) will crawl through event resources (eg. indico agendas) collect the entries in those agendas and merge them into one google calendar. The author being subscribed to multiple dozen indico agendas was motivated to write this script b/c

  - When subscribing to an indico agenda the corresponding events can be imported into a calendar tool but the subscribed calendar is note editable (e.g. an agenda contains various different events and one wants to remove some from the local calendar to not get cluttered)
  - The possibility to edit individual events before writing them into the google calendar (e.g. set different reminder times, add info in the text field, etc)
  - Subscribing to many individual calendars can make the local calendar tool unmanagable or slow 

## How it works

Once setup and calling calmerge.py the script will

1. Collect all events from the resources listed in the ```calendar.links``` file 
2. For each calendar entry compute a checksum and compare with the one in the ```calendar.cache``` file
   - if the checksum is the same (no changes) skip over the entry
   - otherwise compare the downloaded entries with the local ones and apply changes if needed. Those are 
     - add new entries
     - remove entries that don't exist anymore
     - if any part of an entry has changed, overwrite it with the new info
  
The entries in the local calendar can be deleted (e.g. to not clutter the local calendar) and will not be re-entered with a new run of the script. 

## How to add new resource entries

The file ```calendar.links``` contains all the resources (one per line) which the script will go through and collect information from. 

Lines starting with # will be ignored. 

A typical entry in the file looks like 

```
https://indico.cern.ch/export/categ/7970.ics?apikey=7ebebcbb-e2f9-468b-92ba-6d94ec1e22e0&from=-31d&signature=e500551e536da2d06f518c1d9948eb4e7f123807 # MND # 10 # HSF weekly
```

where the entries are separted by ```#``` delimiters

1. The source to collect the data from e.g. the link under "Export to scheduling tool" in indico
2. Whether the entry is mandatory (MND) or optional (OPT). OPT will be ignored in case of problems
3. The minutes to set the reminder in the local google calendar for the events
4. A string for convenience to document which entries the link correspond to 

## How to run it

```
python calmerge.py
```

## What else one can do with the script

### An entry in the local calendar was accidentally deleted

Remove also the corresponding calendar entry in the "cache" calendar and re-run the script. Go to the ```calendar.cache``` file and remove the entry in the json corresponding to the calendar which contains the entry. The entry should re-appear. 

NB: The cache file contains entries a la {"calendarid": checksum}, where calendar id corresponds to the "ics" number in the indico url.

### Delete unwanted calendar entries

Remove them in your google calendar, they won't re-appear when the script is re-run


## Notes

- Google allows so many interactions with the calendar API per period of time. I advise to not run the script too often (though cached entries will not issue API calls)

A few ideas for the script which have not or only partly been implemented

- use a proper configuration file for setup (file and reading of it exists but is not used)
- use a filtering mechanism, e.g. ignore events in a category which contain string "XYZ" (partly works)
- use other sources to retrieve event data. For the moment only indico is supported (via module pycal in the local directory)

## Getting Started

### Initial Setup

#### Authenticate against your Google calendar

In order to write to a google calendar you need to setup oauth2 authentication. You can use the script in <home>/oauth2 to do so.

1. Download the initial google credentials
  - Go to the [Google API console](https://console.developers.google.com/)
  - If you haven't done so you need to create a project first.
  - Enable the Calendar api in your project by clicking "Enable APIs and services" in the top of the dashboard. Search for "Google Calendar API" and enable it.
  - Make sure you have a OAuth consent screen configured by clicking the "OAuth consent screen" in the left pane. You need to add the scope "../auth/calendar.events". Google will warn you that this will require verification but you can just click "Save" and not submit it for verification and use it in development mode.
  - click "Credentials" on the left pane.
  - On the new page clicke "Create Credentials" (top) and select "Oauth client ID"
  - In the drop down menu select "Desktop app" and give it some name and "Create"
  - You are now back to the previous page. Under the "OAuth 2.0 Client IDs" go to the line of your app and download the corresponding file (most right). The file should have a name "client_secret_<userid>-<looongstring>.apps.googleusercontent.com.json" and look like

  ```
  {"installed":{"client_id":"<removed>.apps.googleusercontent.com","project_id":"api-project-<removed>","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"<removed>","redirect_uris":["urn:ietf:wg:oauth:2.0:oob","http://localhost"]}}
  ```
  - Copy that file into the directory where the oauth2.py script lives and rename/symlink it to ```client_secrets.json```
2. Run ```python oauth2.py```
  - The script will ask you to call a URL, copy paste it to your favorite browser and follow the instructions there. The outcome should be a new URL like ```http://localhost/?code=<very long string>&scope=https://www.googleapis.com/auth/calendar```
  - Take the ```<very long string>``` from above and paste it into the script
  - The script should return with a new json file a la 
    ```
    {"_module": "oauth2client.client", "scopes": ["https://www.googleapis.com/auth/calendar"], "token_expiry": "2018-09-11T14:51:13Z", "id_token": null, "access_token": "<removed>", "token_uri": "https://accounts.google.com/o/oauth2/token", "invalid": false, "token_response": {"access_token": "<removed>", "scope": "https://www.googleapis.com/auth/calendar", "token_type": "Bearer", "expires_in": 3600, "refresh_token": "<removed>"}, "client_id": "<removed>.apps.googleusercontent.com", "token_info_uri": "https://www.googleapis.com/oauth2/v3/tokeninfo", "client_secret": "<removed>", "revoke_uri": "https://accounts.google.com/o/oauth2/revoke", "_class": "OAuth2Credentials", "refresh_token": "<removed>", "user_agent": null}
    ```
3. Take the output of the script and write it to a ```calsecrets.json``` file in the home diretory (one level above where also calmerge.py sits)
4. Don't worry you only need to do this once ;-)

#### Handle Google calendars

For the script to work you need two calendars. One "visible" and one for "caching"

1. Go to your [Google calendar](https://calendar.google.com/calendar/) and create two new calendars. Click "+" next to "Other calendars". Any name is fine
2. Back to the main calendar page select each of the calendars click the triple "." on the right side, select "Settings and sharing"
  - Go down to "Integrate calendar" and copy the "Calendar ID" string e.g. ```21v7349crguab2ua591aguqkj4@group.calendar.google.com```
3. Now open the ```calmerge.py``` file and search for "<26alnums>". You should fine code lines which look like

```
self.calendarids = {'all2': {'id': '<26alnums>@group.calendar.google.com'},  # noqa: E501                                                                                                         
                    'vrk2': {'id': '<26alnums>@group.calendar.google.com'}   # noqa: E501                                                                                                         
                            }
```
4. Replace the string ```id``` of ```all2``` (```<26alnums>@group.calendar.google.com```) with the id of the "caching" calendar and the ```vrk2``` with the "visible" calendar id. 

### Dependencies

Please see the ```calmerge.py``` and ```oauth2.py``` scripts for python module dependencies ;-)

***

Stefan Roiser, [stefan.roiser@cern.ch](mailto:stefan.roiser@cern.ch)

