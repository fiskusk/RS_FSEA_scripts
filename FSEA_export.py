# fiskusk 2023
# program for download exports from Rohde Schwarz FSEA
# using py -3.9

import unidecode
from termcolor import colored

from FSEA_modules import Analyzer

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


fsea = Analyzer('COM4')
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
