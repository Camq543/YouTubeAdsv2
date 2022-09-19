from selenium import webdriver

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementClickInterceptedException

from selenium.webdriver.common.keys import Keys

from utils.driverhelpers import *
from utils.helpers import *
from constants.constants import *

import time
import traceback

def check_for_banner(driver):
    # Checks page for the presence of a banner ad
    # Returns the button to click on to get more ad info ("Why am I seeing this ad" button)
    # Returns none if no ad found
    banner_info = None

    try:
        container = driver.find_element_by_xpath('//div[@class="ytp-ad-image-overlay"]')
        banner_info = container.find_element_by_xpath('.//span[@class="ytp-ad-button-icon"]')


    except NoSuchElementException:
        pass

    return banner_info

def check_for_preroll(driver):
    # Checks page for the presence of a preroll ad
    # Returns the button to click on to get more ad info ("Why am I seeing this ad" button)
    # Returns none if no ad found
    # As is, should only be called after checking for banner as it might pick up a banner ad
    preroll_info = None

    try:
        preroll_info = WebDriverWait(driver, 2).until(EC.element_to_be_clickable(
            (By.XPATH, "//span[@class='ytp-ad-button-icon']")))
    except:
        pass

    return preroll_info

def check_ad_type(driver):
    # Checks for the presense of an advertisement, and what type of ad it is
    # Returns the type of ad and the "why am I seeing this ad" button, if an ad was found
    info = None
    adtype = ''

    try:
        banner_info = check_for_banner(driver)
        # print('banner info:', banner_info)
        if not banner_info:
            # print('entered preroll check')
            preroll_info = check_for_preroll(driver)
            if preroll_info:
                info = preroll_info
                adtype = 'preroll'

        else:
            # print('entered banner chunk')
            info = banner_info
            adtype = 'banner'

    except NoSuchElementException:
        info = None
        adtype = ''
        
    return info, adtype


def get_ad_info(driver, button):
    "CURRENTLY BROKEN"
    # Get the targeting info from "why am I seeing this ad button"
    # Pass in adinfo button from check_ad_type
    # Returns the targeting info as a list


    toReturn = []
    try:
        # Try to click ad info button
        button.click()
    except ElementClickInterceptedException as e:
        try:
            # If click is intercepted, try mousing over button to get video player bar to popup
            ActionChains(driver).move_to_element(button).perform()
            button.click()
        except:
            return None

    try:
        # Find targeting info 
        driver.find_element_by_xpath('//button[@class="VfPpkd-Bz112c-LgbsSe yHy1rc eT1oJ DiOXab YJBIwf"]').click()
    except Exception as e:
        print("Get_ad_info closing exception", e)
        pass

    return toReturn

def get_preroll_advertiser(driver):
    # Get the advertiser page from the advertisement
    # Clicks on link, loads ad page, pulls URL
    # Clicked on link to bypass ad retargeting urls

    # Find button to visit advertiser
    ad_button = driver.find_element_by_xpath('//button[@class="ytp-ad-button ytp-ad-visit-advertiser-button ytp-ad-button-link"]')
    try:
        driver.execute_script("arguments[0].click();", ad_button)
        # ad_button.click()
    except:
        # Try again
        time.sleep(1)
        ad_button = driver.find_element_by_xpath('//button[@class="ytp-ad-button ytp-ad-visit-advertiser-button ytp-ad-button-link"]')
        ad_button.click()

    # Wait for ad to load in new page
    current_tab = driver.current_window_handle
    tabs_open = driver.window_handles
    driver.switch_to.window(tabs_open[1])
    loaded = False
    start = time.time()
    while not loaded:
        try:
            # Wait till page is loaded
            status = driver.execute_script("return document.readyState")
        except:
            status = "uninitialized"

        loaded = status != "uninitialized"
        if not loaded:
            loaded = (time.time() - start) > 10

        time.sleep(.5)

    # Once page is loaded return the resolved URL
    url = driver.current_url
    driver.close()
    driver.switch_to.window(current_tab)

    return url

def get_banner_advertiser(driver):
    "Same logic as get_preroll_advertiser, could probably be rewritten into the same function"
    # Get the advertiser page from the advertisement
    # Clicks on link, loads ad page, pulls URL
    # Clicked on link to bypass ad retargeting urls


    ad_button = driver.find_element_by_xpath('//div[@class="ytp-ad-image-overlay"]')
    ad_button = ad_button.find_element_by_xpath('.//img')
    try:
        driver.execute_script("arguments[0].click();", ad_button)
    except Exception as e:
        print("first exception in banner advertiser", e)
        try:
            time.sleep(1)
            ad_button = driver.find_element_by_xpath('//div[@class="ytp-ad-image-overlay"]')
            ad_button.click()
        except Exception as f:
            print("second exception in banner advertiser", f)
            return None


    current_tab = driver.current_window_handle
    tabs_open = driver.window_handles
    driver.switch_to.window(tabs_open[1])
    loaded = False
    while not loaded:
        status = driver.execute_script("return document.readyState")
        loaded = status != "uninitialized"
    url = driver.current_url

    driver.close()
    driver.switch_to.window(current_tab)

    return url

def get_ad_id(driver):
    # Gets the video ID of the first preroll advertisement
    # All YouTube video ads are hosted as an unlisted video on YouTube with a VideoID
    # VideoID is sent in network response payload
    # Stored in response string as ad_v parameter
    events = get_network_logs(driver)
    for event in events:
        if 'request' in event['params']:
            if 'url' in event['params']['request']:
                if 'ad_v' in event['params']['request']['url']:
                    index = event['params']['request']['url'].find('ad_v')
                    toReturn = event['params']['request']['url'][index + 5:index + 16]
                    return toReturn
                else:
                    toReturn = None

    return toReturn

def get_number_of_ads_left(driver):
    # Gets number of ads loaded by YouTube
    # Used to help figure out how to skip ads
    try:
        container = driver.find_element_by_xpath('//span[@class="ytp-ad-simple-ad-badge"]')
        element = container.find_element_by_xpath('.//div[@class="ytp-ad-text"]')
        text = element.text 
        if 'of' in text:
            num_ads = int(text[-3]) - int(text[-8]) + 1
        else:
            num_ads = 1
        print('Found ' + str(num_ads) + ' ads.')
        return num_ads

    except:
        return -1

def get_ad_duration(driver):
    # Get time left in advertisement
    container = driver.find_element_by_xpath('//div[@class="ytp-ad-duration-remaining"]')
    element = container.find_element_by_xpath('.//div[@class="ytp-ad-text"]')

    text = element.text
    if text:
        return duration_from_text(text)
    else:
        return -1



def skip_ads(driver, ad_type = None):
    # Skip ads if possible or wait till ads are done
    # Returns True if there were ads to be skipped

    if ad_type is None:
        # Check what kind of ad we got
        info, ad_type = check_ad_type(driver)

    if ad_type != 'preroll':
        if ad_type == 'banner':
            # If its a banner ad, we don't need to skip it
            return True
        else:
            # If no ad, return false
            return False


    try:
        # Try finding the skip button for ads
        skip_button = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//span[@class="ytp-ad-skip-button-container"]')))
        if skip_button:
            # If we find it, click the skip button
            driver.execute_script("arguments[0].click();", skip_button)
        return True
    except:
        # If we can't find it, wait (means an ad is playing but can't be skipped right now)
        # print('couldnt find skip button first pass')
        pass

    # Figure out how many ads will be played
    num_ads = get_number_of_ads_left(driver)
    start = time.time()
    while num_ads != 1:
        # If there are multiple ads playing, wait for up to 30 seconds to get to the last ad
        time.sleep(1)
        num_ads = get_number_of_ads_left(driver)
        now = time.time()
        if (now - start) > 30:
            break

    try:
        # Once we're down to one ad, check to see if there's a count down timer to the video
        element = driver.find_element_by_xpath('//div[@class="ytp-ad-text ytp-ad-preview-text"]')
        if 'play after' in element.text:
            # If there's a countdown, wait it out
            duration = get_ad_duration(driver)
            if duration > 0:
                time.sleep(duration + 10)
            else:
                # If something broke, wait a minute and return True because we found an ad
                time.sleep(60)
            return True
    except:
        # Something went wrong
        print('error while waiting for ad to end')
        print(traceback.format_exc())
        pass

    try:
        # Check again for a skip button
        skip_button = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//span[@class="ytp-ad-skip-button-container"]')))
        if skip_button:
            driver.execute_script("arguments[0].click();", skip_button)
        return True
    except:
        print('couldnt find skip button second pass')
        print(traceback.format_exc())
        pass

    return False


def check_for_ads(driver):
    # Checks for the presence of ads, and skips them or waits for them to end

    targetinginfo = []
    ad_url = None
    ad_base_url = None
    ad_type = None
    ad_info = None
    ad_id = None

    # Check if and what type of ad is playing 
    info, ad_type = check_ad_type(driver)

    if info is not None:
        # If we found an ad, get the targeting info and advertiser url
        targetinginfo = get_ad_info(driver, info)
        if ad_type == 'preroll':
            ad_url = get_preroll_advertiser(driver)
        elif ad_type == 'banner':
            ad_url = get_banner_advertiser(driver)


    else:
        # If we didn't find an ad at the start of the video, skip halfway through and do the same thing
        # This will sometimes get a banner ad to load
        skip_to(driver, "5")
        time.sleep(6)
        info, ad_type = check_ad_type(driver)
        if info is not None:
            targetinginfo = get_ad_info(driver, info)
            if ad_type == 'preroll':
                ad_url = get_preroll_advertiser(driver)
            elif ad_type == 'banner':
                ad_url = get_banner_advertiser(driver)

    # Try to skip ads if any are there
    skip_ads(driver, ad_type)

    if ad_url:
        # If we found an advertising url, strip the base url for storage
        ad_base_url = re.search(url_matcher, ad_url)[0]

    if targetinginfo is not None:
        # If we found targeting info, join list into string for storage
        targetinginfo = "&&&&".join(targetinginfo)
    else:
        targetinginfo = ''

    if ad_type == 'preroll':
        # If we found a video advertisement, pull the videoid from the network logs
        ad_id = get_ad_id(driver)

    return targetinginfo, ad_url, ad_base_url, ad_type, ad_id

