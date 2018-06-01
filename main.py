#!/usr/bin/env python

import sys
import csv
from parser import EmailParser

# initialize script
def init():
    # make sure that this script is not
    # being imported as a module
    if __name__ == "__main__":
        url = get_url_from_user()
        max_urls_to_visit = 20
        results = EmailParser(url, max_urls_to_visit).init_search()
        # Emails
        print '\nFound these email addresses:'
        print_results(results["emails"])
        # Urls visited
        print '\nUrls visited:'
        print results["urls_visited"]
        # Urls found before stopping
        print '\nUrls found before stopping:'
        print results["urls_found_before_exiting"]
        print '\n'
        # Dump emails to CSV
        dump_to_csv(results["emails"])
    else:
        raise Exception('This script will be inactive if imported as a module.')

# fetch root domain from user input
def get_url_from_user():
    try:
        return sys.argv[1]
    except IndexError:
        print "Error: no argument passed for root domain"
        sys.exit(1)
    except Exception as e:
        print "Error: unable to parse the domain that was passed - " + str(e)

# print out what we found
def print_results(array):
    if len(array):
        for entry in array:
            print entry
    else:
        print 'None found'

def dump_to_csv(emails):
    writer = csv.writer(open("emails.csv", 'w'))
    writer.writerow(list(emails))

init()
