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
        while len(self.visited_urls) < self.MAX_URLS_TO_VISIT and count < len(self.urls_to_visit):
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
        url_contains_root_domain = self.ROOT_DOMAIN in tldextract.extract(url).domain or self.ROOT_DOMAIN in tldextract.extract(url).subdomain
        # url_contains_root_domain = True

        url_is_relative = self.is_a_relative_url(url)
        ignore_url = self.should_ignore_url(url)
        if (url_contains_root_domain or url_is_relative) and is_not_an_email and not ignore_url:
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
                email = email.replace('mailto:', '').strip().lower().replace('{', '').replace('}', '').replace('(', '').replace(')', '')
                if i == -1:
                    final_emails.add(email)
                else:
                    final_emails.add(email[:i+1])
            else:
                print 'Ignoring ' + email
        return final_emails

    def should_ignore_url(self, url):
        return (
          '.pdf' in url or
          '.ashx' in url or
          '.avi' in url or
          '.css' in url or
          '.doc' in url or
          '.docx' in url or
          '.exe' in url or
          '.gif' in url or
          '.jpg' in url or
          '.jpeg' in url or
          '.mid' in url or
          '.midi' in url or
          '.mp3' in url or
          '.mpg' in url or
          '.mpeg' in url or
          '.mov' in url or
          '.qt' in url or
          '.pdf' in url or
          '.png' in url or
          '.ram' in url or
          '.rar' in url or
          '.tiff' in url or
          '.wav' in url or
          '.zip' in url
        )

    def is_not_ignored_email(self, email):
        return (
            'sales' not in email and
            'hello' not in email and
            'support' not in email and
            'team' not in email and
            'privacy' not in email and
            'jobs' not in email and
            'careers' not in email and
            'security' not in email and
            'legal' not in email and
            'abuse' not in email and
            'press' not in email and
            'contact' not in email and
            'webmaster' not in email and
            'social' not in email and
            'billing' not in email and
            'seminars' not in email and
            'events' not in email and
            'tips' not in email and
            'letters' not in email and
            'accessibility' not in email and
            'research' not in email and
            'website' not in email and
            'investors' not in email and
            'subscription' not in email and
            'tour' not in email and
            'dev' not in email and
            'copywright' not in email and
            'copyright' not in email and
            'web' not in email and
            'production' not in email and
            'feedback' not in email and
            'corrections' not in email and
            'letters' not in email and
            'staff' not in email and
            '.gov' not in email and
            'regist' not in email and
            'request' not in email and
            'email' not in email and
            'invoice' not in email and
            'inquiry' not in email and
            'connect' not in email and
            '@media' not in email and
            'privacy' not in email and
            'help' not in email and
            'feedback' not in email and
            'admission' not in email and
            'coordinator' not in email and
            'consumer' not in email and
            'question' not in email and
            'customer' not in email and
            'media' not in email and
            'trademark' not in email and
            '@' in email and
            '.' in email and
            ' ' not in email and
            'reviews' not in email and
            'twitter' not in email and
            'help' not in email and
            'spam' not in email and
            'admin' not in email and
            'financ' not in email and
            'editor' not in email and
            'webkit' not in email and
            'test' not in email and
            'sales' not in email and
            'court' not in email and
            'service' not in email and
            'enforce' not in email and
            'student' not in email and
            'public' not in email and
            'reference' not in email and
            'director' not in email and
            'resource' not in email and
            'graduat' not in email and
            'info' not in email and
            'academic' not in email and
            'news' not in email and
            'educat' not in email and
            'counsel' not in email and
            'council' not in email and
            'dean' not in email and
            'android' not in email and
            'member' not in email and
            'conference' not in email and
            'partner' not in email and
            'comment' not in email and
            'donate' not in email and
            'section' not in email and
            'sport' not in email and
            'fraud' not in email and
            'history' not in email and
            'client' not in email and
            'hotel' not in email and
            'example' not in email and
            'communicat' not in email and
            'relations' not in email and
            'compliance' not in email and
            'optout' not in email and
            'mobile' not in email and
            'manage' not in email and
            'tickets' not in email and
            'advertising' not in email and
            'meeting' not in email and
            'sponsor' not in email and
            'account' not in email and
            'subscribe' not in email and
            'recruit' not in email and
            'reward' not in email and
            'trust' not in email and
            'retire' not in email and
            'certification' not in email and
            'train' not in email and
            'market' not in email and
            'volunteer' not in email and
            'gift' not in email and
            'design' not in email and
            'consent' not in email and
            'enquiries' not in email and
            'radio' not in email and
            'video' not in email and
            'data' not in email and
            'care' not in email
        )



