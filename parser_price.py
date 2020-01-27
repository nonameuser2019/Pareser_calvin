import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import random
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from model import *

basedir = os.path.abspath(os.path.dirname(__file__))
db_engine = create_engine("sqlite:///calvin.db", echo=True)
proxy = {'HTTPS': '163.172.182.164:3128'}
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'calvin.db')
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:71.0) Gecko/20100101 Firefox/71.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Host': 'www.calvinklein.us',
    'Referer': 'https://www.calvinklein.us/en/womens-plus',
    'TE': 'Trailers',
    'Upgrade-Insecure-Requests': '1'

}
cat_url_list = []


def read_file_url():
    with open('input.txt', 'r') as file:
        for line in file:
            cat_url_list.append(line.strip('\n'))
    return cat_url_list


def get_html(url, payload=None):
    while True:
        time.sleep(random.randint(random.randint(6, 10), random.randint(12, 27)))
        html = requests.get(url, headers=HEADERS, proxies=proxy, params=payload)
        if html.status_code == 200:
            print(html.status_code)
            return html
        elif html.status_code == 403:
            print(html.status_code)
            print('weit to 600 sec')
            time.sleep(random.randint(600,800))
        else:
            time.sleep(random.randint(14, 27))
            print(html.status_code)
            continue


def get_page_size(html):
    try:
        # парсим переменную payload
        soup = BeautifulSoup(html.content, 'html.parser')
        page_size = soup.find('span', class_='totalCount').text
        print(f'Page sizes : {page_size}')
        payload = {
            'pageSize': page_size
        }

    except:
        payload = 60

    return payload


def get_url_category(html):
    soup = BeautifulSoup(html.content, 'html.parser')
    total_count = soup.find('div', class_='grid').find_all('div', class_='productCell')
    for link in total_count:
        url = link.find('div', class_='productImage focusParent').find('a', class_='productThumbnail')['href']
        try:
            full_price = link.find('div', id='price_display').find_all('span')[0].text[1:]
        except:
            full_price = None
        try:
            discount_price = link.find('div', id='price_display').find_all('span')[1].text[1:]
        except:
            discount_price = None
        try:
            discount = link.find('div', class_='promoMessage discount').find('span').text.strip().split()[2]
        except:
            discount = None
        Session = sessionmaker(bind=db_engine)
        session = Session()
        new_element = CalvinPrice(full_price, discount_price, discount, url)
        session.add(new_element)
        session.commit()





def main():
    cat_url_list = read_file_url()
    for cat_url in cat_url_list:
        html = get_html(cat_url)
        payload = get_page_size(html)
        get_url_category(get_html(cat_url, payload))


if __name__ == '__main__':
    main()