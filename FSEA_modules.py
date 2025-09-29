#!/usr/bin/python3
# wykys 2017 and fiskusk 2023
# modules for download exports from Rohde Schwarz FSEA
# using py -3.9

import time
import os
import log

from uart import UART

try:
    import ghostscript
except ImportError:
    print ("Trying to Install required module: ghostscript\n")
    os.system('py -3.9 -m pip install ghostscript')
    # -- above lines try to install requests module if not present
    # -- if all went well, import required module again ( for global access)
import ghostscript

try:
    import pyvisa as visa
except ImportError:
    print ("Trying to Install required module: pyvisa\n")
    os.system('py -3.9 -m pip install pyvisa')
    # -- above lines try to install requests module if not present
    # -- if all went well, import required module again ( for global access)
import pyvisa as visa

try:
    import logging
except ImportError:
    print ("Trying to Install required module: logging\n")
    os.system('py -3.9 -m pip install logging')
    # -- above lines try to install requests module if not present
    # -- if all went well, import required module again ( for global access)
import logging

def ps_to_pdf(input_ps, output_pdf):
    args = [
        "ps2pdf",          # jen jméno programu, libovolné
        "-dBATCH",
        "-dNOPAUSE",
        "-sDEVICE=pdfwrite", # 24bit BMP
        f"-sOutputFile={output_pdf}",
        input_ps
    ]
    ghostscript.Ghostscript(*args)

def check_dir(name=''):
    if not os.path.exists(name):
        os.makedirs(name)

def create_file(data, dir='', title='', extension='.dat'):
    check_dir(dir)

    trc_url = dir + '/'
    fileName = time.strftime('%Y-%m-%d_%H-%M-%S_', time.localtime()) + title

    with open(trc_url + fileName + extension, 'wb') as fw:
        if isinstance(data, str):
            fw.write(data.encode('utf-8'))
        else:
            fw.write(bytearray(data))
    fw.close()

    print('File Created!')
    return fileName

class Analyzer(object):
    def __init__(self, connectionType='UART', name=''):
        self.connectionType = connectionType
        if type ==  'UART':
            self.uart = UART(name, baudrate=19200, timeout=10)
        else:
            self.rm = visa.ResourceManager()
            self.gpib = self.rm.open_resource(name, write_termination= '\n', read_termination='\n')
            #logging.basicConfig(level=logging.DEBUG)
            self.gpib.timeout = 10000
            self.gpib.chunk_size = 1024*1024

        analyzerIdentifier = self.send_read("*IDN?")
        if analyzerIdentifier == None:
            log.err('Analyzer did not respond to *IDN? in response time')
            exit(1)

        if type(analyzerIdentifier) == str:
            print("Connected to Analyzer: " + analyzerIdentifier)
            print("Instaled Options: " + self.send_read("*OPT?"))
        else:
            print("Connected to Analyzer: " + ''.join(chr(x) for x in analyzerIdentifier))
            print("Instaled Options: " + ''.join(chr(x) for x in self.send_read("*OPT?")))

    def send_cmd(self, cmd, printCommand = False):
        if type(cmd) == str:
            if self.connectionType == 'UART':
                for c in cmd:
                    self.uart.send_byte(ord(c))
                self.uart.send_byte(10)  # LF
            else:
                self.gpib.write(cmd)
                
            if printCommand == True:
                print('Send command {}.'.format(cmd))
    
    def send_read(self, cmd, printOutput = False):
        self.send_cmd(cmd, printOutput)
        received = False
        received_data = []
        if self.connectionType == 'UART':
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
                    
        else:
            received_data = self.gpib.read();
        if printOutput == True:
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

        print('Waiting for dates...')
        if self.connectionType == "UART":
            self.send_cmd('TRAC? ' + trace + ';*WAI')
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
        else:
            resp = self.send_read('TRAC? ' + trace + ';*WAI')
            if isinstance(resp, str):
                resp = list(resp.encode('ascii', 'ignore'))
            elif isinstance(resp, (bytes, bytearray)):
                resp = list(resp)
            trace_data += resp

        # --- FINÁLNÍ POJIŠTĚNÍ: převedeme vše na list[int] ---
        buf = bytearray()
        for x in trace_data:
            if isinstance(x, int):
                buf.append(x & 0xFF)
            elif isinstance(x, (bytes, bytearray)):
                buf.extend(x)
            elif isinstance(x, str):
                buf.extend(x.encode('ascii', 'ignore'))
            else:
                buf.extend(str(x).encode('ascii', 'ignore'))
        return list(buf)
    
    def getFile(self, command):
        trace_complete = False
        trace_data = []
        previous_byte = None
        i = 0

        print('Waiting for dates...')

        if self.connectionType == "UART":
            self.send_cmd(command);
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
        else:
            self.gpib.read_termination = None         # důležité u binárky
            trace_data = self.gpib.query_binary_values(
                command,   # SCPI dotaz, který vrací blok s hlavičkou #...
                datatype='B',               # 'B' = raw bajty (uint8)
                container=bytes,            # ať to vrátí rovnou jako bytes
                header_fmt='ieee',          # očekává SCPI/IEEE hlavičku
                expect_termination=True     # po datech čeká terminátor (většinou LF)
            )
            self.gpib.read_termination = '\n'         # revert

        return trace_data

    
    def get_trace_data(self, title, comment):
        if self.connectionType == "UART":
            if ''.join(chr(x) for x in self.send_read("DISP:TRAC1?")) == "1":
                create_file(self.get_dates_basic(comment, "TRACE1"), 'trc_spect', "TRC1; " + title)

            if ''.join(chr(x) for x in self.send_read("DISP:TRAC2?")) == "1":
                create_file(self.get_dates_basic(comment, "TRACE2"), 'trc_spect', "TRC2; " + title)

            if ''.join(chr(x) for x in self.send_read("DISP:TRAC3?")) == "1":
                create_file(self.get_dates_basic(comment, "TRACE3"), 'trc_spect', "TRC3; " + title)

            if ''.join(chr(x) for x in self.send_read("DISP:TRAC4?")) == "1":
                create_file(self.get_dates_basic(comment, "TRACE4"), 'trc_spect', "TRC4; " + title)
        else:
            if self.send_read("DISP:TRAC1?") == "1":
                create_file(self.get_dates_basic(comment, "TRACE1"), 'trc_spect', "TRC1; " + title)

            if self.send_read("DISP:TRAC2?") == "1":
                create_file(self.get_dates_basic(comment, "TRACE2"), 'trc_spect', "TRC2; " + title)

            if self.send_read("DISP:TRAC3?") == "1":
                create_file(self.get_dates_basic(comment, "TRACE3"), 'trc_spect', "TRC3; " + title)

            if self.send_read("DISP:TRAC4?") == "1":
                create_file(self.get_dates_basic(comment, "TRACE4"), 'trc_spect', "TRC4; " + title)
    
    def get_trace_file(self, title, comment):
        self.send_cmd('FORM:DEXP:DSEParator POINt')
        self.send_cmd('FORM:DEXP:APPend OFF')
        self.send_cmd('FORM:DEXP:HEADer ON')
        self.send_cmd("FORM:DEXP:COMM '" + comment + "'")

        if self.connectionType == "UART":
            if ''.join(chr(x) for x in self.send_read("DISP:TRAC1?")) == "1":
                self.send_cmd('MMEM:STOR:TRAC 1, \'C:\\USER\\DATA\\trace1.dat\'')
                time.sleep(3)
                create_file(self.getFile('MMEM:DATA? \'C:\\USER\\DATA\\trace1.dat\''), 'trc_spect', "TRC1; " + title)

            if ''.join(chr(x) for x in self.send_read("DISP:TRAC2?")) == "1":
                self.send_cmd('MMEM:STOR:TRAC 2, \'C:\\USER\\DATA\\trace2.dat\'')
                time.sleep(3)
                create_file(self.getFile('MMEM:DATA? \'C:\\USER\\DATA\\trace2.dat\''), 'trc_spect', "TRC2; " + title)

            if ''.join(chr(x) for x in self.send_read("DISP:TRAC3?")) == "1":
                self.send_cmd('MMEM:STOR:TRAC 3, \'C:\\USER\\DATA\\trace3.dat\'')
                time.sleep(3)
                create_file(self.getFile('MMEM:DATA? \'C:\\USER\\DATA\\trace3.dat\''), 'trc_spect', "TRC3; " + title)

            if ''.join(chr(x) for x in self.send_read("DISP:TRAC4?")) == "1":
                self.send_cmd('MMEM:STOR:TRAC 4, \'C:\\USER\\DATA\\trace4.dat\'')
                time.sleep(3)
                create_file(self.getFile('MMEM:DATA? \'C:\\USER\\DATA\\trace4.dat\''), 'trc_spect', "TRC4; " + title)
        else:
            if self.send_read("DISP:TRAC1?") == "1":
                self.send_cmd('MMEM:STOR:TRAC 1, \'C:\\USER\\DATA\\trace1.dat\';*WAI')
                create_file(self.getFile('MMEM:DATA? \'C:\\USER\\DATA\\trace1.dat\''), 'trc_spect', "TRC1; " + title)

            if self.send_read("DISP:TRAC2?") == "1":
                self.send_cmd('MMEM:STOR:TRAC 2, \'C:\\USER\\DATA\\trace2.dat\';*WAI')
                create_file(self.getFile('MMEM:DATA? \'C:\\USER\\DATA\\trace2.dat\''), 'trc_spect', "TRC2; " + title)

            if self.send_read("DISP:TRAC3?") == "1":
                self.send_cmd('MMEM:STOR:TRAC 3, \'C:\\USER\\DATA\\trace3.dat\';*WAI')
                create_file(self.getFile('MMEM:DATA? \'C:\\USER\\DATA\\trace3.dat\''), 'trc_spect', "TRC3; " + title)

            if self.send_read("DISP:TRAC4?") == "1":
                self.send_cmd('MMEM:STOR:TRAC 4, \'C:\\USER\\DATA\\trace4.dat\';*WAI')
                create_file(self.getFile('MMEM:DATA? \'C:\\USER\\DATA\\trace4.dat\''), 'trc_spect', "TRC4; " + title)

    def get_postscript(self, title, comment):
        image_complete = False
        buffer = []
        i = 0
        
        self.send_cmd("HCOPy:ITEM:LABel:TEXT '" + title + "'")
        self.send_cmd("HCOP:ITEM:WIND1:TEXT '" + comment + "'")

        if self.connectionType == 'GPIB':
            self.send_cmd("HCOPy:GRID ON")
            self.send_cmd("HCOPy:DEV:LANG2 POST")
            self.send_cmd("HCOPy:DEST2 'MMEM'")
            self.send_cmd("MMEM:NAME 'C:\\USER\\data\\image.ps'")
            self.send_cmd('HCOPy:IMM2;*WAI')
        else:
            self.send_cmd('HCOPy:IMM1')


        print('Waiting for dates...')

        if self.connectionType == 'UART':
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
        else:
            buffer = self.getFile("MMEM:DATA? 'C:\\USER\\data\\image.ps'")

        print('\nReceive Complete')
        dir = 'img_spect'
        extension = '.ps'
        fileName = create_file(buffer, dir, title, extension)

        ps_to_pdf(dir + '/' + fileName + extension, dir + '/' + fileName + ".pdf")
