"""Main script to read companies from techcrunch main page"""

# Some Ideas to improve this script:
# Use some nlp software to calculate subject or main subjects. 
# (We can use scikit-learn for simple bag of words to start).

import argparse
from bs4 import BeautifulSoup
import csv
import datetime
import grequests
import logging
import re
import requests


# Regexs.
VIABLE_LINK_REGEX = (
    '.+techcrunch\.com\/\d{4}\/(0[0-9]|1[1-2])\/([0-2][0-9]|3[0-1])\/.+')
ORGANIZATION_REGEX = '.+\/organization\/.+'
CLEAN_URL_REGEX = '^(.+)(\/)[^\/]+$'

# Techcrunch html parsing keywords.
TECH_URL = 'http://www.techcrunch.com'
PAGE_TITLE = 'article'
HTML_PARSER = 'html.parser'
UNKNOWN_COMPANY_NAME = 'n/a'
UNKNOWN_COMPANY_URL = 'n/a'
HREF = 'href'
SIDEBAR_COMPANY_DIV = 'crunchbase-cluster'
INDIVIDUAL_COMPANY_CARD_DIV = 'crunchbase-card'
CRUNCHBASE_URL_DIV = 'data-crunchbase-url'
COMPANY_NAME_DIV = 'card-title'
COMPANY_URL_DIV = 'Website'

# Final dictionary keywords.
URL_KEY = 'url'
TITLE_KEY = 'title'
COMPANY_NAME_KEY = 'company_name'
COMPANY_URL_KEY = 'company_url'

# Valid Regex's to check.
valid_re = re.compile(VIABLE_LINK_REGEX)
organization_re = re.compile(ORGANIZATION_REGEX)
clean_url_re = re.compile(CLEAN_URL_REGEX)

# Setup logging.
LOG_FORMAT = '%(asctime)s-%(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger('clearmob')


class CompanyUrlError(Exception): 
    def __init__(self,*args, **kwargs):
        super(Exception, self).__init__(*args, **kwargs)


class CompanyNameError(Exception): 
    def __init__(self,*args, **kwargs):
        super(Exception, self).__init__(*args, **kwargs)


def exception_handler(request, exception):
    """Handle exceptions"""
    logger.error("Request {} failed".format(request.url))


def is_viable_link(link):
    """Ensure a link is correct"""
    href = link.get(HREF)
    if not href:
        return None
    if valid_re.match(href):
        return True
    return False


def is_company_card(card):
    """Checks if company card is valid"""
    website = card.get(CRUNCHBASE_URL_DIV)
    if website:
        return True if organization_re.match(website) else False
    return False


def clean_url(url):
    """Return URL without data after final slash

    Note: This method is meant to clean all arguments after slash
    I.e. ?mobile=True or #comments. If we would like to search all url's,
    simply comment out this method call."""
    match = clean_url_re.match(url)
    if match:
        return ''.join(match.group(1,2))
    return url


def dedupe_urls(valid_links):
    """Return only unique urls"""
    url_set = set([])
    for link in valid_links:
        url_set.add(clean_url(link))
    return list(url_set)


def get_page_title(response_text):
    """Extract page title from page"""
    soup = BeautifulSoup(response_text, HTML_PARSER)
    article = soup.find(PAGE_TITLE)
    return article.header.h1.text


def read_main_page(url):
    """Read only main page for valid links"""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, HTML_PARSER)
    links = soup.find_all('a')
    return [link.get(HREF) for link in links if is_viable_link(link)]


def search_page_for_company_cards(text):
    """Search page for any valid company cards"""
    soup = BeautifulSoup(text, HTML_PARSER)
    company_div = soup.find(class_=SIDEBAR_COMPANY_DIV)
    if company_div:
        cards = company_div.find_all('li', class_=INDIVIDUAL_COMPANY_CARD_DIV)
        return [card for card in cards if is_company_card(card)]
    return []


def get_company_name(company_card):
    try:
        title_h = company_card.find(class_=COMPANY_NAME_DIV)
        return title_h.a.text.strip()
    except AttributeError as e:
        raise CompanyNameError(e)


def get_company_url(company_card):
    """Returns company url for a particular company card"""
    try:
        for li in company_card.find_all('li'):
            if li.find_all(text=COMPANY_URL_DIV):
                return li.a.text
        raise CompanyUrlError(None)
    except AttributeError as e:
        raise CompanyUrlError(e)


def create_company_dict(url, title, company_card=None):
    """Create a company dictionary for a url, title, and company"""
    company_name, company_url = (None, None)
    try:
        company_name = get_company_name(company_card)
    except CompanyNameError:
        company_name = UNKNOWN_COMPANY_NAME
    try:
        company_url = get_company_url(company_card)
    except CompanyUrlError:
        company_url = UNKNOWN_COMPANY_URL
    return {URL_KEY : url,
            TITLE_KEY : title, COMPANY_NAME_KEY : company_name,
            COMPANY_URL_KEY : company_url}


def extract_companies_from_page(response):
    """Extract all companies from a single get response"""
    title = get_page_title(response.text)
    company_list = []
    companies = search_page_for_company_cards(response.text)
    if not companies:
        return [create_company_dict(response.url, title, company_card=None)]
    for company in companies:
        company_list.append(create_company_dict(response.url, title, company))
    return company_list


def search_child_pages(cleaned_links):
    """Search each page of passed in list of links

    Args:
        cleaned_links: list of links to search
    
    Returns:
        A list of dictionaries with url, title, company_name,
        and company_title as attributes.
    """
    data = [grequests.get(link) for link in cleaned_links]
    responses = grequests.imap(data, size=20)
    final_list = []
    logging.info("Searching descendant pages")
    counter = 0
    for response in responses:
        counter += 1
        if counter % 5 == 0:
            logging.info("Parsing descendant page {}-{}".format(
                counter-4, counter))
        final_list.extend(extract_companies_from_page(response))
    return final_list


def write_file(filename, rs):
    """Write csv file of recordset"""
    keys = [URL_KEY, TITLE_KEY, COMPANY_NAME_KEY, COMPANY_URL_KEY]
    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys)
        writer.writeheader()
        for item in rs:
            writer.writerow(item)
    return None


def parse_command_line_filename():
    """Return filename from command line"""
    parser = argparse.ArgumentParser(
        description="""Read TechCrunch website and output company info to a
        csv file path passed in""")
    parser.add_argument('filename', help='file path to csv output')
    args = parser.parse_args()
    return args.filename

if __name__ == "__main__":
    filename = parse_command_line_filename()
    viable_links = read_main_page(TECH_URL)
    cleaned_links = dedupe_urls(viable_links)
    company_list = search_child_pages(cleaned_links)
    write_file(filename, sorted(company_list, key=lambda a: a['url']))
