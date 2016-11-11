import requests
import tldextract
from bs4 import BeautifulSoup
from urlparse import urlparse
from urlparse import urljoin

class EmailParser:

    visited_urls = {}
    found_email_addresses = set()
    ROOT_DOMAIN = ''
    ROOT_DOMAIN_SUBDOMAIN = ''
    ROOT_DOMAIN_SUFFIX = ''
    ROOT_DOMAIN_SCHEME = ''
    INITIAL_URL = ''
    MAX_URLS_TO_VISIT = 0

    def __init__(self, url, max_urls_to_visit):
        parsed_url = urlparse(url)
        self.INITIAL_URL = parsed_url.geturl() if parsed_url.scheme else 'http://' + parsed_url.geturl()
        self.ROOT_DOMAIN = tldextract.extract(self.INITIAL_URL).domain
        self.ROOT_DOMAIN_SUBDOMAIN = tldextract.extract(self.INITIAL_URL).subdomain
        self.ROOT_DOMAIN_SUFFIX = tldextract.extract(self.INITIAL_URL).suffix
        self.ROOT_DOMAIN_SCHEME = urlparse(self.INITIAL_URL).scheme
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
                    self.visited_urls[link] = 1
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
    def fetch_all_links(self, html):
        links = set()
        for link in html.select('a'):
            url = link.get('href') or ''
            valid_url = self.is_valid_url(url)
            if valid_url['valid']:
                links.add(valid_url['url'])
        return links

    # determine if the given url is valid
    # (1) url is not a "mailto" link
    # (2) the url contains the root domain as part of the domain or subdomain
    def is_valid_url(self, url):
        valid_url = {'valid': False, 'url': ''}
        is_not_an_email = urlparse(url).scheme != 'mailto'
        url_contains_root_domain = (
            self.ROOT_DOMAIN in tldextract.extract(url).domain or
            self.ROOT_DOMAIN in tldextract.extract(url).subdomain
        )
        url_is_relative = self.is_a_relative_url(url)
        if (url_contains_root_domain or url_is_relative) and is_not_an_email:
            full = self.get_full_initial_url()
            valid_url['url'] = urljoin(full + '/', url)
            valid_url['valid'] = True
        return valid_url

    # build full initial url from parsed pieces
    def get_full_initial_url(self):
        subdomain = self.ROOT_DOMAIN_SUBDOMAIN + '.' if self.ROOT_DOMAIN_SUBDOMAIN else ''
        return (
            self.ROOT_DOMAIN_SCHEME + '://' +
            subdomain +
            self.ROOT_DOMAIN + '.' +
            self.ROOT_DOMAIN_SUFFIX
        )

    # determine if the given url is a relative url
    def is_a_relative_url(self, url):
        parsed = tldextract.extract(url)
        return not parsed.subdomain and not parsed.domain and not parsed.suffix

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
