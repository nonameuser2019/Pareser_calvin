import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import random
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from model import *


db_engine = create_engine("sqlite:///calvin.db", echo=True)
basedir = os.path.abspath(os.path.dirname(__file__))
size_list = []
details_list = []
color_list = []
url_list = []
cat_url_list = []

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
            cat_url_list.append(line)
    return cat_url_list


def get_html(url):
    while True:
        time.sleep(random.randint(random.randint(6, 10), random.randint(12, 27)))
        html = requests.get(url, headers=HEADERS, proxies=proxy)
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


# def get_url(url):
#     browser = webdriver.Chrome()
#     browser.get(url)
#     url_block = browser.find_elements_by_class_name('productThumbnail.requested')
#     time.sleep(5)
#     for link in url_block:
#         url = link.get_attribute('href')
#         url_list.append(url)
#
#     browser.quit()
#     time.sleep(60)
#     return url_list

def parser_content(html):
    # порсит все данные из карточки кроме фото, подумать разбить на несколько функций
    soup = BeautifulSoup(html.text, 'html.parser')
    # имя товара
    product_name = soup.find('span', class_='productNameInner').text
    #базовая цена(без скидки)
    price = soup.find('div', id='price_display').find_all('span')[0].text[1:]
    try:
        # акционная цена
        price_sale = soup.find('div', id='price_display').find_all('span')[1].text[1:]
    except (IndexError, ValueError):
        price_sale = None
    try:
        # размер скидки в процентах
        discount = soup.find('div', class_='promoTagline promoMessage').find('div').text.split()[
            2]  # заменить регулярным выражением
    except:
        discount = None

    # доступные размеры, на сайте все доступные размеры имеют класс available, поэтому парсим только их
    try:
        block_size = soup.find('ul', id='sizes').find_all('li')
        for li in block_size:
            if li['class'] == ['available']:
                size_list.append(li.find('span').text)
                print(li.find('span').text)
    except:
        print(f'Size {None}')
    # маркированый список Details с доп инфой снизу карточки
    details_group = soup.find('ul', class_='bullets')
    for details in details_group.find_all('li'):
        details_list.append(details.text)
    # цветовая схема
    try:
        radiogrup = soup.find('ul', class_='productswatches')
        for color in radiogrup.find_all('li'):
            color_list.append(color['data-color-swatch'])
    except:
        color_list.append(None)
    print(product_name, price, price_sale, discount, size_list, color_list, details_list)
    count = 1
    Session = sessionmaker(bind=db_engine)
    session = Session()
    new_element = Calvin(product_name, price, price_sale, discount, ','.join(size_list), ','.join(color_list), count, ','.join(details_list))
    session.add(new_element)
    session.commit()
    count+=1
    size_list.clear()
    color_list.clear()
    details_list.clear()


def create_dir_name(cat_url):
    html = get_html(cat_url)
    dir_name = html.url[html.url.find('-') + 1:]
    try:
        os.mkdir(dir_name)
    except OSError:
        print('Папка существует')
    return dir_name


def get_photo(html, dir_name):
    photo_name = 0
    soup = BeautifulSoup(html.content, 'html.parser')
    image_url = soup.find('div', class_='product_main_image').find('img')['data-src']
    try:
        photo_name = random.randint(1, 100000)
        file_obj = requests.get(image_url, stream=True)
        with open(dir_name+'/'+str(photo_name)+'.JPG', 'bw') as photo:
            for chunk in file_obj.iter_content(8192):
                photo.write(chunk)
    except:
        print('Error file_obj')


def get_page_size(html):
    # парсим переменную payload
    soup = BeautifulSoup(html.content, 'html.parser')
    page_size = soup.find('span', class_='totalCount').text
    payload = {
        'pageSize': page_size
    }
    return payload


def get_url_category(cat_url, payload):
    # получаем список карточек всей подкатегории товара, для этого испоользуем параметр payload
    # без payload возвращает страницу с макс 30 товарами
    html = requests.get(cat_url, headers=HEADERS, proxies=proxy, params=payload)
    soup = BeautifulSoup(html.content, 'html.parser')
    total_count = soup.find('div', class_='grid').find_all('div', class_='productCell')
    for link in total_count:
        url = link.find('div', class_='productImage focusParent').find('a', class_='productThumbnail')['href']
        url_list.append(url)
    return url_list


def main():
    count = 1
    cat_url_list = read_file_url()
    for cat_url in cat_url_list:
        url_list = get_url_category(cat_url, get_page_size(get_html(cat_url)))
        dir_name = create_dir_name(cat_url)
        for url in url_list:
            html = get_html(url)
            get_photo(html, dir_name)
            parser_content(html)



if __name__ == '__main__':
    main()