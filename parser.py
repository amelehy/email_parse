import requests
import tldextract
from bs4 import BeautifulSoup
from urlparse import urlparse
from urlparse import urljoin
from validate_email import validate_email
from time import gmtime, strftime

class EmailParser:

    visited_urls = {}
    urls_to_visit = list()
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
        start_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        self.discover_links_and_save_emails(self.INITIAL_URL)
        end_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        return {
            "emails": self.found_email_addresses,
            "urls_visited": len(self.visited_urls),
            "urls_found_before_exiting": len(self.urls_to_visit),
            "start_time": start_time,
            "end_time": end_time
        }

    def discover_links_and_save_emails(self, url):
        self.urls_to_visit.append(url)
        count = 0
        while len(self.visited_urls) < self.MAX_URLS_TO_VISIT and self.urls_to_visit[count]:
            url = self.urls_to_visit[count]
            if url not in self.visited_urls:
                # Log visiting url
                print '(' + str(len(self.visited_urls)) + ' / ' + str(self.MAX_URLS_TO_VISIT) + ')' + ' Visiting ' + url
                self.visited_urls[url] = 1
                # Fetch URL content
                response = self.init_request(url)
                if response['success']:
                    # Get HTML
                    soup = BeautifulSoup(response['payload'].text, 'html.parser')
                    # Find emails
                    self.found_email_addresses.update(self.parse_emails(soup))
                    # Get other links temp.
                    links_to_visit = self.fetch_all_links(soup)
                    for link in links_to_visit:
                        if link not in self.visited_urls:
                            self.urls_to_visit.append(link)
                else:
                    print 'Request to ' + url + ' failed because of: ' + str(response['payload'])
            # Increment counter
            count = count + 1
        return

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
        links = list()
        for link in html.select('a'):
            url = link.get('href') or ''
            valid_url = self.is_valid_url(url)
            if valid_url['valid']:
                links.append(valid_url['url'])
        return links

    # determine if the given url is valid
    # (1) url is not a "mailto" link
    # (2) the url contains the root domain as part of the domain or subdomain
    # (3) the url does not point to a PDF
    def is_valid_url(self, url):
        valid_url = {'valid': False, 'url': ''}
        is_not_an_email = urlparse(url).scheme != 'mailto'
        # url_contains_root_domain = self.url_contains_root_domain(url)
        url_contains_root_domain = True

        url_is_relative = self.is_a_relative_url(url)
        is_not_a_pdf = not url.endswith('.pdf')
        if (url_contains_root_domain or url_is_relative) and is_not_an_email and is_not_a_pdf:
            full = self.get_full_initial_url()
            valid_url['url'] = urljoin(full + '/', url)
            valid_url['valid'] = True
        return valid_url

    def url_contains_root_domain(url):
      return (
          self.ROOT_DOMAIN in tldextract.extract(url).domain or
          self.ROOT_DOMAIN in tldextract.extract(url).subdomain
      )

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
        # Find in anchor tags
        for link in html.select('a'):
            href = link.get('href') or ''
            url = urlparse(href)
            if url.scheme == 'mailto' and '.' in url.path and '@' in url.path:
                emails_found.update(self.parse_mailto(url.path))
        # Find in text
        for textSnippet in html.get_text().split(' '):
            if validate_email(textSnippet) is True and '.' in textSnippet and '@' in textSnippet:
                emails_found.update(self.parse_mailto(textSnippet))
        return emails_found

    # parse the email addressses from a "mailto" url
    def parse_mailto(self, email_string):
        final_emails = set()
        emails = email_string.split(',')
        for email in emails:
            i = email.find('?')
            if self.is_not_ignored_email(email):
                email = email.replace('mailto:', '').strip()
                if i == -1:
                    final_emails.add(email)
                else:
                    final_emails.add(email[:i+1])
            else:
                print 'Ignoring ' + email
        return final_emails

    def is_not_ignored_email(self, email):
        return (
            not email.startswith('info') and
            not email.startswith('sales') and
            not email.startswith('hello') and
            not email.startswith('support') and
            not email.startswith('team') and
            not email.startswith('privacy') and
            not email.startswith('jobs') and
            not email.startswith('careers') and
            not email.startswith('security') and
            not email.startswith('legal') and
            not email.startswith('abuse') and
            not email.startswith('press') and
            not email.startswith('contact') and
            not email.startswith('membership') and
            not email.startswith('webmaster') and
            not email.startswith('social') and
            not email.startswith('billing') and
            not email.startswith('seminars') and
            not email.startswith('events') and
            not email.startswith('tips') and
            not email.startswith('letters') and
            not email.startswith('accessibility') and
            not email.startswith('research') and
            not email.startswith('help') and
            not email.startswith('website') and
            not email.startswith('investors') and
            not email.startswith('subscription') and
            not email.startswith('tour') and
            not email.startswith('dev') and
            not email.startswith('copywright') and
            not email.startswith('web') and
            not email.startswith('production') and
            not email.startswith('feedback') and
            not email.startswith('media') and
            not email.startswith('corrections') and
            not email.startswith('letters') and
            not email.startswith('staff') and
            'request' not in email and
            'email' not in email and
            'invoice' not in email and
            'inquiry' not in email and
            'connect' not in email and
            '@media' not in email and
            'privacy' not in email and
            'help' not in email
        )



