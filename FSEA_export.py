# fiskusk 2023
# program for download exports from Rohde Schwarz FSEA
# using py -3.9

import unidecode
from termcolor import colored

from FSEA_modules import Analyzer

fsea = Analyzer('COM4')

title = input('\nEnter TITLE (max 60 characters) >>> ')
while len(title) > 60:
		print(colored("Entered TITLE is to long - " + str(len(title)) + " (maximum is 60 characters)", 'red'))
		title = input('Enter TITLE >>> ')
title = unidecode.unidecode(title)

comment = input('Enter COMMENT (max 100 characters) >>> ')
while len(comment) > 100:
	print(colored("Entered COMMENT is to long - " + str(len(comment)) + " (maximum is 100 characters)", 'red'))
	comment = input('Enter COMMENT >>> ')

comment = unidecode.unidecode(comment)

fsea.get_postscript(title, comment)