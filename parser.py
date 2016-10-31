import requests
import tldextract
from bs4 import BeautifulSoup
from urlparse import urlparse
from urlparse import urljoin
from urllib import unquote

class EmailParser:

    visited_urls = []
    found_email_addresses = set()
    ROOT_DOMAIN = ''
    INITIAL_URL = ''
    MAX_URLS_TO_VISIT = 0

    def __init__(self, url, max_urls_to_visit):
        parsed_url = urlparse(url)
        self.INITIAL_URL = parsed_url.geturl() if parsed_url.scheme else 'http://' + parsed_url.geturl()
        self.ROOT_DOMAIN = tldextract.extract(self.INITIAL_URL).domain
        self.MAX_URLS_TO_VISIT = max_urls_to_visit

    # initialize the search for emails based on the 
    # initial url passed
    def init_search(self):
        self.init_link_discovery(self.INITIAL_URL)
        return self.found_email_addresses

    # initialize link discovery to recursively determine
    # what links we should visit from the current page
    def init_link_discovery(self, url):
        response = self.init_request(url)
        if response['success']:
            soup = BeautifulSoup(response['payload'].text, 'html.parser')
            links_to_visit = self.fetch_all_links(soup)
            for link in links_to_visit:
                if link not in self.visited_urls and len(self.visited_urls) < self.MAX_URLS_TO_VISIT:
                    print 'Visiting ' + link
                    self.visited_urls.append(link)
                    emails = self.init_link_discovery(link)
                    if emails:
                        self.found_email_addresses.update(emails)
            return self.parse_emails(soup) 
        else:
            print 'Request to ' + url + ' failed because of: ' + str(response['payload'])

    # make a request to the given url and return the response
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
    # (1) url is not a "mailto" link 
    # (2) the url contains the root domain as part of the domain or subdomain
    def fetch_all_links(self, html):
        links = set()
        for link in html.select('a'):
            url = link.get('href') or ''
            is_not_an_email = urlparse(url).scheme != 'mailto'
            url_contains_root_domain = (
                self.ROOT_DOMAIN in tldextract.extract(url).domain or 
                self.ROOT_DOMAIN in tldextract.extract(url).subdomain
            )
            if url_contains_root_domain and is_not_an_email:
                new_url = urljoin('http://' + self.ROOT_DOMAIN, url)
                links.add(new_url)
        return links

    # parse all emails given the html from a webpage
    def parse_emails(self, html):
        emails_found = set()
        for link in html.select('a'):
            href = link.get('href') or ''
            url = urlparse(href)
            if url.scheme == 'mailto':
                emails_found.update(self.parse_mailto(url.path))
        return emails_found

    # parse the email addressses from a "mailto" url
    def parse_mailto(self, email_string):
        final_emails = set()
        emails = email_string.split(',')
        for email in emails:
            i = email.find('?')
            if i == -1:
                final_emails.add(email)
            else:
                final_emails.add(email[:i+1])
        return final_emails