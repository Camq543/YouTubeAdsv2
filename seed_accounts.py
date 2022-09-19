from selenium import webdriver

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from selenium.webdriver.common.keys import Keys

from utils.helpers import *
from utils.driverhelpers import *
from utils.videoinfo import *
from utils.adinfo import *
from constants.constants import *

import copy
import csv
import traceback
import json
import os

from pprint import pprint

# File for seeding accounts with videos to generate recommendation/advertising profile
# Watches the whole video then moves on for however many videos you put in the list to watch

def main():
    # Gen test ID and default config
    testid, test_str = get_test_id()

    # Config dict to set parameter runs
    config = {
        # If we run headless (turn on when running tests)
        'headless' : False,
        'mute' : True,
        # Number of videos to test
        'numvideos' : 2,
        # Filename to pull videos from (stored in constants)
        'video_list' : 'seed_videos.json',
        # Text file with list of videos seen already 
        'watched_videos' : 'seen_videos.txt'
    }


    try:
        # Load json holding config parameters (username and password of account, and chrome userdata folder location)
        config_doc = open('config/computer_config.json', 'r')
        computer_config = json.load(config_doc)
        config_doc.close()
        config['username'] = computer_config['username']
        config['password'] = computer_config['password']
        config['user_data'] = computer_config['user_data']
    except:
        computer_config = None
        print('computer config not found')
        pass


    # Setup logging
    try:
        logpath = 'logging/{}.txt'.format(test_str)
        if os.path.exists('logging'):
            logfile = open(logpath, 'w')
        else:
            os.makedirs('logging')
            logfile = open(logpath, 'w')

    except:
        print('Open logfile failed')
        print(traceback.format_exc())
        exit()



    # Get videos to watch
    try:
        seen_videos = []
        seen_path = 'config/' + config['watched_videos']

        if os.path.exists(seen_path):

            watched = open(seen_path, 'r')
            for line in watched:
                seen_videos.append(line.strip())
            watched.close()

            watched = open(seen_path, 'a')

        else:
            watched = open(seen_path, 'w')

        # For multiple videos, call get_video_list
        video_list = get_video_list('constantls/' + config['video_list'], config['username'], config['num_videos'])

        # For single video, call get_video
        video_id = get_video('constants/' + config['video_list'], seen_videos, config['username'])
        video_list = [video_id]

        # Test lists below
        # video_list = ["9dCm7SnVrh0", "p6rWFeaIKnA","rwcc-aNMh6g", "s68XHVWV4es", "aW4qn6hAQC0"]
        # video_list = ['p6rWFeaIKnA']
        # video_list = ['FtdVglihDok']
        # video_list = ['7CtSEKkzv0A']

        if video_id is None:
            print("I've seen it all before")
            logfile.write("I've seen it all before\n")
            logfile.close()
            exit()

    except:
        logfile.write('Get videos failed\n')
        logfile.write(traceback.format_exc())
        logfile.write('\n')
        logfile.close()
        print(traceback.format_exc())
        exit()

    # Setup Driver
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1540,1080")
        options.add_argument("--no-sandbox")
        # options.add_argument("--disable-site-isolation-trials")
        if config['headless']:
            options.add_argument("--headless")
        if config['mute']:
            options.add_argument("--mute-audio")
        if computer_config:
            options.add_argument("user-data-dir=" + config['user_data'])

        # Enables the ability to read network logs
        capabilities = DesiredCapabilities.CHROME
        capabilities["goog:loggingPrefs"] = {"performance": "ALL"}
        driver = webdriver.Chrome(options = options,
            desired_capabilities=capabilities)

        # Wait for driver to load
        time.sleep(3)

        # Make sure that account logged in successfully
        if computer_config:
            check_login(driver, config['username'])

        logfile.write('Driver launched successfuly\n')

    except:
        logfile.write('Driver setup failed\n')
        logfile.write(traceback.format_exc())
        logfile.write('\n')
        logfile.close()
        print(traceback.format_exc())
        exit()


    # Actual scraping
    try:
        data = []
        for videoid in video_list:
            logfile.write('Checking video {}\n'.format(videoid))

            # Get collection time
            collectiontime = int(time.time())        

            # Load video
            driver.get(base_url + videoid)

            # This function dismisses the premium ad popup, gets called a few times
            check_for_premium_ad(driver)

            # Check for age gate and bypass
            inappropriate = check_viewer_discretion(driver)

            # Try to play video 
            played = play_video(driver)

            check_for_premium_ad(driver)

            # Check if video was removed and get removal reason
            removed, reason = check_removed(driver)
            # print(removed, reason)

            if removed:
                # Get empty entry and return
                entry = copy.copy(sample_entry)
                entry['videoid'] = videoid
                entry['datecollected'] = collectiontime
                entry['testid'] = testid
                entry['removed'] = True
                entry['removalreason'] = reason

                data.append(entry)
                # events = get_network_logs(driver)
                continue
            
            check_for_premium_ad(driver)
            
            # Restart video in case youtube saved our watch time
            skip_to(driver, '0')
            time.sleep(2)

            "Logic to find advertisement type and info goes here"
            # Checks for ads and skips, returns None for each variable if no ad found
            # targetinginfo, adurl, adbaseurl, adtype, adid = check_for_ads(driver)
            #print('adid:', adid)

            # Skip ads or wait for them to be over if unskippable
            adspresent = False
            adcheck = skip_ads(driver)
            if adcheck:
                adspresent = True

            # Get top recommended videos
            recs = get_recs(driver)

            # Check for misinformation context box
            context, context_link, context_topic = check_context(driver)
            
            # Check for paid promotion disclaimer
            sponsor = check_sponsorship_disclosure(driver)

            # Check for channel merchandising
            merch, merch_url = check_merchandising(driver)

            check_for_premium_ad(driver)

            # Check if video is live, changes some DOM elements
            islive = check_live(driver)

            # Get video title
            title = get_title(driver).encode("utf-8", 'ignore').decode('utf-8','ignore')
        
            # Get channel info
            channelID, channelName = get_channel_info(driver)
            # Strip non utf chars
            channelID = channelID.encode("utf-8", 'ignore').decode('utf-8','ignore')
            channelName = channelName.encode("utf-8", 'ignore').decode('utf-8','ignore')
            
            # If it's live, the engagement data is weird so we ignore it
            if islive:
                likes = get_likes(driver)
                views = get_views(driver)
                comments_off = check_no_comments(driver, live = True)
                comments = -1
            # Else get likes, views and number of comments
            else:
                views = get_views(driver)

                likes = get_likes(driver)

                comments_off = check_no_comments(driver)
                comments = get_comment_count(driver)


            # Get video description info and list of links 
            descr, descrurls = get_description(driver)

            # Strip non utf chars
            descr = descr.encode("utf-8", 'ignore').decode('utf-8','ignore')
            for i in range(len(descrurls)):
                descrurls[i] = descrurls[i].encode("utf-8", 'ignore').decode('utf-8','ignore')

            # Turn list of links into string for storage
            descrurls = "&&&&".join(descrurls)

            # Get upload date
            dateuploaded, uploadts = get_upload_date(driver)

            # Get duration of video so we can watch the whole thing
            time_left = get_duration_remaining(driver)

            timestamp = time.time()
            count = 0
            watch_time = 0

            # Wait while video finishes
            while time_left - watch_time > 1:
                print('Time left', time_left)
                print('Watch time', watch_time)
                
                check_for_premium_ad(driver)
                adcheck = skip_ads(driver)

                if adcheck:
                    adspresent = True

                time.sleep(10)
                count += 1

                if count % 10 == 0:
                    watch_time = 0
                    timestamp = time.time()
                    time_left = get_duration_remaining(driver)

                watch_time = time.time() - timestamp

                if time_left == -1:
                    watch_time = 0
                    timestamp = time.time()
                    time_left = get_duration_remaining(driver)



            # Store data
            data.append({
                'videoid' : videoid,
                'videoname' : title,
                'channelid' : channelID,
                'channelname' : channelName,
                'islive' : islive,
                'views' : views,
                'commentsoff' : comments_off,
                'comments' : comments,
                'likes' : likes,
                'descr' : descr,
                'descrurls' : descrurls,
                'adspresent' : adspresent,
                # 'adtype' : adtype,
                # 'advertiser' : adbaseurl,
                # 'adfullurl' : adurl,
                # 'adid' : adid,
                # 'targetinginfo' : targetinginfo,
                'merch' : merch,
                'merchstore' : merch_url,
                'sponsored' : sponsor,
                'datecollected' : collectiontime,
                'dateuploaded' : dateuploaded,
                'uploadts' : uploadts,
                'testid' : testid,
                'removed' : False,
                'removalreason' : reason,
                'inappropriate' : inappropriate,
                'context' : context,
                'contexttopic' : context_topic,
                'contextlink' : context_link,
                'recs' : recs
            })

            pprint(recs)



        pprint(data)




    except Exception as e:
        logfile.write('Error in main loop, cleaning up\n')
        logfile.write(traceback.format_exc())
        logfile.write('\n')
        logfile.close()
        print(traceback.format_exc())
        exit()
    

    # Make tests directory if needed and store test data
    if os.path.exists('tests'):
        pass
    else:
        os.makedirs('tests')
    outfile = open('tests/' + test_str + '.json', 'w')
    json.dump(data, outfile)
    outfile.close()

    # Add watched videos to list 
    for entry in data:
        watched.write(entry['videoid'] + '\n')
    watched.close()

    print('closing driver')
    logfile.write('Closing driver.\n')
    driver.quit()
    logfile.write('Goodbye.\n')
    print('Goodbye')
    logfile.close()


main()