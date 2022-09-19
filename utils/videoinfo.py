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
import datetime
import traceback

import re

from utils.helpers import *
from utils.driverhelpers import *



def check_live(driver):
    # Check if video was/is a live stream, certain dom elements are switched
    try:
        container = driver.find_element_by_xpath('//span[@class="view-count style-scope ytd-video-view-count-renderer"]')
    except Exception as e:
        print('error in live check')
        print(e)
        return False

    if 'watching now' in container.text:
        return True
    else:
        return False

def check_viewer_discretion(driver):
    # Check if video has viewer restrictions on it
    # Need to click through age restrictions/content warnings
    # Returns true if any content gate is found
    innapropriate = False
    try:
        container = driver.find_element_by_xpath('//div[@class="style-scope yt-player-error-message-renderer"]')
        button = container.find_element_by_xpath('.//tp-yt-paper-button[@class="style-scope yt-button-renderer style-overlay size-default"]')
        button.click()
        time.sleep(1)
        innapropriate = True
    except:
        innapropriate = False

    return innapropriate

def check_removed(driver):
    # Check if video is removed
    # Returns True if removed, along with the resaon for removal (private, content guidelines, removed by uploader, etc.)
    removed = False
    reason = None

    try:
        container = driver.find_element_by_xpath('//div[@class="style-scope yt-player-error-message-renderer"]')
        inner = container.find_element_by_xpath('.//yt-formatted-string[@id="subreason"]')
        removed = True
        reason = inner.get_attribute('innerHTML')
    except:
        removed = False
        reason = None
    
    return removed, reason

def check_merchandising(driver):
    # Check to see if the page has official merchandising on the YouTube page

    merch = False
    store = None

    try:
        # Check for merchandising and get store URL
        merch_shelf = driver.find_element_by_xpath('//div[@class="style-scope ytd-merch-shelf-renderer"]')
        merch = True
        merch_link = merch_shelf.find_element_by_xpath('.//div[@class="product-item-merchant-text style-scope ytd-merch-shelf-item-renderer"]')
        
        # Click store link and get resolved URL
        merch_link.click()
        current_tab = driver.current_window_handle
        tabs_open = driver.window_handles
        driver.switch_to.window(tabs_open[1])

        loaded = False
        start = time.time()
        while not loaded:
            try:
                status = driver.execute_script("return document.readyState")
            except:
                status = "uninitialized"

            loaded = status != "uninitialized"
            if not loaded:
                loaded = (time.time() - start) > 10

            time.sleep(.5)

        url = driver.current_url
        store = re.search(url_matcher, url)[0]

        driver.close()
        driver.switch_to.window(current_tab)

    except:
        merch = False
        store = None

    return merch, store

def get_title(driver):
    # Get video title
    return driver.find_element_by_xpath('//yt-formatted-string[@class="style-scope ytd-video-primary-info-renderer"]').text

def get_channel_info(driver):
    container = driver.find_element_by_xpath('//ytd-channel-name[@id="channel-name"]')
    channel = container.find_element_by_xpath('.//a[@class="yt-simple-endpoint style-scope yt-formatted-string"]')

    link = channel.get_attribute('href')
    link = removeprefix(link, 'https://www.youtube.com')

    if '/channel/' not in link:
        ID = link
    else:
        ID = removeprefix(link, '/channel/')

    return ID, channel.text

def get_views(driver):
    # Get number of views
    # Returns -1 if we cant find the view count
    try:
        container = driver.find_element_by_xpath('//span[@class="view-count style-scope ytd-video-view-count-renderer"]')
        print(container)
        views = int("".join(list(filter(str.isdigit, container.text))))
    except:
        return -1

    return views

def check_no_comments(driver, live = False):
    # Check if comments have been turned off
    comments_off = False

    if live:
        try:
            container = driver.find_element_by_xpath('//ytd-message-renderer[@class="style-scope ytd-live-chat-frame"]')
            message = container.find_element_by_xpath('.//yt-formatted-string[@id="message"]')
            comments_off = message.text == 'Chat is disabled for this live stream.'
        except:
            comments_off = False

    else:
        try:
            message = driver.find_element_by_xpath('//yt-formatted-string[@id="message"]')
            info = message.find_element_by_xpath('.//span[@class="style-scope yt-formatted-string"]')
            comments_off = info.text == 'Comments are turned off.'
        except:
            comments_off = False

    return comments_off


def get_comment_count(driver):
    # Get number of comments
    # Returns -1 if can't get comment count
    SCROLL_PAUSE_TIME = .5

    last_height = driver.execute_script("return document.documentElement.scrollHeight")
    found = False
    container = None

    # Sometimes need to scroll page to get comment section to load
    count = 0
    while not found:
        try:
            container = driver.find_element_by_xpath('//yt-formatted-string[@class="count-text style-scope ytd-comments-header-renderer"]')
            found = True
        except:
            found = False

        if not found:
            driver.execute_script("window.scrollTo(0, " + str(last_height/4) + ");")
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.documentElement.scrollHeight") 

            if (new_height == last_height) and count > 3:
                driver.execute_script("window.scrollTo(0, 0);")
                return -1
            last_height = new_height

        count += 1


    try:
        comment_count = int("".join(list(filter(str.isdigit, container.text))))
    except:
        comment_count = -1

    driver.execute_script("window.scrollTo(0, 0);")

    return comment_count

def get_likes(driver, live = False):
    # Get like and dislike count (dislikes now hidden)
    # May be broken for live videos 

    button_container = driver.find_element_by_xpath('//div[@id="top-level-buttons-computed"]')
    containers = button_container.find_elements_by_xpath('.//button[@class="style-scope yt-icon-button"]')

    likes = -1

    first = True
    for container in containers:
        aria_label = container.get_attribute('aria-label')
        if aria_label is None:
            aria_label = container.text

        aria_label = aria_label.replace(',', '')

        if 'like this video along' in aria_label.lower():
            try:
                likes = int("".join(list(filter(str.isdigit, aria_label))))
            except ValueError:
                likes = -1
        else:
            continue


    return likes


def get_likes_live(driver):
    # Get likes if video is live (same logic but diffrent dom element)
    
    button_container = driver.find_element_by_xpath('//div[@id="top-level-buttons-computed"]')
    containers = button_container.find_elements_by_xpath('.//button[@class="style-scope yt-icon-button"]')

    likes = -1

    first = True
    for container in containers:
        # print(container.get_attribute('class'))
        aria_label = container.get_attribute('aria-label')
        # print(aria_label)
        if aria_label is None:
            aria_label = container.text


        aria_label = aria_label.replace(',', '')

        if 'like' in aria_label:
            if aria_label == "No likes":
                likes = 0
            else:
                try:
                    # print(list(filter(str.isdigit, aria_label)))
                    likes = int("".join(list(filter(str.isdigit, aria_label))))
                except ValueError:
                    # print('likes error')
                    likes = -1
        else:
            continue


    return likes

def get_description(driver):
    # Get description string and URLs in description
    # Returns full description string and all found URLs

    try:
        # See if description is loaded
        driver.find_element_by_xpath('//yt-formatted-string[@class="less-button style-scope ytd-video-secondary-info-renderer"]')
        pass
    except:
        # If needed, click show more button to load description
        show_more = driver.find_element_by_xpath('//yt-formatted-string[@class="more-button style-scope ytd-video-secondary-info-renderer"]')
        show_more.click()

    # Description is stored as blocks of text and list of highlighted URLs, we need to find and recombine into descr string
    container = driver.find_element_by_xpath('//div[@id="description"]')
    text_blocks = container.find_elements_by_xpath('.//span[@class="style-scope yt-formatted-string"]')
    url_blocks = container.find_elements_by_xpath('.//a[@class="yt-simple-endpoint style-scope yt-formatted-string"]')

    text_index = 0
    url_index = 0
    descr_string = ""
    urls = []

    # Add text block to string, then add url if there are any left
    # Store URLs in separate list as well
    while text_index < len(text_blocks):
        descr_string += text_blocks[text_index].get_attribute("innerHTML")
        text_index += 1

        if url_index < len(url_blocks):
            url = get_descr_link(url_blocks[url_index].get_attribute("href"))
            descr_string += url
            urls.append(url)
            url_index += 1

            descr_string += ' '
            text_index += 1

    return descr_string, urls

def get_upload_date(driver):
    # Get date uploaded
    # Returns date as string and timestamp
    container = driver.find_element_by_xpath('//div[@id="info-strings"]')
    date = container.find_element_by_xpath('.//yt-formatted-string[@class="style-scope ytd-video-primary-info-renderer"]').text

    pattern = "(Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?) \d{1,2}, \d{4}"
    
    search = re.search(pattern, date)
    if search is not None:
        date = search.group()

    try:
        date_time_object = datetime.datetime.strptime(date, '%b %d, %Y')
    except: 
        return date, datetime.datetime(1990,1,1).timestamp()
    
    return date, int(date_time_object.timestamp())

def check_context(driver):
    # Check for context warnings (fact check notification type things that show up under the video)
    # Returns if there is a context warning, any associated link (usually to a wikipedia page), and the topic YouTube flags
    context = False
    link = None
    topic = None

    try:    
        container = driver.find_element_by_xpath('//div[@id="clarify-box"]')
        link_container = container.find_element_by_xpath('.//a[@class="yt-simple-endpoint title-container style-scope ytd-info-panel-content-renderer"]')
        link = link_container.get_attribute('href')
        topic = link_container.find_element_by_xpath('.//yt-formatted-string[@class="style-scope ytd-info-panel-content-renderer"]').get_attribute('innerHTML')   
        context = True         

    except:
        pass

    return context, link, topic

def check_sponsorship_disclosure(driver):
    # Check if channel has disclosed any sponsorship
    sponsor = False
    try:
        sponsor_box = driver.find_element_by_xpath('//div[@div="ytp-paid-content-overlay-text"]')
        sponsor = True
    except:
        sponsor = False

    return sponsor


def get_recs(driver, maxnum = 20):
    # Get YouTube recommendations

    # Get the dom elements storing the recommendations
    out = []
    recs = driver.find_elements_by_xpath('//ytd-compact-video-renderer[@class="style-scope ytd-item-section-renderer"]')
    if len(recs) == 0:
        recs = driver.find_elements_by_xpath('//ytd-compact-video-renderer[@class="style-scope ytd-watch-next-secondary-results-renderer"]')

    # Parse the reccomendation elements to get video info
    count = 0
    for element in recs:
        thumb = element.find_element_by_xpath('.//a[@class="yt-simple-endpoint style-scope ytd-compact-video-renderer"]')
        href = thumb.get_attribute('href')
        watch_index = href.find("watch?v=")
        if watch_index > -1:
            videoid = href[watch_index + 8 : watch_index + 19]
        else:
            videoid = None

        channel = element.find_element_by_xpath('.//yt-formatted-string[@class="style-scope ytd-channel-name"]').text
        video = element.find_element_by_xpath('.//span[@id="video-title"]')
        title = video.text


        out.append({'title' : title, 'id' : videoid, 'channel_name' : channel})

        count += 1
        if count == maxnum:
            break

    return out

def get_duration_remaining(driver):
    # Get duration remaining in video
    # Returns -1 if can't get duration
    try:
        # Pause video to get player bar to popup so we can see the duration element
        player = driver.find_element_by_xpath('//div[@id="movie_player"]')
        try:
            player.click()
        except:
            pass

        length = duration_from_text(driver.find_element_by_xpath('//span[@class="ytp-time-duration"]').text)
        current = duration_from_text(driver.find_element_by_xpath('//span[@class="ytp-time-current"]').text)
        time_left = length - current
        player.click()

        return time_left

    except:
        print(traceback.format_exc())
        return -1
