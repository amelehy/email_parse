#!/usr/bin/env python

import sys
import requests
import tldextract
from bs4 import BeautifulSoup
from urlparse import urlparse
from urlparse import urljoin

class EmailParser:

    visited_urls = []
    found_email_addresses = []
    root_domain = ''
    initial_url = ''
    MAX_URLS_TO_VISIT = 50

    def __init__(self, url):
        parsed_url = urlparse(url)
        self.initial_url = parsed_url.geturl() if parsed_url.scheme else 'http://' + parsed_url.geturl()
        self.root_domain = tldextract.extract(self.initial_url).domain

    def init_search(self):
        self.init_link_discovery(self.initial_url)
        final_emails = self.flatten_and_dedupe(self.found_email_addresses)
        return final_emails

    # initialize link discovery to recursively determine
    # what links we should visit from the current page
    def init_link_discovery(self, url):
        response = self.init_request(url)
        if response['success']:   
            payload = response['payload']
            raw_html = payload.text
            soup = BeautifulSoup(raw_html, 'html.parser')
            links_to_visit = self.fetch_all_links(soup)
            for link in links_to_visit:
                if link not in self.visited_urls and len(self.visited_urls) < self.MAX_URLS_TO_VISIT:
                    print 'Visiting ' + link
                    self.visited_urls.append(link)
                    emails = self.init_link_discovery(link)
                    if emails:
                        self.found_email_addresses.append(emails)
            return self.parse_emails(soup) 
        else:
            print 'Request to ' + url + ' failed because of: ' + str(response['payload'])

    def init_request(self, url):
        response = {'success': False, 'payload': ''}
        try:
            response['payload'] = requests.get(url)
            response['success'] = True
        except requests.exceptions.Timeout as e:
            response['payload'] = e
        except requests.exceptions.TooManyRedirects as e:
            response['payload'] = e
        except requests.exceptions.RequestException as e:
            response['payload'] = e
        return response

    # fetch all relevant links in given page 
    def fetch_all_links(self, html):
        links = set()
        for link in html.select('a'):
            url = link.get('href') or ''
            if self.root_domain in urlparse(url).netloc:
                new_url = urljoin('http://' + self.root_domain, url)
                links.add(new_url)
        return links

    # parse all emails given the html from a webpage
    def parse_emails(self, html):
        emails_found = []
        for element in html.select('a[href^=mailto]'):
            mailto_email = element['href']
            index_of_colon = mailto_email.find(':') + 1
            emails_found.append(mailto_email[index_of_colon:])
        return emails_found

    # given an array flatten and dedupe it
    def flatten_and_dedupe(self, emails):
        flattened = [val for sublist in emails for val in sublist]
        deduped = set(flattened)
        return deduped


# initialize script
def init():
    # make sure that this script is not
    # being imported as a module
    if __name__ == "__main__":
        url = get_url_from_user()
        emails = EmailParser(url).init_search()
        print_results(emails)
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
    print '\nFound these email addresses:'
    for entry in array:
        print entry
        break
    else:
        print 'None found'

init()
