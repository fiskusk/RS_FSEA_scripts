# wykys 2018

import os
from sys import stdout, stderr

try:
    from colorama import Fore, Style, init
except ImportError:
    print ("Trying to Install required module: colorama\n")
    os.system('py -3.9 -m pip install colorama')
    # -- above lines try to install requests module if not present
    # -- if all went well, import required module again ( for global access)
from colorama import Fore, Style, init
init()

PROMPT = Fore.BLUE + Style.BRIGHT + '>>> ' + Style.RESET_ALL


def err(s=''):
    print(Fore.RED + Style.BRIGHT + 'Error: ' + s + Style.RESET_ALL, file=stderr)


def war(s=''):
    print(Fore.YELLOW + Style.BRIGHT + 'Warning: ' + s + Style.RESET_ALL, file=stderr)


def ok(s=''):
    print(Fore.GREEN + Style.BRIGHT + 'OK: ' + s + Style.RESET_ALL, file=stdout)


def stdo(s=''):
    print(Fore.WHITE + Style.BRIGHT + s + Style.RESET_ALL, file=stdout)


def rx(s='', prompt=True):
    print('\r' + Fore.LIGHTRED_EX + Style.BRIGHT + 'Rx: ' + Style.RESET_ALL + Fore.LIGHTRED_EX + s + Style.RESET_ALL, file=stdout, end='')
    if prompt:
        print('\n' + PROMPT, file=stdout, end='')


def tx(s=''):
    print(Fore.GREEN + Style.BRIGHT + 'Tx: ' + Style.RESET_ALL + Fore.GREEN + s + Style.RESET_ALL, file=stdout)
