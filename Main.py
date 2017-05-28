import requests
from asciimatics.screen import Screen
import time
from datetime import datetime
import winsound
import json

__VERSION__ = "1705.0.5"

#---------------------------------------------------------------
# DATA
#---------------------------------------------------------------

# JSON file loader
def load_file_json(file_name):
	with open(file_name, 'r') as _file:
		content = _file.read()
		content_dict = json.loads(content)
		return content_dict

# Config files
data_file = "NanoSniffer.conf"
config = load_file_json(data_file)

# Settings
_address = str(config["address"])
__MONEY = str(config["currency"])

# BASE_URLs

_baseURL_GENERAL = "https://api.nanopool.org/v1/%s/user/" % __MONEY.lower()
_baseURL_REPORTEDHASH = "https://api.nanopool.org/v1/%s/reportedhashrate/" % __MONEY.lower()
_baseURL_OTHER = "https://api.nanopool.org/v1/%s/approximated_earnings/" % __MONEY.lower()
_cryptonatorAPI = "https://api.cryptonator.com/api/ticker/" #$money$-usd/btc-usd

# User-Agent
_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1"}

# INFOS dicts

__miner_infos = dict(balance="0", old_balance="0", hashrate="0", old_hashrate="0", lastReportedHash="0", averageHashrate6H="0", USDmonth="0", USDday="0")
__money_ticker = {"%s_usd" % __MONEY.lower() : 1}


def __get_infos():
    # Declarations des globales
    global __miner_infos

    # General Infos
    req = requests.get(_baseURL_GENERAL + _address, headers=_headers)
    _JSON = req.json()

    # Modification des globales
    __miner_infos["balance"] = _JSON["data"]["balance"]
    __miner_infos["old_hashrate"] = __miner_infos["hashrate"]
    __miner_infos["hashrate"] = _JSON["data"]["hashrate"]
    __miner_infos["averageHashrate6H"] = _JSON["data"]["avgHashrate"]["h6"]

    # General Infos
    req = requests.get(_baseURL_REPORTEDHASH + _address, headers=_headers)
    _JSON = req.json()

    # Modification des globales
    __miner_infos["lastReportedHash"] = _JSON["data"]

    # General Infos
    req = requests.get(_baseURL_OTHER + __miner_infos["averageHashrate6H"], headers=_headers)
    _JSON = req.json()

    # Modification des globales
    __miner_infos["USDmonth"] = _JSON["data"]["month"]["dollars"]
    __miner_infos["USDday"] = _JSON["data"]["day"]["dollars"]

    # Cours des monnaies
    req = requests.get(_cryptonatorAPI + "%s-usd" % __MONEY, headers=_headers)
    _JSON = req.json()

    # Modification des globales
    __money_ticker["%s_usd" % __MONEY.lower()] = _JSON["ticker"]["price"]


    return


def getfuckingnormaltime(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def update(screen):
    _seconds = 0
    _refreshLimit = 0
    _history = []
    _beep = False

    screen.print_at(("Nanopool JSON Sniffer      -          %s Pool          -      v " % __MONEY) + __VERSION__, 2, 1, Screen.COLOUR_YELLOW, Screen.A_BOLD)
    screen.print_at("Address : " + _address, 3, 3, Screen.COLOUR_CYAN)
    screen.print_at("Press Q to exit()", 3, 24, Screen.COLOUR_WHITE)
    screen.print_at("Press R - Force refresh()", 45, 25, Screen.COLOUR_WHITE)

    screen.print_at("Reward history :", 4, 10, Screen.COLOUR_WHITE, Screen.A_BOLD)
    screen.print_at("Estimated USD", 4, 18, Screen.COLOUR_WHITE, Screen.A_BOLD)
    screen.print_at("Day : ", 20, 18, Screen.COLOUR_WHITE, Screen.A_BOLD)
    screen.print_at("Month : ", 30, 18, Screen.COLOUR_WHITE, Screen.A_BOLD)
    screen.print_at("Based on 6hrs Avg. Hashrate : ", 45, 18, Screen.COLOUR_WHITE, Screen.A_BOLD)

    screen.print_at("%s Price :" % __MONEY, 45, 10, Screen.COLOUR_WHITE, Screen.A_BOLD)
    screen.print_at("Balance Est.", 60, 10, Screen.COLOUR_WHITE, Screen.A_BOLD)

    screen.print_at("Last reported hashrate : ", 3, 7, Screen.COLOUR_WHITE)
    screen.print_at("Hashrate : ", 3, 6, Screen.COLOUR_WHITE)
    screen.print_at("Balance : ", 3, 5, Screen.COLOUR_WHITE, Screen.A_BOLD)

    while True:

        if _beep:
            screen.print_at("Press B - Reward beep() : ON", 45, 24, Screen.COLOUR_WHITE)
        else:
            screen.print_at("Press B - Reward beep() : OFF ", 45, 24, Screen.COLOUR_WHITE)

        if _seconds != 0:
            screen.print_at("update in : " + "%d" % (_seconds - 1) + " ", 60, 3)
            _seconds = _seconds - 1

            # Réinitialise le compteur de Force Refresh
            # et efface le texte "disabled until...."
            if _seconds == 0:
                _refreshLimit = 0
                screen.print_at("                             ", 45, 26)

        else:
            # Ré-initialisation des variables (round end)
            _seconds = 29

            screen.print_at("fetching data()...", 3, 25, Screen.COLOUR_YELLOW)
            screen.refresh()

            __get_infos()

            # affiche la différence (si balance ++)
            if __miner_infos["old_balance"] != "0":
                # si aucune augmentation depuis la dernière maj, on affiche rien
                if float(__miner_infos["balance"]) - float(__miner_infos["old_balance"]) == 0:
                    screen.print_at("                   ", 50, 5, Screen.COLOUR_WHITE)
                else:
                    # sinon on affiche la différence
                    screen.print_at("+" + str(
                        round(float(__miner_infos["balance"]) - float(__miner_infos["old_balance"]),
                              8)) + " " + __MONEY, 50, 5, Screen.COLOUR_MAGENTA)
                    _history.insert(0, str(round(float(__miner_infos["balance"]) - float(__miner_infos["old_balance"]),
                                              8)) + " @ " + '{:%Y-%m-%d %H:%M}'.format(datetime.now())+"    ")
                    _history = _history[-5:]
                    __miner_infos["old_balance"] = __miner_infos["balance"]

                    if _beep:
                        winsound.Beep(550, 950)

            else:
                # La valeur de base doit être initialisée, si old_balance = 0
                __miner_infos["old_balance"] = __miner_infos["balance"]

            screen.print_at(__miner_infos["balance"] + " " + __MONEY, 30, 5, Screen.COLOUR_YELLOW)
            screen.print_at(str(int(float(__miner_infos["hashrate"]))) + " Mh/s         ", 30, 6, Screen.COLOUR_YELLOW)
            screen.print_at(str(int(float(__miner_infos["lastReportedHash"]))) + " Mh/s           ", 30, 7,
                            Screen.COLOUR_YELLOW)

            # Estimation des gains sur 1 jour en USD
            screen.print_at(str(int(float(__miner_infos["USDday"]))) + " USD     ", 20, 19, Screen.COLOUR_CYAN)

            # Estimation des gains sur 1 mois en USD
            screen.print_at(str(int(float(__miner_infos["USDmonth"]))) + " USD     ", 30, 19, Screen.COLOUR_CYAN)

            # Average Hashrate / 6h
            screen.print_at(str(int(float(__miner_infos["averageHashrate6H"]))) + " Mh/s     ", 45, 19, Screen.COLOUR_CYAN)

            # Currency price in USD
            screen.print_at(str(round(float(__money_ticker["%s_usd" % __MONEY.lower()]),2))+" USD        ", 45, 11, Screen.COLOUR_RED)
            
            # Balance estimation in USD
            screen.print_at("~ " + str(round(float(__money_ticker["%s_usd" % __MONEY.lower()]) * float(__miner_infos["balance"]), 4)) + " USD   ", 60, 11, Screen.COLOUR_RED)

            for i in range(len(_history)):
                # Lignes de l'historique
                screen.print_at("+" + _history[i], 5, 11 + i, Screen.COLOUR_GREEN)

            screen.print_at("update in : " + str(_seconds), 60, 3)

        screen.refresh()
        screen.print_at("                  ", 3, 25)

        time.sleep(1)

        ev = screen.get_key()
        if ev in (ord('Q'), ord('q')):
            return
        else:
            if ev in (ord('B'), ord('b')):
                if _beep:
                    screen.print_at("Press B - Reward beep() : OFF", 45, 24, Screen.COLOUR_WHITE)
                    _beep = False
                else:
                    screen.print_at("Press B - Reward beep() : ON ", 45, 24, Screen.COLOUR_WHITE)
                    _beep = True
            else:
                if ev in (ord('R'), ord('r')):
                    # Si, et seulement SI, moins de 3 refresh en 30 secondes
                    if _refreshLimit < 2:
                        _seconds = 0
                        _refreshLimit = _refreshLimit + 1
                    else:
                        screen.print_at("∟ disabled until next round()", 45, 26, Screen.COLOUR_RED)

        screen.refresh()


Screen.wrapper(update)
