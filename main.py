#!/usr/bin/env python

import sys
from parser import EmailParser

# initialize script
def init():
    # make sure that this script is not
    # being imported as a module
    if __name__ == "__main__":
        params = get_user_params()
        emails = EmailParser(params['url'], params['max_urls_to_visit']).init_search()
        print_results(emails)
    else:
        raise Exception('This script will be inactive if imported as a module.')

# fetch root domain from user input
def get_user_params():
    try:
        params = { "url": sys.argv[1], "max_urls_to_visit": sys.argv[2] }
        return params
    except IndexError:
        print "Error: no argument passed for root domain"
        sys.exit(1)
    except Exception as e:
        print "Error: unable to parse the domain that was passed - " + str(e)

# print out what we found
def print_results(array):
    print '\nFound these email addresses:'
    if len(array):
        for entry in array:
            print entry
    else:
        print 'None found'

init()
