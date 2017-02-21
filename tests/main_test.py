"""Test script for techcrunch crawler"""

import unittest.mock as mock
from bs4 import BeautifulSoup
import pytest

import company_reader.main as main



HTML_TITLE = 'taco_title'


class DotDict(dict):
    """
    a dictionary that supports dot notation
    as well as dictionary access notation
    usage: d = DotDict() or d = DotDict({'val1':'first'})
    set attributes: d.val2 = 'second' or d['val2'] = 'second'
    get attributes: d.val2 or d['val2']
    """
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


@pytest.fixture
def main_page():
    html = """<html>
    <a href="https://techcrunch.com/2016/08/05/unpacking-theranoss-magic-zika-detection-box/">
    </a>
    <a href="https://techcrunch.com/2016/08/05/unpacking-theranoss-magic-zika-detection-box/#comments">
    </a>
    <a href="https://techcrunch.com/unpacking-theranoss-magic-zika-detection-box/">
    </a></html>"""
    return html


@pytest.fixture
def valid_links():
    links = ['<a href="https://techcrunch.com/2016/08/05/unpacking-theranoss-magic-zika-detection-box/#comments"></a>',
             '<a href="https://techcrunch.com/2016/08/05/unpacking-theranoss-magic-zika-detection-box/">']
    return ''.join(links)


@pytest.fixture
def invalid_links():
    links = ['<a href="https://techcrunch.com/unpacking-theranoss-magic-zika-detection-box/"></a>',
             '<a href="https://marketing.com/adthing/tacotuesday/"></a>']
    return ''.join(links)


@pytest.fixture
def valid_company_cards():
    html = """<html>
    <ul>
    <li class="data-card {} active"
    {}="https://crunchbase.com/organization/space-exploration-technologies/">
        <h4 class="{} card-acc-handle">
            <a class="cb-card-title-link" href="https://crunchbase.com/organization/space/">spacex</a>
        </h4>
        <li>
            <strong class="key">Website</strong>
            <span class="value"><a href="https://www.spacex.com">https://www.spacex.com</a></span>
        </li>
    </li>
    <li class="data-card {} active"
    {}="https://crunchbase.com/organization/tesla/">
        <h4 class="{} card-acc-handle">
            <a class="cb-card-title-link" href="https://crunchbase.com/organization/tesla/">tesla</a>
        </h4>
        <li>
            <strong class="key">Website</strong>
            <span class="value"><a href="https://www.tesla.com">https://www.tesla.com</a></span>
        </li>
    </li>
    </ul></html>"""
    soup = BeautifulSoup(html.format(
        main.INDIVIDUAL_COMPANY_CARD_DIV,
        main.CRUNCHBASE_URL_DIV, main.COMPANY_NAME_DIV,
        main.INDIVIDUAL_COMPANY_CARD_DIV, main.CRUNCHBASE_URL_DIV,
        main.COMPANY_NAME_DIV), 'html.parser')
    return soup.find_all('li', class_=main.INDIVIDUAL_COMPANY_CARD_DIV)


@pytest.fixture
def invalid_company_cards():
    html = """<html>
    <ul>
    <li class="data-card crunchbase-card active"
    data-crunchbase-url="https://crunchbase.com/people/katherine-mcpheee/"></li>
    <li class="data-card crunchbase-card active"/>
    </ul></html>"""
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all('li')


@pytest.fixture
def child_page():
    html = """<html>
    <article>
    <header>
    <h1>{}</h1>
    </header>
    </article>
    <div class="{}">
        <ul>
            <li class="data-card {} active"
                {}="https://crunchbase.com/organization/space-exploration-technologies/">
                <h4 class="{} card-acc-handle">
                    <a class="cb-card-title-link" href="https://crunchbase.com/organization/space/">spacex</a>
                </h4>
                <li>
                    <strong class="key">Website</strong>
                    <span class="value"><a href="https://www.spacex.com">https://www.spacex.com</a></span>
                </li>
            </li>
        <li class="{}" {}="https://crunchbase.com/people/taco/"></li>
        </ul>
    </div>
    </html>"""
    return html.format(HTML_TITLE, main.SIDEBAR_COMPANY_DIV,
                       main.INDIVIDUAL_COMPANY_CARD_DIV,
                       main.CRUNCHBASE_URL_DIV, main.COMPANY_NAME_DIV,
                       main.INDIVIDUAL_COMPANY_CARD_DIV,
                       main.CRUNCHBASE_URL_DIV)


@pytest.fixture
def dirty_url():
    return ('https://techcrunch.com/2017/02/17/'
            'snap-takes-aim-a-facebook-in-roadshow-video/#comments')


@pytest.fixture
def clean_url():
    return ('https://techcrunch.com/2017/02/17/'
            'snap-takes-aim-a-facebook-in-roadshow-video/')


def test_is_viable_link(valid_links, invalid_links):
    soup = BeautifulSoup("<html>{}</html".format(valid_links), 'html.parser')
    valid_soup_links = soup.find_all('a')
    for link in valid_soup_links:
        assert main.is_viable_link(link)
    soup = BeautifulSoup("<html>{}</html".format(invalid_links), 'html.parser')
    invalid_soup_links = soup.find_all('a')
    for link in invalid_soup_links:
        assert not main.is_viable_link(link)


def test_is_company_card(valid_company_cards, invalid_company_cards):
    for card in valid_company_cards:
        assert main.is_company_card(card)
    for card in invalid_company_cards:
        assert not main.is_company_card(card)


def test_clean_url(dirty_url):
    cleaned_url = main.clean_url(dirty_url)
    assert cleaned_url == dirty_url[:-len('#comments')]
    assert len(cleaned_url) == len(dirty_url) - len('#comments')


def test_dedupe_urls(clean_url, dirty_url):
    urls = main.dedupe_urls([clean_url, dirty_url])
    assert len(urls) == 1
    assert urls.pop() == clean_url


def test_get_page_title(child_page):
    assert main.get_page_title(child_page) == HTML_TITLE


@mock.patch('requests.get')
def test_read_main_page(req, valid_links, invalid_links):
    req.return_value = DotDict({'text': (
        '<html>{}{}</html'.format(valid_links, invalid_links))})
    links = main.read_main_page(main.TECH_URL)
    assert len(links) == 2


def test_search_page_for_company_cards(child_page):
    cards = main.search_page_for_company_cards(child_page)
    assert len(cards) == 1


def test_get_company_name(valid_company_cards):
    name = main.get_company_name(valid_company_cards[0])
    assert name == 'spacex'
    name = main.get_company_name(valid_company_cards[1])
    assert name == 'tesla'


def test_raise_company_name_error(invalid_company_cards):
    try:
        main.get_company_name(invalid_company_cards[0])
        assert False
    except main.CompanyNameError:
        assert True


def test_get_company_url(valid_company_cards):
    url = main.get_company_url(valid_company_cards[0])
    assert url == 'https://www.spacex.com'


def test_raise_company_url_error(invalid_company_cards):
    try:
        main.get_company_url(invalid_company_cards[1])
        assert False
    except main.CompanyUrlError:
        assert True


def test_create_company_dict(valid_company_cards):
    url = 'https://techcrunch.com/2017/02/17/snap-takes-aim-a-facebook/'
    title = 'YOYOYOYO'
    company_dict = main.create_company_dict(url, title, valid_company_cards[0])
    assert company_dict[main.URL_KEY] == url
    assert company_dict[main.TITLE_KEY] == title
    assert company_dict[main.COMPANY_URL_KEY] == 'https://www.spacex.com'
    assert company_dict[main.COMPANY_NAME_KEY] == 'spacex'


def test_create_company_dict_none(valid_company_cards):
    url = 'https://techcrunch.com/2017/02/17/snap-takes-aim-a-facebook/'
    title = 'YOYOYOYO'
    company_dict = main.create_company_dict(url, title, None)
    assert company_dict[main.URL_KEY] == url
    assert company_dict[main.TITLE_KEY] == title
    assert company_dict[main.COMPANY_URL_KEY] == 'n/a'
    assert company_dict[main.COMPANY_NAME_KEY] == 'n/a'


def test_extract_companies_from_page(child_page):
    response = DotDict(
        {'text': child_page, 'url': 'https://techcrunch.com'})
    companies = main.extract_companies_from_page(response)
    assert len(companies) == 1
    company_dict = companies.pop()
    assert company_dict[main.URL_KEY] == 'https://techcrunch.com'
    assert company_dict[main.TITLE_KEY] == HTML_TITLE
    assert company_dict[main.COMPANY_URL_KEY] == 'https://www.spacex.com'
    assert company_dict[main.COMPANY_NAME_KEY] == 'spacex'


def test_extract_companies_from_page_none():
    html = """<html>
    <article>
    <header>
    <h1>{}</h1>
    </header>
    </article>""".format(HTML_TITLE)
    response = DotDict(
        {'text': html, 'url': 'https://techcrunch.com'})
    companies = main.extract_companies_from_page(response)
    assert len(companies) == 1
    company_dict = companies.pop()
    assert company_dict[main.URL_KEY] == 'https://techcrunch.com'
    assert company_dict[main.TITLE_KEY] == HTML_TITLE
    assert company_dict[main.COMPANY_URL_KEY] == 'n/a'
    assert company_dict[main.COMPANY_NAME_KEY] == 'n/a'


@mock.patch('grequests.imap')
def test_search_child_pages(rget, child_page):
    response = DotDict(
        {'text': child_page, 'url': 'https://techcrunch.com'})
    rget.return_value = iter([response])
    companies = main.search_child_pages(['asd'])
    company_dict = companies.pop()
    assert company_dict[main.URL_KEY] == 'https://techcrunch.com'
    assert company_dict[main.TITLE_KEY] == HTML_TITLE
    assert company_dict[main.COMPANY_URL_KEY] == 'https://www.spacex.com'
    assert company_dict[main.COMPANY_NAME_KEY] == 'spacex'
