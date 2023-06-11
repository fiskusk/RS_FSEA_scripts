# fiskusk 2023
# program for download exports from Rohde Schwarz FSEA
# using py -3.9

# import unidecode
# from termcolor import colored
# import configparser
import os
import sys
import atexit

def exit_handler():
    input("Press Enter To Exit...")

atexit.register(exit_handler)

try:
    import tests as main_test
except SyntaxError:
    version_info = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    string = f"You're executing the script with Python {version_info}. Execute the script with Python 3.9"
    print(string)
    exit()

main_test.version_check()

try:
    import unidecode
except ImportError:
    print ("Trying to Install required module: unidecode\n")
    os.system('py -3.9 -m pip install unidecode')
    # -- above lines try to install requests module if not present
    # -- if all went well, import required module again ( for global access)
import unidecode

try:
    from termcolor import colored
except ImportError:
    print ("Trying to Install required module: termcolor\n")
    os.system('py -3.9 -m pip install termcolor')
    # -- above lines try to install requests module if not present
    # -- if all went well, import required module again ( for global access)
from termcolor import colored

# https://docs.python.org/3/library/configparser.html
try:
    import configparser
except ImportError:
    print ("Trying to Install required module: configparser\n")
    os.system('py -3.9 -m pip install configparser')
    # -- above lines try to install requests module if not present
    # -- if all went well, import required module again ( for global access)
import configparser

from FSEA_modules import Analyzer

# def install(package):
#     subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def get_title():
    title = input('\nEnter TITLE (max 60 characters) >>> ')
    while len(title) > 60:
            print(colored("Entered TITLE is to long - " + str(len(title)) + " (maximum is 60 characters)", 'red'))
            title = input('Enter TITLE >>> ')
    return unidecode.unidecode(title)

def get_comment():
    comment = input('Enter COMMENT (max 100 characters) >>> ')
    while len(comment) > 100:
        print(colored("Entered COMMENT is to long - " + str(len(comment)) + " (maximum is 100 characters)", 'red'))
        comment = input('Enter COMMENT >>> ')
    return unidecode.unidecode(comment)

def print_menu():
    print("\nWhat kind of output do you want:")
    print("1 - Postscript")
    print("2 - Trace Data File")
    print("3 - Basic Trace Data")
    print("12 - Postscript + Trace Data File")
    print("13 - Postscript + Basic Trace Data")
    print("23 - Trace Data File + Basic Trace Data")
    print("123 - All outputs (Postscript + Trace Data File + Basic Trace Data")

    while True:
        try:
            selector = int(input('\nEnter Menu Number >>> '))
            if selector == 1 or selector == 2 or selector == 3 or \
               selector == 12 or selector == 13 or selector == 23 or \
               selector == 123:
                break
            else:
                print("That's not a valid option!")
        except:
            print("That's not a valid option!")

    return selector

if len(sys.argv) == 1:
    serialPort = 'COM4'
elif len(sys.argv) == 2:
    serialPort = sys.argv[1]
fsea = Analyzer(serialPort)

run = True
while (run == True) :
	selector = print_menu()
	title = get_title()
	comment = get_comment()

	if selector == 1:
		fsea.get_postscript(title, comment)
	elif selector == 2:
		fsea.get_trace_file(title, comment)
	elif selector == 3:
		fsea.get_trace_data(title, comment)
	elif selector == 12:
		fsea.get_postscript(title, comment)
		fsea.get_trace_file(title, comment)
	elif selector == 13:
		fsea.get_postscript(title, comment)
		fsea.get_trace_data(title, comment)
	elif selector == 23:
		fsea.get_trace_file(title, comment)
		fsea.get_trace_data(title, comment)
	elif selector == 123:
		fsea.get_postscript(title, comment)
		fsea.get_trace_file(title, comment)
		fsea.get_trace_data(title, comment)
	else:
		print("Bad Input")

	while True:
		try:
			cont = input("Do you wish continue? (Y/N) >>> ")
			if cont == "Y" or cont == "N" or cont == "y" or cont == "n":
				break
			else:
				print("That's not a valid option!")
		except:
			print("That's not a valid option!")
			
	if cont == "N" or cont == "n" :
		run = False
