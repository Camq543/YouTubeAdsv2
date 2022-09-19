from selenium import webdriver

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException

from selenium.webdriver.common.keys import Keys

import time
import json
from pprint import pprint

from constants.constants import *



def play_video(driver):
    # Check if video is playing, and start video if not

    try:
        # Look for big play button on video
        WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, '//button[@class="ytp-large-play-button ytp-button"]')))
        play_button = driver.find_element_by_xpath('//button[@class="ytp-large-play-button ytp-button"]')
        play_button.click()

    except Exception as e:
        # Exception means that play button couldn't be found, video is playing
        return False

    return True

def process_browser_log_entry(entry):
    # Get network logs as a json file
    response = json.loads(entry['message'])['message']
    return response

def get_network_logs(driver):
    # Get logs of network activity
    # Used to find the YouTube video ID of the actual ad video
    browser_log = driver.get_log('performance') 
    events = [process_browser_log_entry(entry) for entry in browser_log]
    events = [event for event in events if 'Network.request' in event['method']]

    return events

def skip_to(driver, number):
    # Inputs number key to skip to point in video
    # Used to restart (input 0) or skip halfway through (input 5)
    ActionChains(driver).key_down(number).key_up(number).perform()

def check_for_premium_ad(driver):
    # Check for premium ad popup and dismiss
    # Called repeadtedly becuase the popup will intercept clicks on the page
    try:
        skip_button = driver.find_element_by_xpath('//ytd-button-renderer[@id="dismiss-button"]')
        skip_button = skip_button.find_element_by_xpath('//paper_button[@id="button"]')
        skip_button.click()
    except Exception as e:
        pass



def check_login(driver, email):
    # Checks to see if account login was successful
    # Visit gmail home and check for username in page title
    driver.get("https://www.gmail.com")
    print('gmail page title', driver.title)
    time.sleep(1)
    assert(email in driver.title)

def highlight(element, effect_time, color, border):
    # Online code found for debugging, will highlight an element you select
    """Highlights (blinks) a Selenium Webdriver element"""
    driver = element._parent
    def apply_style(s):
        driver.execute_script("arguments[0].setAttribute('style', arguments[1]);",
                              element, s)
    original_style = element.get_attribute('style')
    apply_style("border: {0}px solid {1};".format(border, color))
    time.sleep(effect_time)
    apply_style(original_style)



# def youtube_login(driver, username, password):

#     signinurl = "https://accounts.google.com/signin/v2/identifier?service=youtube"
#     driver.get(signinurl)

#     uEntry = driver.find_element_by_id("identifierId")
#     uEntry.clear()
#     uEntry.send_keys(username)

#     nextButton = driver.find_element_by_xpath('//span[text()="Next"]')
#     nextButton = nextButton.find_element_by_xpath('./..')
#     nextButton.click()

#     # WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.XPATH, '//input[@type="password"]')))
#     WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.ID, 'password')))
#     pEntry = driver.find_element_by_id("password")
#     pEntry = pEntry.find_element_by_xpath('.//input[@type="password"]')
#     pEntry.clear()
#     pEntry.send_keys(password)
#     time.sleep(1)
#     pEntry.send_keys(Keys.RETURN)
#     time.sleep(2)