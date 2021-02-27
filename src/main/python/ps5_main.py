import random

import requests
import configparser
import os
import datetime
from bs4 import BeautifulSoup

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
NOTIFY_TEST_MINUTE = 'test_minute'
PROXY = 'proxy'
PROXY_PROVIDER = 'proxylist_provider'
BOT_DETECTIE = 'bot_detectie'


class Proxy:
    def __init__(self, proxylistprovider):
        self.proxylistprovider = proxylistprovider
        self.proxies = self.retrievelist()
        self.usedproxies = []

    def retrievelist(self):
        proxies = []
        r = requests.get(self.proxylistprovider)
        if r.status_code == 200:
            proxylist_html = BeautifulSoup(r.text, 'html.parser')
            lines = proxylist_html.find(id="raw").text
            for line in lines.splitlines():
                if line != "" and line[0].isdigit():
                    proxies.append(line.strip())
        return proxies

    def get_random_proxy(self):
        randomproxy = {'http': random.choice(self.proxies)}
        while randomproxy in self.usedproxies and len(self.proxies) > len(self.usedproxies):
            randomproxy = {'http': random.choice(self.proxies)}
        self.usedproxies.append(randomproxy)
        return randomproxy


def get_base_config(filename) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    if os.path.isfile(filename):
        config.read(filename)
    else:
        log("Missing file: " + filename)
        exit(1)
    return config


def log(message):
    now = str(datetime.datetime.now())
    print(now + "\t" + str(message))


def get_secrets():
    config = get_base_config(SECRETS_FILE)
    if TELEGRAM in config:
        if CHANNEL_ID in config[TELEGRAM] and TOKEN in config[TELEGRAM]:
            return config
        else:
            log("Secrets file not properly filled, missing chanel_id of token")
    else:
        log('Secrets does not contain telegram section')
    exit(1)


def get_winkels():
    return get_base_config(WINKELS_FILE)


def valid_hours(value):
    if 0 <= value < 24:
        return True
    else:
        return False


def valid_minute(value):
    if 0 <= value < 60:
        return True
    else:
        return False


def get_config():
    config_ok = True
    config = get_base_config(CONFIG_FILE)
    if NOTIFY in config:
        if NOTIFY_START_UUR in config[NOTIFY] and NOTIFY_STOP_UUR in config[NOTIFY] and \
                NOTIFY_TEST_MINUTE in config[NOTIFY]:
            if not valid_hours(int(config[NOTIFY][NOTIFY_START_UUR])) or \
               not valid_hours(int(config[NOTIFY][NOTIFY_STOP_UUR])):
                config_ok = False
                log("Config file values of " + NOTIFY + " not correct numbers, must be 0 - 23")
            if not valid_minute(int(config[NOTIFY][NOTIFY_TEST_MINUTE])):
                config_ok = False
                log("Config file values of " + NOTIFY + " not correct minute, must be 0 - 59")
        else:
            config_ok = False
            log("Config file not properly filled, missing " + NOTIFY_START_UUR + " or " + NOTIFY_STOP_UUR)
    else:
        config_ok = False
        log("Config file not properly filled, missing " + NOTIFY)
    if PROXY in config:
        if PROXY_PROVIDER in config[PROXY]:
            if not config[PROXY][PROXY_PROVIDER].startswith("http"):
                config_ok = False
                log("Config file value of " + PROXY + " not correct url.")
        else:
            config_ok = False
            log("Config file not properly filled, missing " + PROXY_PROVIDER)
    else:
        config_ok = False
        log("Config file not properly filled, missing " + PROXY)
    if config_ok:
        return config
    else:
        exit(1)


def checks_on_page(checks, page):
    checks = checks.split('|')
    for check in checks:
        if check in page:
            return True
    return False


def leverbaar(urls, check, bot_detectie, proxy):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15'
    }
    # amazon redirects indien geen browser-achtige user agent. Daarnaast is er een soort bot detectie ;-0
    # en verlopen requests via een proxy
    opvoorraad = False
    for url in urls.split(','):
        url.strip()
        try:
            retries = len(proxy.proxies)
            log_nr_of_retries = 0
            while retries > 0:
                s = requests.session()
                par = {"par":str(random.randint(0, 9))+str(random.randint(0, 9))+str(random.randint(0, 9))}
                r = s.get(url, headers=headers, params=par, proxies=proxy.get_random_proxy(), timeout=10)
                if r.status_code == 200:
                    if bot_detectie != "" and bot_detectie in r.text:
                        retries -= 1
                        log_nr_of_retries += 1
                    elif checks_on_page(check, r.text):
                        opvoorraad = False
                        retries = 0
                    else:
                        log(url)
                        log(r.text)
                        opvoorraad = True
                        retries = 0
                elif r.status_code == 404:
                    log(url)
                    log("404 status")
                    opvoorraad = False
                    retries = 0
                else:
                    log(url)
                    log(str(r.status_code))
                    opvoorraad = False
                    retries = 0
            if log_nr_of_retries != 0:
                log("botdetactie vermijding " + str(log_nr_of_retries) + " keer toegepast.")
            if opvoorraad:
                break
        except Exception as e:
            log(url + " " + str(e))
    return opvoorraad


def notify(message):
    secret = get_secrets()
    # telegram wil -100 voor chat_id indien een bot
    message = {'chat_id': "-100" + secret[TELEGRAM][CHANNEL_ID],
               'text': message}
    r = requests.post(BASE_URL + secret[TELEGRAM][TOKEN] + "/sendMessage", data=message)
    if r.status_code == 200:
        return True
    else:
        log(r.text)
        exit(1)


def same_message(naam):
    lastmessage_file = "lastmessage"
    if os.path.exists(lastmessage_file):
        if naam == "":
            os.remove(lastmessage_file)
        else:
            return True
    else:
        with open(lastmessage_file, 'w') as fp:
            pass
    return False


def main():
    config = get_config()
    now = datetime.datetime.now()
    if int(config[NOTIFY][NOTIFY_START_UUR]) <= now.hour < int(config[NOTIFY][NOTIFY_STOP_UUR]):
        winkel = get_winkels()
        genotificeerd = False
        winkels = ""
        proxy = Proxy(config[PROXY][PROXY_PROVIDER])
        for winkelnaam in winkel.sections():
            if winkels == "":
                winkels = winkelnaam
            else:
                winkels += ', ' + winkelnaam
            if BOT_DETECTIE in winkel[winkelnaam]:
                botdetectie = winkel[winkelnaam][BOT_DETECTIE]
            else:
                botdetectie = ""
            proxy.usedproxies = []
            if leverbaar(winkel[winkelnaam][URL], winkel[winkelnaam][VOORRAAD_TEKST], botdetectie, proxy):
                if not same_message(winkelnaam):
                    genotificeerd = notify(winkelnaam + '\n' + winkel[winkelnaam][URL])
            else:
                pass
                # log("niet leverbaar bij " + winkelnaam)
        if not genotificeerd:
            if now.minute == int(config[NOTIFY][NOTIFY_TEST_MINUTE]):
                same_message("")
                # Elk uur een notificatie om aan te tonen dat ie nog steeds draait en alles nog werkt.
                notify(winkels + '\nhebben de ps5 niet op voorraad.')
    else:
        log("No checking due to configured time window")


if __name__ == "__main__":
    log("start ps5 alerter")
    main()
    log("end ps5 alerter")
