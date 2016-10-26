#!/usr/bin/env python

import requests
import re
import sys
from bs4 import BeautifulSoup

EMAILS = []

def parse_emails_recursive(domain):
  raw_html = requests.get(domain).text
  soup = BeautifulSoup(raw_html, 'html.parser')
  # parse all emails from the current page
  for el in soup.select('a[href^=mailto]'):
    email = el['href']
    index_of_colon = email.find(':') + 1
    EMAILS.append(email[index_of_colon:])
  # get all linked pages 
  # print(soup.find_all('a'))

# make sure that this script is not being imported as a module
if __name__ == "__main__":
  try:
    arg1 = sys.argv[1]
  except IndexError:
    print "Error: no argument passed for root domain"
    sys.exit(1)

  # parse emails from the webpage recursively
  parse_emails_recursive('http://' + arg1)
  # print all emails that we found
  for email in EMAILS:
    print(email)