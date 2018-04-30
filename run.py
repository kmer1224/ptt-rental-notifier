import configparser
import re
from datetime import datetime

from requests_html import HTMLSession
from slackclient import SlackClient

BASE_URL = 'https://www.ptt.cc/'
RENTAL_URLS = [BASE_URL + 'bbs/Rent_apart/index.html',
               BASE_URL + 'bbs/Rent_tao/index.html']

DATETIME_FORMAT = "%c"
REGEX_PATTERN = r"\[無\/(台北|新北)\/.+?\].*"

config = configparser.ConfigParser()
config.read('config.cfg')

slack_token = config.get('SLACK', 'token')
sc = SlackClient(slack_token)

session = HTMLSession()


def get_post_datetime(html):
    meta = html.find('.article-meta-value')
    datetime_string = meta[3].text
    datetime_object = datetime.strptime(datetime_string, DATETIME_FORMAT)

    return datetime_object


def get_matched_urls(html):
    urls = []

    rows = html.find('.title')
    for row in rows:
        url = row.find('a', first=True)
        if url:
            result = re.match(REGEX_PATTERN, url.text)
            if result:
                urls.append(BASE_URL + url.attrs['href'])

    return urls


def push_notification(url):
    sc.api_call(
        "chat.postMessage",
        channel="#rental",
        text=url
    )


def update_previous_record(previous_record):
    previous_record = previous_record.strftime(DATETIME_FORMAT)
    config.set('RECORD', 'previous', previous_record)
    with open('config.cfg', 'w') as configfile:
        config.write(configfile)


def main():
    previous_record = config.get('RECORD', 'previous')
    previous_record = datetime.strptime(previous_record, DATETIME_FORMAT)

    matched_urls = []

    for url in RENTAL_URLS:
        res = session.get(url)
        urls = get_matched_urls(res.html)
        matched_urls.extend(urls)

    for url in matched_urls:
        res = session.get(url)
        post_datetime = get_post_datetime(res.html)
        if previous_record <= post_datetime:
            push_notification(url)
            previous_record = post_datetime

    update_previous_record(previous_record)


if __name__ == '__main__':
    main()