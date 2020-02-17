import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import random
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from model import *
import json
import re

db_engine = create_engine("sqlite:///calvin.db", echo=True)
basedir = os.path.abspath(os.path.dirname(__file__))
size_list = []
details_list = []
color_list = []
url_list = []
cat_url_list = []
error_count = 0
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


engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)
session = Session()

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

def parser_content(html):
    # порсит все данные из карточки кроме фото, подумать разбить на несколько функций
    soup = BeautifulSoup(html.text, 'html.parser')
    link = html.url
    try:
        # имя товара
        product_name = soup.find('span', class_='productNameInner').text
    except:
        product_name = None

    try:
        # базовая цена(без скидки)
        price_span = soup.find('div', id='price_display').find_all('span')[0].text[1:]
        price = re.findall(r'\d*[.]\d+', price_span)[0]
    except:
        price = None
    try:
        # акционная цена
        price_sale_span = soup.find('div', id='price_display').find_all('span')[1].text[1:]
        price_sale = re.findall(r'\d*[.]\d+', price_sale_span)[0]
    except (IndexError, ValueError):
        price_sale = None
    try:
        if price_sale:
            discount = int(((float(price) - float(price_sale)) / float(price)) * 100)
        else:
            discount = None
    except:
        discount = None

    try:
        # цветовая схема доступных цветов с сайта
        radiogrup = soup.find('ul', class_='productswatches')
        for color in radiogrup.find_all('li'):
            color_list.append(color['data-color-swatch'])
    except:
        color_list.append('NoColor')


    try:
        # парсим 1 цвет
        color = soup.find('ul', class_='productswatches').find('li')['data-color-swatch']
    except:
        color = None
    try:
        # парсим все размеры
        size = soup.find('div', id='sizeJSON').text
        data = json.loads(size)
        size_list = data['colorToSize'][color]
    except(KeyError, AttributeError):
        try:
            size_list = data['waists'].sort()
        except:
            size_list = ['']


    try:
        # айди обьявления
        universal_id = soup.find('div', class_='universalStyleNumber').find_all('span')[1].text
    except:
        universal_id = None

    try:
        Session = sessionmaker(bind=db_engine)
        session = Session()
        new_element = CalvinPrice(product_name, price, price_sale, discount, ','.join(size_list), color,
                                  universal_id, ','.join(color_list), link)
        session.add(new_element)
        session.commit()
        size_list.clear()
        details_list.clear()
    except:
        global error_count
        error_count +=1


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
    # получаем список карточек всей подкатегории товара, для этого испоользуем параметр payload
    # без payload возвращает страницу с макс 30 товарами
    soup = BeautifulSoup(html.content, 'html.parser')
    try:
        total_count = soup.find('div', class_='grid').find_all('div', class_='productCell')
        for link in total_count:
            url = link.find('div', class_='productImage focusParent').find('a', class_='productThumbnail')['href']
            url_list.append(url)
    except:
        url_list.append(None)
    return url_list


def main():
    count = 1
    cat_url_list = read_file_url()
    for cat_url in cat_url_list:
        print(cat_url)
        html = get_html(cat_url)
        payload = get_page_size(html)
        print(payload)
        url_list = get_url_category(get_html(cat_url, payload))
    for url in url_list:
        card_exist = session.query(Calvin.url).filter(Calvin.url == url).count()
        if not card_exist:
            html = get_html(url)
            parser_content(html)
            print(f'Всего товаров для парсинга {len(url_list)} спарсили {count}')
            count +=1
        else:
            count += 1
            print('Этот товар есть в базе, пропускаем')
    print(f'Eror for parsing {error_count}')


if __name__ == '__main__':
    main()
