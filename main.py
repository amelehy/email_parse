#!/usr/bin/env python

import sys
import requests
from bs4 import BeautifulSoup
from urlparse import urlparse

visited_urls = []

# initialize script
def init():
    # make sure that this script is not being imported as a module
    if __name__ == "__main__":
        try:
            root_domain = sys.argv[1]
            emails = init_link_discovery('http://' + root_domain)
            print_results(emails)
        except IndexError:
            print "Error: no argument passed for root domain"
            sys.exit(1)

def init_link_discovery(url):
    response = requests.get(url)
    domain_name = urlparse(response.url).netloc
    raw_html = response.text
    soup = BeautifulSoup(raw_html, 'html.parser')
    links_to_visit = fetch_all_links(soup, domain_name)
    for link in links_to_visit:
        if link not in visited_urls:
            print 'Visiting ' + link
            visited_urls.append(link)
            init_link_discovery(link)
    return parse_emails(soup) 

# fetch all links in the page that have the original 
# domain name in them or that start with '/'
def fetch_all_links(html, domain_name):
    array = []
    # get all urls that start with http and 
    # have the root domain name as a substring
    for link in html.select('a[href^=http]'):
        url = link.get('href')
        if domain_name in url:
            array.append(url)
    # get all urls that start with '/' 
    for link in html.select('a[href^=\\/]'):
        page = link.get('href')
        array.append('http://' + domain_name + page)
    return set(array)

# parse all emails from a webpage
def parse_emails(html):
    emails_found = []
    for element in html.select('a[href^=mailto]'):
        mailto_email = element['href']
        index_of_colon = mailto_email.find(':') + 1
        emails_found.append(mailto_email[index_of_colon:])
    return emails_found

# print out what we found
def print_results(array):
    print '\nFound these email addresses:'
    for entry in array:
        print entry

init()
