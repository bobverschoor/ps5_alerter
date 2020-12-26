import random

import requests
import configparser
import os
import datetime

BASE_URL = "https://api.telegram.org/bot"
SECRETS_FILE = 'resource/secrets.txt'
WINKELS_FILE = 'resource/winkels.txt'
CONFIG_FILE = 'resource/config.txt'
TELEGRAM = 'telegram'
CHANNEL_ID = 'channel_id'
TOKEN = 'TOKEN'
WINKEL = 'winkel'
VOORRAAD_TEKST = 'voorraad_tekst'
URL = 'url'
NOTIFY = 'notify'
NOTIFY_START_UUR = 'start_uur'
NOTIFY_STOP_UUR = 'stop_uur'


def get_base_config(filename) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    if os.path.isfile(filename):
        config.read(filename)
    else:
        print("Missing file: " + filename)
        exit(1)
    return config


def get_secrets():
    config = get_base_config(SECRETS_FILE)
    if TELEGRAM in config:
        if CHANNEL_ID in config[TELEGRAM] and TOKEN in config[TELEGRAM]:
            return config
        else:
            print("Secrets file not properly filled, missing chanel_id of token")
    else:
        print('Secrets does not contain telegram section')
    exit(1)


def get_winkels():
    return get_base_config(WINKELS_FILE)


def valid_hours(value):
    if 0 <= value < 24:
        return True
    else:
        return False


def get_config():
    config_ok = True
    config = get_base_config(CONFIG_FILE)
    if NOTIFY in config:
        if NOTIFY_START_UUR in config[NOTIFY] and NOTIFY_STOP_UUR in config[NOTIFY]:
            if not valid_hours(int(config[NOTIFY][NOTIFY_START_UUR])) or \
               not valid_hours(int(config[NOTIFY][NOTIFY_STOP_UUR])):
                config_ok = False
                print("Config file values of " + NOTIFY + " not correct numbers, must be 0 - 23")
        else:
            config_ok = False
            print("Config file not properly filled, missing " + NOTIFY_START_UUR + " or " + NOTIFY_STOP_UUR)
    else:
        config_ok = False
        print("Config file not properly filled, missing " + NOTIFY)
    if config_ok:
        return config
    else:
        exit(1)


def leverbaar(url, check):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_' + str(random.randint(0, 9))
    }
    # amazon redirects indien geen browser-achtige user agent. daarnaast is er een soort bot detectie ;-0
    # Hopelijk werkt de randomizer op de useragent goed genoeg, icm de sessie, en dus acceptatie van cookies.
    s = requests.session()
    par = {"par":str(random.randint(0, 9))+str(random.randint(0, 9))+str(random.randint(0, 9))}
    r = s.get(url, headers=headers, params=par)
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


def notify(message, config):
    secret = get_secrets()
    now = datetime.datetime.now()
    # telegram wil -100 voor chat_id indien een bot
    message = {'chat_id': "-100" + secret[TELEGRAM][CHANNEL_ID],
               'text': message}
    if int(config[NOTIFY][NOTIFY_START_UUR]) <= now.hour < int(config[NOTIFY][NOTIFY_STOP_UUR]):
        r = requests.post(BASE_URL + secret[TELEGRAM][TOKEN] + "/sendMessage", data=message)
        if r.status_code == 200:
            return True
        else:
            print(r.text)
            exit(1)
    else:
        print("No notification due to configured time window")


def same_message(naam):
    lastmessage_file = "lastmessage"
    if naam == "":
        os.remove(lastmessage_file)
    else:
        if os.path.exists(lastmessage_file):
            return True
        else:
            with open(lastmessage_file, 'w') as fp:
                pass
    return False

def main():
    config = get_config()
    winkel = get_winkels()
    genotificeerd = False
    winkels = ""
    for winkelnaam in winkel.sections():
        if winkels == "":
            winkels = winkelnaam
        else:
            winkels += ', ' + winkelnaam
        if leverbaar(winkel[winkelnaam][URL], winkel[winkelnaam][VOORRAAD_TEKST]):
            if not same_message(winkelnaam):
                genotificeerd = notify(winkelnaam + '\n' + winkel[winkelnaam][URL], config)
        else:
            pass
            # print("niet leverbaar bij " + winkelnaam)
    if not genotificeerd:
        now = datetime.datetime.now()
        if now.minute == 0:
            same_message("")
            # Elk uur een notificatie om aan te tonen dat ie nog steeds draait en alles nog werkt.
            notify(winkels + '\nhebben de ps5 niet op voorraad.', config)


if __name__ == "__main__":
    main()
