#!/usr/bin/env python

import sys
import csv
import tldextract
from parser import EmailParser

# initialize script
def init():
    # make sure that this script is not
    # being imported as a module
    if __name__ == "__main__":
        url = get_url_from_user()
        max_urls_to_visit = int(get_max_urls_to_visit_from_user())
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
        # Time
        print '\nScript timing:'
        print 'Start - ' + results["start_time"]
        print 'End - ' + results["end_time"]
        # Dump emails to CSV
        dump_to_csv(url, max_urls_to_visit, results["emails"])
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

def get_max_urls_to_visit_from_user():
    try:
        return sys.argv[2]
    except IndexError:
        print "Error: no argument passed for max urls to visit"
        sys.exit(1)
    except Exception as e:
        print "Error: unable to parse the max urls that was passed - " + str(e)

# print out what we found
def print_results(array):
    if len(array):
        for entry in array:
            print entry
    else:
        print 'None found'

def dump_to_csv(url, max_urls_to_visit, emails):
    writer = csv.writer(open('./emails/' + url + '-' + str(max_urls_to_visit) + "-emails.csv", 'w'))
    writer.writerow(list(emails))

init()
