#!/usr/bin/python3
# wykys 2017
# program for download the image screen from TEKTRONIX TDS 320
# using py -3.9

import time
import os
import unidecode
from termcolor import colored

from uart import UART

TRC_DIR = 'trc_spect'

def check_dir(name=''):
    if not os.path.exists(name):
        os.makedirs(name)


class Analyzer(object):
    def __init__(self, name=''):
        self.uart = UART(name, baudrate=19200, timeout=3)

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
    
    def get_trace_file(self):
        trace_complete = False
        trace_data = []
        previous_byte = None
        i = 0

        self.send_cmd('MMEM:DATA? \'C:\\USER\DATA\\trace.dat\'')

        print('Waiting for dates...')
        start_character = self.uart.read_byte()
        if (start_character == ord('#')):
            length_of_length = self.uart.read_byte()
            data_length = self.uart.read_bytes(int(chr(length_of_length)))
            data_length_int = int(''.join([chr(x) for x in data_length]))
        else:
            trace_complete = True
            trace_data = None
            print("Missing header for file length. Received: ")
            print(start_character)
        
        while (not trace_complete):
            byte = self.uart.read_byte()
            if byte == None: # serial timeout
                trace_complete = True
                trace_data = None
                print("\nSerial timeout occur")
            else:
                trace_data.append(byte)
                i += 1
                print('\rReceived{:71d} B of {:d} B'.format(i, data_length_int+2), end='')
                if data_length_int == i-2 and previous_byte == 0x0D and byte == 0x0A:
                    trace_complete = True
                    trace_data = trace_data[ : -4]
                    print('\nReceive Complete')
                elif data_length_int == i-2:
                    trace_complete = True
                    trace_data = None
                    print("\nCorrupted EOI end character")
                previous_byte = byte

            # check end file
            # if (byte == 0x0D):
            #     trace_complete = True

        return trace_data

    def make_header(self, freq_start, freq_stop, freq_span):
        header = []
        header += self.str_to_list("# Freq Start: ")
        header += freq_start
        header += self.str_to_list(" Hz\n")
        header += self.str_to_list("# Freq Stop: ")
        header += freq_stop
        header += self.str_to_list(" Hz\n")
        header += self.str_to_list("# Freq Span: ")
        header += freq_span
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

        title = input('Enter TITLE (max 60 characters) >>> ')
        while len(title) > 60:
             print(colored("Entered TITLE is to long - " + str(len(title)) + " (maximum is 60 characters)", 'red'))
             title = input('Enter TITLE >>> ')
        title = unidecode.unidecode(title)
        
        # freq_start = self.send_read('FREQ:STAR?')
        # freq_stop = self.send_read('FREQ:STOP?')
        # freq_span = self.send_read('FREQ:SPAN?')
        
        # data += self.make_header(freq_start, freq_stop, freq_span)
        # data += self.get_trace_data()

        self.send_cmd('FORM:DEXP:DSEParator POINt')
        self.send_cmd('FORM:DEXP:APPend OFF')
        self.send_cmd('FORM:DEXP:HEADer ON')
        self.send_cmd('MMEM:STOR:TRAC 1, \'C:\\USER\\DATA\\trace.dat\'')
        time.sleep(3)
        data += self.get_trace_file()
        
        check_dir(TRC_DIR)

        trc_url = TRC_DIR + '/'
        #trc_url += time.strftime('%Y-%m-%d_%H-%M-%S_', time.localtime())
        trc_url += title + '.dat'

        fw = open(trc_url, 'wb')
        fw.write(bytes(data))
        fw.close()
        print('Trace File Created!')

fsea = Analyzer('COM4')
fsea.read_trace_data()
