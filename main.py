#!/usr/bin/env python

import sys
import requests
from bs4 import BeautifulSoup
from urlparse import urlparse

visited_urls = []
found_email_addresses = []
MAX_URLS_TO_VISIT = 50

# initialize script
def init():
    # make sure that this script is not being imported as a module
    if __name__ == "__main__":
        try:
            root_domain = sys.argv[1]
            init_link_discovery('http://' + root_domain)
            final_emails = flatten_and_dedupe(found_email_addresses)
            print_results(final_emails)
        except IndexError:
            print "Error: no argument passed for root domain"
            sys.exit(1)

# initialize link discovery to recursively determine
# what links we should visit from the current page
def init_link_discovery(url):
    response = requests.get(url)
    domain_name = urlparse(response.url).netloc
    raw_html = response.text
    soup = BeautifulSoup(raw_html, 'html.parser')
    links_to_visit = fetch_all_links(soup, domain_name)
    for link in links_to_visit:
        if link not in visited_urls and len(visited_urls) < MAX_URLS_TO_VISIT:
            print 'Visiting ' + link
            visited_urls.append(link)
            emails = init_link_discovery(link)
            if emails:
                found_email_addresses.append(emails)
    return parse_emails(soup) 

# fetch all relevant links in given page 
def fetch_all_links(html, domain_name):
    array = []
    # get all urls that start with 'http' and 
    # have the root domain name as a substring
    for link in html.select('a[href^=http]'):
        url = link.get('href')
        if domain_name in urlparse(url).netloc:
            array.append(url)
    # get all urls that start with '/' 
    for link in html.select('a[href^=\\/]'):
        page = link.get('href')
        # to account for situations like '//www.jana.com'
        if '.com' in page:
            array.append('http:' + page)
        else:
            array.append('http://' + domain_name + page)
    return set(array)

# parse all emails given the html from a webpage
def parse_emails(html):
    emails_found = []
    for element in html.select('a[href^=mailto]'):
        mailto_email = element['href']
        index_of_colon = mailto_email.find(':') + 1
        emails_found.append(mailto_email[index_of_colon:])
    return emails_found

# given an array flatten and dedupe it
def flatten_and_dedupe(emails):
    flattened = [val for sublist in emails for val in sublist]
    deduped = set(flattened)
    return deduped

# print out what we found
def print_results(array):
    print '\nFound these email addresses:'
    for entry in array:
        print entry

init()
