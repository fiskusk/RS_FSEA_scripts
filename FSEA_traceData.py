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

TRC_DIR = 'trc_spect'

def check_dir(name=''):
    if not os.path.exists(name):
        os.makedirs(name)


class Analyzer(object):
    def __init__(self, name=''):
        self.uart = UART(name, baudrate=19200)

    def get_trace_data(self):
        trace_complete = False
        trace_data = []
        i = 0

        self.send_cmd('TRAC? TRACE1')

        print('Waiting for dates...')

        while (not trace_complete):
            byte = self.uart.read_byte()
            # check end file
            if (byte == 0x0A):
                trace_complete = True

            if byte == ord(','):
                byte = ord('\n')
            trace_data.append(byte)
            i += 1
            print('\rReceived{:71d} B'.format(i), end='')


        print('\nReceive Complete')
        return trace_data

    def make_header(self):
        header = []
        header += self.str_to_list("# Freq Start: ")
        header += self.send_read('FREQ:STAR?')
        header += self.str_to_list(" Hz\n")
        header += self.str_to_list("# Freq Stop: ")
        header += self.send_read('FREQ:STOP?')
        header += self.str_to_list(" Hz\n")
        header += self.str_to_list("# Freq Span: ")
        header += self.send_read('FREQ:SPAN?')
        header += self.str_to_list(" Hz\n\n")

        return header

    def str_to_list(self, str):
        data = []
        for c in str:
            data.append(ord(c))
        return data

    def send_cmd(self, cmd):
        if type(cmd) == str:
            for c in cmd:
                self.uart.send_byte(ord(c))
            self.uart.send_byte(10)  # LF
            print('Send command {}'.format(cmd))
    
    def send_read(self, cmd):
        self.send_cmd(cmd)
        received = False
        received_data = []
        while (not received):
            byte = self.uart.read_byte()
            if (byte != 0x0A) and (byte != 0x0D):
                received_data.append(byte)

            # check end
            if (byte == 0x0A):
                received = True

        return received_data

    def read_trace_data(self):
        data = []

        # předělat na systém příkazů
        title = input('Enter TITLE (max 60 characters) >>> ')
        while len(title) > 60:
             print(colored("Entered TITLE is to long - " + str(len(title)) + " (maximum is 60 characters)", 'red'))
             title = input('Enter TITLE >>> ')
        title = unidecode.unidecode(title)
        
        data += self.make_header()
        data += self.get_trace_data()
        
        check_dir(TRC_DIR)

        trc_url = TRC_DIR + '/'
        #trc_url += time.strftime('%Y-%m-%d_%H-%M-%S_', time.localtime())
        trc_url += title + '.dat'

        fw = open(trc_url, 'wb')
        fw.write(bytes(data))
        fw.close()
        print('Image created!')

fsea = Analyzer('COM4')
fsea.read_trace_data()
