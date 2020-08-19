import codecs
# import inspect
# import urllib2
# import urllib
import requests
import time
import json

from .exceptions import FSConnectionError

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

from .morphlinks import ML


# http://push.api.bbci.co.uk/p?t=morph%3A%2F%2Fdata%2Fbbc-morph-football-scores-match-list-data%2FendDate%2F2017-08-31%2FstartDate%2F2017-08-01%2Ftournament%2Fpremier-league%2Fversion%2F2.2.3%2FwithPlayerActions%2Ffalse&c=1

# '/data/bbc-morph-sport-teams-competitions-list/competitionURLTemplate/%2Fsport%2Ffootball%2F%7B%7Bslug%7D%7D%2Fscores-fixtures/sport/football/teamURLTemplate/%2Fsport%2Ffootball%2Fteams%2F%7B%7Bslug%7D%7D%2Fscores-fixtures/version/1.0.0'
# '/data/bbc-morph-football-teams-competitions-list/competitionURLTemplate/%2Fsport%2Ffootball%2F%7B%7Bslug%7D%7D%2Fscores-fixtures/teamURLTemplate/%2Fsport%2Ffootball%2Fteams%2F%7B%7Bslug%7D%7D%2Fscores-fixtures/version/3.1.0'
# "/data/bbc-morph-football-teams-competitions-list/teamURLTemplate/%2Fsport%2Ffootball%2Fteams%2F%7B%7Bslug%7D%7D%2Fscores-fixtures/version/3.1.0"

API_BASE = "http://push.api.bbci.co.uk/p"
API_MORPH = "morph:/"



REFERER = "http://www.bbc.co.uk/sport/football/scores-fixtures"

class matchcommon(object):
    '''class for common functions for match classes.'''

    LAST_REQUEST = 0
    REQUEST_COUNT = 1

    def __init__(self, retry_count=5, timeout=0.5):
        self.RETRY_COUNT = retry_count
        self.TIMEOUT = 0.5

    # livescoreslink = ("http://www.bbc.co.uk/sport/shared/football/live-scores/matches/{comp}/today")

    # def getPage(self, url, sendresponse = False):
    #     page = None
    #     try:
    #         # user_agent = ('Mozilla/5.0 (Windows; U; Windows NT 6.1; '
    #         #               'en-US; rv:1.9.1.5) Gecko/20091102 Firefox')
    #         # headers = { 'User-Agent' : user_agent }
    #
    #         request = urllib2.Request(url)
    #         response = urllib2.urlopen(request)
    #         page = response.read()
    #     except:
    #         pass
    #
    #     if sendresponse:
    #         return response
    #     else:
    #         # Fixed this line to handle accented team namess
    #         return codecs.decode(page, "utf-8") if page else None

    def __create_payload(self, page):

        now = time.time()
        if now - type(self).LAST_REQUEST < 30:
            type(self).REQUEST_COUNT += 1
        else:
            type(self).REQUEST_COUNT = 1

        page = API_MORPH + page

        type(self).LAST_REQUEST = now

        return {"t": page, "c": type(self).REQUEST_COUNT}


    def sendRequest(self, page):

        payload = self.__create_payload(page)

        for _ in range(self.RETRY_COUNT):
            try:
                result = requests.get(API_BASE, params=payload,
                                      headers={"Referer": REFERER}).json()
                if result["moments"]:
                    return result["moments"]
            except JSONDecodeError:
                pass
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as e:
                    raise FSConnectionError

            time.sleep(self.TIMEOUT)

        return None

    def requestPushStream(self, page):

        payload = self.__create_payload(page)

        r = requests.get(API_BASE, params=payload,
                         headers={"Referer": REFERER}, stream=True).json()

        # for line in r.iter_lines():
        #     if line:
        #         print line

    def getTeams(self):

        teams = self.sendRequest(ML.MORPH_TEAMS_COMPS)

        if teams:
            teams = json.loads(teams[0]["payload"])
            return [x for x in teams if "teams" in x["url"]]

    def getTournaments(self):

        teams = self.sendRequest(ML.MORPH_TEAMS_COMPS)

        if teams:
            teams = json.loads(teams[0]["payload"])
            return [x for x in teams if "teams" not in x["url"]]


def getAllTeams():
    return matchcommon().getTeams()

def getAllTournaments():
    return matchcommon().getTournaments()
