#!/usr/bin/python3
# wykys 2017
# program for download the image screen from TEKTRONIX TDS 320
# using py -3.9

import time
import os
import csv
import unidecode
from termcolor import colored

from uart import UART

IMG_DIR = 'img_spect'

def check_dir(name=''):
    if not os.path.exists(name):
        os.makedirs(name)


class Analyzer(object):
    def __init__(self, name=''):
        self.uart = UART(name, baudrate=19200)

    def send_cmd(self, cmd):
        if type(cmd) == str:
            for c in cmd:
                self.uart.send_byte(ord(c))
            self.uart.send_byte(10)  # LF
            print('Send command {}.'.format(cmd))

    def read_postscript(self):
        image_complete = False

        img = []
        i = 0

        # předělat na systém příkazů
        title = input('Enter TITLE (max 60 characters) >>> ')
        while len(title) > 60:
            print(colored("Entered TITLE is to long - " + str(len(title)) + " (maximum is 60 characters)", 'red'))
            title = input('Enter TITLE >>> ')

        title = unidecode.unidecode(title)
        
        comment = input('Enter COMMENT (max 100 characters) >>> ')
        while len(comment) > 100:
            print(colored("Entered COMMENT is to long - " + str(len(comment)) + " (maximum is 100 characters)", 'red'))
            comment = input('Enter COMMENT >>> ')

        comment = unidecode.unidecode(comment)

        self.send_cmd("HCOPy:ITEM:LABel:TEXT '" + title + "'")
        self.send_cmd("HCOP:ITEM:WIND1:TEXT '" + comment + "'")
        self.send_cmd('HCOPy')

        print('Waiting for dates...')

        while (not image_complete):
            byte = self.uart.read_byte()
            img.append(byte)
            i += 1

            print('\rReceive{:71d} B'.format(i), end='')

            # check end file
            if (byte == 0x04):
                image_complete = True

        print('\nReceive Complete')
        img.append(0x0d);
        img.append(0x0a);

        check_dir(IMG_DIR)

        img_url = IMG_DIR + '/'
        img_url += time.strftime('%Y-%m-%d_%H-%M-%S_', time.localtime())
        img_url += title + '.ps'

        fw = open(img_url, 'wb')
        fw.write(bytes(img))
        fw.close()
        print('Image created!')

    def read_value(self, data_url):
        read_complete = False

        value = []

        while (not read_complete):
            byte = self.read_byte()
            value.append(byte)

            # check end read
            if (byte == 10):
                read_complete = True
        s = ''.join(chr(i) for i in value)
        print('\nRead value is ', s)

        # TODO řešit jinde
        with open(data_url, "a") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow([s])

fsea = Analyzer('COM4')
fsea.read_postscript()
