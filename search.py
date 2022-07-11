import os
import argparse
import time
import random
from base64 import b64encode
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
import webbrowser
import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger('urllib3').setLevel(logging.ERROR)


def create_driver():
    options = webdriver.ChromeOptions()
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    # options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280x1696')
    # options.add_argument('--user-data-dir=/tmp/user-data')
    options.add_argument('--hide-scrollbars')
    # options.add_argument('--enable-logging')
    # options.add_argument('--log-level=0')
    # options.add_argument('--v=99')
    # options.add_argument('--single-process')
    # options.add_argument('--data-path=/tmp/data-path')
    options.add_argument('--ignore-certificate-errors')
    # options.add_argument('--homedir=/tmp')
    # options.add_argument('--disk-cache-dir=/tmp/cache-dir')
    options.add_argument(
        'user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')
    # options.binary_location = "/usr/bin/chromium-browser"

    driver = webdriver.Chrome(options=options)

    return driver


def get_url(date):
    code = b64encode(date.encode('utf-8')).decode('utf-8')
    # return f'https://www.google.com/travel/flights/search?tfs=CBwQAhouagwIAhIIL20vMGQ2bHASCjIw{code}DAgCEggvbS8wNndqZigAMgJVQXABggELCP___________wFAAUgBmAEC'
    return f'https://www.google.com/travel/flights/search?tfs=CBwQAhouagwIAhIIL20vMGQ2bHASCjIw{code}DAgCEggvbS8wNndqZigBMgJVQXABggELCP___________wFAAUgBmAEC'


def simplify_dna(dna):
    tokens = dna.split(' at ')
    tokens_dep = tokens[1].split(' and ')[0].split(', ')
    tokens_arr = tokens[3][:-1].split(' and ')[0].split(', ')
    return f"{tokens_dep[0].split(' on ')[0]}, {tokens_dep[1]} -> {tokens_arr[0].split(' on ')[0]}, {tokens_arr[1]}"


def filter_info_list(info_list):
    valid_info_list = []
    for info in info_list:
        tokens = info[1].split()
        hrs = int(tokens[0])
        if len(tokens) == 2:
            if hrs <= 15 and hrs > 13:
                valid_info_list.append(info)
        elif len(tokens) == 4:
            if hrs <= 15 and hrs >= 13:
                valid_info_list.append(info)
        else:
            logging.warning(f'malformatted duration string: {info[1]}')
    return valid_info_list


def get_info_list(url, driver=None, sleep=1):
    _driver = driver
    if _driver is None:
        _driver = create_driver()

    _driver.get(url)
    time.sleep(sleep)
    elem = _driver.find_element('xpath', '//*')
    source_code = elem.get_attribute("outerHTML")
    if driver is None:
        _driver.quit()

    soup = BeautifulSoup(source_code, 'html.parser')

    # Price
    prices = soup.find_all('div', class_='U3gSDe')
    price_list = []
    for price in prices:
        price_str = price.find_all(['span'], recursive=True)[0].get_text()
        _price = float(price_str.replace(',', '').strip('$'))
        price_list.append(_price)

    # Duration
    durations = soup.find_all('div', class_='Ak5kof')
    duration_list = []
    for duration in durations:
        duration_list.append(duration.find_all('div')[0].get_text())

    # Departure/Arrival time
    dnas = soup.find_all('span', class_='mv1WYe')
    dna_list = []
    for dna in dnas:
        dna_list.append(simplify_dna(dna['aria-label']))

    info_list = filter_info_list(
        list(zip(price_list, duration_list, dna_list)))

    return info_list


def play_alarm():
    os.system('afplay media/alarm.wav')


def open_booking_page():
    url_booking_ua = 'https://www.united.com/zh-hans/cn?gclsrc=aw.ds&gclid=Cj0KCQjwzqSWBhDPARIsAK38LY9hcgIUH0v1HiXOuAVlpVgMaAhlY6JtdeHlcVeukbwIkXL4Rno-EbIaAly1EALw_wcB'
    webbrowser.open(url_booking_ua, new=1)


def gen_date_list(start_date_str='220801', end_date_str='221031'):
    start_date = datetime.strptime(start_date_str, '%y%m%d').date()
    end_date = datetime.strptime(end_date_str, '%y%m%d').date()
    delta = end_date - start_date

    date_list = []
    for i in range(delta.days + 1):
        day = start_date + timedelta(days=i)
        if day.isoweekday() in [3, 5, 6, 7]:
            date_list.append(day.strftime('%y-%m-%dr'))

    return date_list


def search_once(driver, date_list, threshold=3000):
    for date in date_list:
        url = get_url(date)
        time.sleep(random.randint(0, 10) / 10)
        info_list = get_info_list(url, driver)
        if info_list:
            for info in info_list:
                logging.info(
                    f'{date[:-1]} | price: {info[0]} | duration: {info[1]} | dep/arr: {info[2]}')
                if info[0] < threshold:
                    print('\n' + '=' * 35 + f' {date[:-1]} ' + '=' * 35 + '\n')
                    open_booking_page()
                    while True:
                        driver.quit()  # terminate the driver here, wait for user response
                        play_alarm()
                        time.sleep(1)
        else:
            logging.warning(
                f'{date[:-1]} | price: Nan | duration: Nan | dep/arr: Nan')


def search(date_list, threshold=3000, repeat=None):
    driver = create_driver()

    if repeat is None:
        while True:
            search_once(driver, date_list, threshold)
            time.sleep(random.randint(0, 30))
    else:
        for i in range(repeat):
            search_once(driver, date_list, threshold)
            if i < repeat - 1:
                time.sleep(random.randint(0, 30))

    driver.quit()


def main():
    parser = argparse.ArgumentParser(description="UA856 Search")
    parser.add_argument('-s', '--start-date', default='220801',
                        help='start date for the search')
    parser.add_argument('-e', '--end-date', default='221031',
                        help='end date for the search')
    parser.add_argument('-p', '--price', type=int, default=3000,
                        help='price threshold for the search')
    parser.add_argument('-r', '--repeat', type=int, default=None,
                        help='how many times to repeat the search, the default behavior is to repeat forever')

    args = parser.parse_args()

    date_list = gen_date_list(args.start_date, args.end_date)
    search(date_list, args.price, args.repeat)


if __name__ == '__main__':
    main()
