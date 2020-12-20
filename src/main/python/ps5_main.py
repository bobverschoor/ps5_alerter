import random

import requests
import configparser
import os
import datetime

BASE_URL = "https://api.telegram.org/bot"
SECRETS_FILE = 'resource/secrets.txt'
WINKELS_FILE = 'resource/winkels.txt'
TELEGRAM = 'telegram'
CHANNEL_ID = 'channel_id'
TOKEN = 'TOKEN'
WINKEL = 'winkel'
VOORRAAD_TEKST = 'voorraad_tekst'
URL = 'url'


def get_secrets():
    config = configparser.ConfigParser()
    if os.path.isfile(SECRETS_FILE):
        config.read(SECRETS_FILE)
        if TELEGRAM in config:
            if CHANNEL_ID in config['telegram'] and TOKEN in config[TELEGRAM]:
                return config
            else:
                print("Config file not properly filled, missing chanel_id of token")
        else:
            print('Config does not contain telegram section')
    else:
        print("Put your token and channel_id in a resources/secrets.txt file")
    exit(1)


def get_winkels():
    winkels = configparser.ConfigParser()
    if os.path.isfile(WINKELS_FILE):
        winkels.read(WINKELS_FILE)
    return winkels


def leverbaar(url, check):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_' + str(random.randint(0,9))
    }
    #amazon redirects indien geen browser-achtige user agent
    s = requests.session()
    r = s.get(url, headers=headers)
    if r.status_code == 200:
        if check in r.text:
            return False
        else:
            print(r.text)
            return True
    else:
        print(r.status_code)
        print(url)
        return False

def notify(message):
    secret = get_secrets()
    # telegram wil -100 voor chat_id indien een bot
    message = {'chat_id': "-100" + secret[TELEGRAM][CHANNEL_ID],
               'text': message}
    r = requests.post(BASE_URL + secret[TELEGRAM][TOKEN] + "/sendMessage", data=message)
    if r.status_code == 200:
        return True
    else:
        print(r.text)
        exit(1)


def main():
    winkel = get_winkels()
    genotificeerd = False
    winkels = ""
    for winkelnaam in winkel.sections():
        if winkels == "":
            winkels = winkelnaam
        else:
            winkels += ', ' + winkelnaam
        if leverbaar(winkel[winkelnaam][URL], winkel[winkelnaam][VOORRAAD_TEKST]):
            genotificeerd = notify(winkelnaam + '\n' + winkel[winkelnaam][URL])
        else:
            pass
            #print("niet leverbaar bij " + winkelnaam)
    if not genotificeerd:
        now = datetime.datetime.now()
        if now.minute == 0 and 6 < now.hour < 22:
            notify(winkels + '\nhebben de ps5 niet op voorraad.')



if __name__ == "__main__":
    main()
