#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, argparse, time, logging, os, redis
from bigbluebutton_api_python import BigBlueButton

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

browser = None
selelnium_timeout = 30
connect_timeout = 5

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

parser = argparse.ArgumentParser()
parser.add_argument("-s","--server", help="Big Blue Button Server URL")
parser.add_argument("-p","--secret", help="Big Blue Button Secret")
parser.add_argument("-i","--id", help="Big Blue Button Meeting ID")
parser.add_argument("-m","--moderator", help="Join the meeting as moderator",action="store_true")
parser.add_argument("-u","--user", help="Name to join the meeting",default="Live")
parser.add_argument("-r","--redis", help="Redis hostname",default="redis")
parser.add_argument("-c","--channel", help="Redis channel",default="chat")
args = parser.parse_args()

bbb = BigBlueButton(args.server,args.secret)

def set_up():
    global browser

    options = Options()
    options.add_argument('--disable-infobars')
    options.add_argument('--no-sandbox')
    options.add_argument('--kiosk')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--window-position=0,0')
    options.add_experimental_option("excludeSwitches", ['enable-automation'])
    options.add_argument('--incognito')
    options.add_argument('--shm-size=1gb')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-fullscreen')

    logging.info('Starting browser to chat!!')

    browser = webdriver.Chrome(executable_path='./chromedriver',options=options)

def bbb_browser():
    global browser

    logging.info('Open BBB for chat!!')
    browser.get(get_join_url())

    element = EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Listen only"]'))
    WebDriverWait(browser, selelnium_timeout).until(element)
    browser.find_elements_by_css_selector('[aria-label="Listen only"]')[0].click()

    element = EC.invisibility_of_element((By.CSS_SELECTOR, '.ReactModal__Overlay'))
    WebDriverWait(browser, selelnium_timeout).until(element)

    browser.find_element_by_id('message-input').send_keys("Viewers of the live stream can now send messages to this meeting")
    browser.find_elements_by_css_selector('[aria-label="Send message"]')[0].click()

    redis_r = redis.Redis(host=args.redis,charset="utf-8", decode_responses=True)
    redis_s = redis_r.pubsub()
    redis_s.psubscribe(**{args.channel:chat_handler})
    thread = redis_s.run_in_thread(sleep_time=0.001)

def chat_handler(message):
    global browser
    browser.find_element_by_id('message-input').send_keys(message['data'])
    browser.find_elements_by_css_selector('[aria-label="Send message"]')[0].click()
    logging.info(message['data'])

def get_join_url():
    minfo = bbb.get_meeting_info(args.id)
    if args.moderator:
        pwd = minfo.get_meetinginfo().get_moderatorpw()
    else:
        pwd = minfo.get_meetinginfo().get_attendeepw()
    return bbb.get_join_meeting_url(args.user,args.id,pwd)

def chat():
    while True:
        time.sleep(60)


while bbb.is_meeting_running(args.id).is_meeting_running() != True:
    time.sleep(connect_timeout)
set_up()
bbb_browser()
chat()
browser.quit()