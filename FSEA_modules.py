#!/usr/bin/python3
# wykys 2017 and fiskusk 2023
# modules for download exports from Rohde Schwarz FSEA
# using py -3.9

import time
import os
import log

from uart import UART

def check_dir(name=''):
    if not os.path.exists(name):
        os.makedirs(name)

def create_file(data, dir='', title='', extension='.dat'):
    check_dir(dir)

    trc_url = dir + '/'
    trc_url += time.strftime('%Y-%m-%d_%H-%M-%S_', time.localtime())
    trc_url += title + extension

    fw = open(trc_url, 'wb')
    fw.write(bytes(data))
    fw.close()
    print('File Created!')

class Analyzer(object):
    def __init__(self, name=''):
        self.uart = UART(name, baudrate=19200, timeout=10)
        analyzerIdentifier = self.send_read("*IDN?")
        if analyzerIdentifier == None:
            log.err('Analyzer did not respond to *IDN? in response time')
            exit(1)
        print("Connected to Analyzer: " + ''.join(chr(x) for x in analyzerIdentifier))
        print("Instaled Options: " + ''.join(chr(x) for x in self.send_read("*OPT?")))

    def send_cmd(self, cmd):
        if type(cmd) == str:
            for c in cmd:
                self.uart.send_byte(ord(c))
            self.uart.send_byte(10)  # LF
            print('Send command {}.'.format(cmd))
    
    def send_read(self, cmd, print_output = False):
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
            if (byte == None):
                received = True
                received_data = None
        if print_output == True:
            print('Received {}.'.format(''.join(chr(x) for x in received_data)))
            print('Received {}.'.format(received_data))
        return received_data
    
    def str_to_list(self, str):
        data = []
        for c in str:
            data.append(ord(c))
        return data
    
    def make_header(self, comment, trace, freq_start, freq_stop, freq_span):
        header = []
        header += self.str_to_list("# Comment: " + comment + "\n")
        header += self.str_to_list("# " + trace + "\n")
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
    
    def get_dates_basic(self, comment, trace):
        trace_complete = False
        trace_data = []
        i = 0

        freq_start = self.send_read('FREQ:STAR?')
        freq_stop = self.send_read('FREQ:STOP?')
        freq_span = self.send_read('FREQ:SPAN?')
        
        trace_data += self.make_header(comment, trace, freq_start, freq_stop, freq_span)

        self.send_cmd('TRAC? ' + trace)

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
        print('\nReceived Complete')
        return trace_data
    
    def get_dates(self):
        trace_complete = False
        trace_data = []
        previous_byte = None
        i = 0

        print('Waiting for dates...')
        start_character = self.uart.read_byte()
        # check header with length of desiref file
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
        return trace_data
    
    def get_trace_data(self, title, comment):
        if ''.join(chr(x) for x in self.send_read("DISP:TRAC1?")) == "1":
            create_file(self.get_dates_basic(comment, "TRACE1"), 'trc_spect', "TRC1; " + title)

        if ''.join(chr(x) for x in self.send_read("DISP:TRAC2?")) == "1":
            create_file(self.get_dates_basic(comment, "TRACE2"), 'trc_spect', "TRC2; " + title)

        if ''.join(chr(x) for x in self.send_read("DISP:TRAC3?")) == "1":
            create_file(self.get_dates_basic(comment, "TRACE3"), 'trc_spect', "TRC3; " + title)

        if ''.join(chr(x) for x in self.send_read("DISP:TRAC4?")) == "1":
            create_file(self.get_dates_basic(comment, "TRACE4"), 'trc_spect', "TRC4; " + title)
    
    def get_trace_file(self, title, comment):
        self.send_cmd('FORM:DEXP:DSEParator POINt')
        self.send_cmd('FORM:DEXP:APPend OFF')
        self.send_cmd('FORM:DEXP:HEADer ON')
        self.send_cmd("FORM:DEXP:COMM '" + comment + "'")

        if ''.join(chr(x) for x in self.send_read("DISP:TRAC1?")) == "1":
            self.send_cmd('MMEM:STOR:TRAC 1, \'C:\\USER\\DATA\\trace1.dat\'')
            time.sleep(3)
            self.send_cmd('MMEM:DATA? \'C:\\USER\\DATA\\trace1.dat\'')
            create_file(self.get_dates(), 'trc_spect', "TRC1; " + title)

        if ''.join(chr(x) for x in self.send_read("DISP:TRAC2?")) == "1":
            self.send_cmd('MMEM:STOR:TRAC 2, \'C:\\USER\\DATA\\trace2.dat\'')
            time.sleep(3)
            self.send_cmd('MMEM:DATA? \'C:\\USER\\DATA\\trace2.dat\'')
            create_file(self.get_dates(), 'trc_spect', "TRC2; " + title)

        if ''.join(chr(x) for x in self.send_read("DISP:TRAC3?")) == "1":
            self.send_cmd('MMEM:STOR:TRAC 3, \'C:\\USER\\DATA\\trace3.dat\'')
            time.sleep(3)
            self.send_cmd('MMEM:DATA? \'C:\\USER\\DATA\\trace3.dat\'')
            create_file(self.get_dates(), 'trc_spect', "TRC3; " + title)

        if ''.join(chr(x) for x in self.send_read("DISP:TRAC4?")) == "1":
            self.send_cmd('MMEM:STOR:TRAC 4, \'C:\\USER\\DATA\\trace4.dat\'')
            time.sleep(3)
            self.send_cmd('MMEM:DATA? \'C:\\USER\\DATA\\trace4.dat\'')
            create_file(self.get_dates(), 'trc_spect', "TRC4; " + title)

    def get_postscript(self, title, comment):
        image_complete = False
        buffer = []
        i = 0

        # Some configuration part. Commented for speeding up communication
        #self.send_cmd("HCOP:ABOR")
        # self.send_cmd("HCOP:DEV:LANG2 POST")
        # time.sleep(0.5)
        # self.send_cmd("HCOP:DEV:LANG1 POST")
        # time.sleep(0.5)
        # self.send_cmd("HCOP:DEST1 'SYST:COMM:SER1'")
        # self.send_cmd("HCOP:DEST2 'MMEM'")
        # self.send_cmd("HCOP:DEV:COL ON")
        # self.send_cmd("HCOP:DEV:PRES2 ON")
        
        self.send_cmd("HCOPy:ITEM:LABel:TEXT '" + title + "'")
        self.send_cmd("HCOP:ITEM:WIND1:TEXT '" + comment + "'")
        self.send_cmd('HCOPy')

        #time.sleep(10)
        #self.send_cmd("MMEM:NAME 'spool.ps'")
        #self.send_cmd('MMEM:DATA? \'C:\\USER\\spool.ps\'')

        print('Waiting for dates...')
        # This part is for get stored file in memory. Section commented because it took 
        # a long time. Firt it must store whole file into disk and then it will be
        # posible to download from instrument. Some complex screen layout took more
        # than 10sec for storing and file was tranfered corrupted. This is why this section
        # of code is commented and for postscript is used clasic HARDCOPY command
        # to direct send to SERIAL interface.

        #previous_byte = None
        # start_character = self.uart.read_byte()
        # # check header with length of desiref file
        # if (start_character == ord('#')): 
        #     length_of_length = self.uart.read_byte()
        #     data_length = self.uart.read_bytes(int(chr(length_of_length)))
        #     data_length_int = int(''.join([chr(x) for x in data_length]))
        # else:
        #     image_complete = True
        #     buffer = None
        #     print("Missing header for file length. Received: ")
        #     print(start_character)
        
        # while (not image_complete):
        #     byte = self.uart.read_byte()
        #     if byte == None: # serial timeout
        #         image_complete = True
        #         buffer = None
        #     else:
        #         buffer.append(byte)
        #         i += 1
        #         print('\rReceived{:71d} B of {:d} B'.format(i, data_length_int+2), end='')
        #         if data_length_int == i-2 and previous_byte == 0x0D and byte == 0x0A:
        #             image_complete = True
        #             buffer = buffer[ : -2]
        #             print('\nReceived Complete')
        #         elif data_length_int == i-2:
        #             image_complete = True
        #             buffer = None
        #             print("\nCorrupted EOI end character")
        #         previous_byte = byte
        # create_file(buffer, 'img_spect', title, '.ps')

        while (not image_complete):
            byte = self.uart.read_byte()
            if (byte == None):
                return
            buffer.append(byte)
            i += 1

            print('\rReceive{:71d} B'.format(i), end='')

            # check end file
            if (byte == 0x04):
                byte = self.uart.read_byte()
                byte = self.uart.read_byte()
                image_complete = True

        print('\nReceive Complete')
        create_file(buffer, 'img_spect', title, '.ps')
