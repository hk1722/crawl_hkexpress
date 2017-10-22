# -*- coding:utf-8 -*-
import json
import re
import requests
from config import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from datetime import datetime
import time
import pymongo
# import sys,os,io
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='gb18030')
chrome_options = webdriver.ChromeOptions()
driver = webdriver.Chrome()
driver.maximize_window()
wait = WebDriverWait(driver,10)

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

def get_first_page():
    driver.get('https://booking.hkexpress.com/zh-CN/Search')
    driver.find_element_by_css_selector(
        '#search_flight > div > div:nth-child(1) > div > div > label.r_oneway > input[type="radio"]').click()
    m = driver.find_element_by_id('newsearch_from_select').click()
    n = driver.find_element_by_link_text('香港 (HKG)').click()
    time.sleep(2)
    o = driver.find_element_by_link_text('东京成田 (NRT)').click()
    p = driver.find_element_by_css_selector(
        '#search_flight > div > div.row.calendar_con > div:nth-child(1) > div > div > img').click()
    r = driver.find_element_by_css_selector(
        '#ui-datepicker-div > table > tbody > tr:nth-child(5) > td:nth-child(1) > a').click()
    s = driver.find_element_by_css_selector(
        '#search_flight > div > div:nth-child(5) > div > div > div:nth-child(2) > div.form-group > button').click()
    cookie = [item["name"] + "=" + item["value"] for item in driver.get_cookies()]
    #cookiestr = ';'.join(item for item in cookie)
    list = ''
    for x in cookie:
        list = list + x + ';'
    return list

def get_values(header,date):
    data = {'DatesSelected': [date], }
    url = 'https://booking.hkexpress.com/zh-CN/Search/DateTabSelect'
    response = requests.post(url=url, headers=header, data=json.dumps(data))
    pattern = re.compile('<input type="radio" value="(.*?)" data', re.S)
    items = re.findall(pattern, response.text)
    return items

def get_result(header, value):
    data = {"JourneyFareSellKeys": [value]}
    print(data)
    url = 'https://booking.hkexpress.com/zh-CN/Search/FareSelect'
    response = requests.post(url=url,headers = header,data =json.dumps(data))
    pattern = re.compile('<td>(.*?)</td>.*?<b>(.*?)</b>.*?<td class="al_c td1">(.*?)</td>.*?<td class="al_c td2">(.*?)</td>'
                     +'.*?<time>(.*?)</time>.*?<time>(.*?)</time>'
                      +'.*?"al_r">(.*?)</th>.*?<th class="al_r">.*?\d+">(.*?)</span>',re.S)
    items = re.findall(pattern, response.text)
    result = {}
    for item in items:
        info ={'date' : item[0],
        'flight_info' : item[1],
        'depart' : item[2],
        'dest':  item[3],
        'd_time' : item[4],
        'a_time' : item[5],
        'total_price': item[6],
        'fare': item[7],
        }
        print(info)
        save_to_mongo(info)

def datelist(beginDate, endDate):
    # beginDate, endDate是形如‘20160601’的字符串或datetime格式
    date_l=[datetime.strftime(x,'%Y-%m-%d') for x in list(pd.date_range(start=beginDate, end=endDate))]
    print(date_l)
    return date_l

def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('save to mongodb sucessfully',result)
    except Exception:
        print('fail to save the result',result)

def main():
    cookie = get_first_page()
    header = {'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Connection': 'keep-alive',
        # 'Content-Length':'349',
        'Content-Type': 'application/json',
        'Cookie': cookie,
        'Host': 'booking.hkexpress.com',
        'Origin': 'https://booking.hkexpress.com',
        'Referer': 'https://booking.hkexpress.com/zh-CN/select',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'}
    dates = datelist('20171026','20171231')
    if dates:
        for date in dates:
            values = get_values(header,date)
            try:
                x = driver.find_element_by_css_selector('#select_departure > a.btn_next').click()
                time.sleep(3)
            except:
                pass
            for value in values:
                if value:
                    get_result(header,value)

if __name__ == '__main__':
    main()