import requests
import configparser
import os

BASE_URL = "https://api.telegram.org/bot"
BOL_COM_PS5_URL = 'https://www.bol.com/nl/p/sony-playstation-5-console/9300000004162282'
CONFIG_FILE = 'resource/secrets.txt'
TELEGRAM = 'telegram'
CHANNEL_ID = 'channel_id'
TOKEN = 'TOKEN'


def get_config():
    config = configparser.ConfigParser()
    if os.path.isfile(CONFIG_FILE):
        config.read(CONFIG_FILE)
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


def leverbaar():
    r = requests.get(BOL_COM_PS5_URL)
    if r.status_code == 200:
        if 'Niet leverbaar' in r.text:
            return False
    return True


def main():
    if not leverbaar():
        config = get_config()
        message = {'chat_id': "-100" + config[TELEGRAM][CHANNEL_ID],
                   'text': 'bol.com\n'
                           'https://www.bol.com/nl/p/sony-playstation-5-console/9300000004162282'}
        r = requests.post(BASE_URL + config[TELEGRAM][TOKEN] + "/sendMessage", data=message)
        if r.status_code != 200:
            print(r.text)
            exit(1)
    else:
        print("niet leverbaar")


if __name__ == "__main__":
    main()
