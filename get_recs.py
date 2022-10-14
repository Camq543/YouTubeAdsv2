import copy
import json
import os
import logging
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import *

from utils.helpers import *
from utils.driverhelpers import *
from utils.videoinfo import *
from utils.adinfo import *
from constants.constants import *


TEST_ID, TEST_STR = get_test_id()
LOG_FILE = Path(f"logging/{TEST_STR}")
logging.basicConfig(filename=LOG_FILE, encoding="utf-8", level=logging.DEBUG)

def get_video_info(driver: webdriver.Chrome) -> dict:
    """
    Get info from video and return as dict. Assumes driver is already pointed at
    a youtube video.
    """

    # Check for misinformation context box
    context, context_link, context_topic = check_context(driver)

    sponsor_info = check_sponsorship_disclosure(driver)
    date_uploaded, upload_timestamp = get_upload_date(driver)
    merch, merch_url = check_merchandising(driver)
    recommended_videos = get_recs(driver)
    channel_id, channel_name = get_channel_info(driver)
    channel_id = remove_non_utf_characters(channel_id)
    channel_name = remove_non_utf_characters(channel_name)
    likes = get_likes(driver)
    views = get_views(driver)
    is_live = check_live(driver)
    description, urls_in_description = get_description(driver)
    description = remove_non_utf_characters(description)
    urls_in_description = [remove_non_utf_characters(url) for url in urls_in_description]
    urls_in_description = "&&&&".join(urls_in_description)
    title = remove_non_utf_characters(get_title(driver))
    comments_off = check_no_comments(driver, live=is_live)
    comments = -1

    if not is_live():
        comments = get_comment_count(driver)

    return locals()


def get_ad_info(driver: webdriver.Chrome) -> dict:
    """
    Get ad info from driver
    """
    adspresent = False
    adcheck = skip_ads(driver)
    if adcheck:
        adspresent = True
    return locals()


def main():
    # 1. Setup the config

    CONFIG_PATH = Path("config/")
    try:
        config_file = CONFIG_PATH / "computer_config.json"
        with open(config_file, "r") as config_doc:
            config = json.load(config_doc)
    except FileNotFoundError:
        config = None
        logging.warning("computer config not found")

    # 2. Get videos to watch
    seen_videos = []
    seen_path = CONFIG_PATH / config["watched_videos_videos"]

    if os.path.exists(seen_path):
        with open(seen_path, "r") as watched_videos:
            seen_videos = [
                line.strip() for line in watched_videos.read_lines()
            ]

    try:
        video_id = get_video(Path(f"constants/{config["video_list"]}"), seen_videos, config["username"])
    except Exception as e:
        logging.error("Get videos failed")
        logging.error(e)
        exit()

    if video_id is None:
        logging.info("All videos have been watched")
        exit()

    # 3. Setup Driver

    try:
        driver = create_driver(config)
        logging.info("Driver created successfully")
    except Exception as e:
        logging.error("Driver creation failed")
        logging.error(e)
        exit()

    last_recs = []

    # 4. Actual scraping

    try:
        data = []
        for _ in range(config["numvideos"]):
            entry = copy.copy(sample_entry)
            logging.info(f"Checking video {video_id}")

            # Get collection time
            entry["datecollected"] = int(time.time())
            entry["video_id"] = video_id
            entry["test_id"] = TEST_ID

            driver.get(base_url + video_id)

            # This function dismisses the youtube premium ad/ free trial popup
            # Gets called a few times because the timing of the popup is random
            # and it sometimes blocks other key elements
            check_for_premium_ad(driver)

            removed, reason = check_removed(driver)  # TODO check if we need vars here or can be removed
            if removed:
                entry =  removed, reason
                
            else:
                is_inappropriate = check_viewer_discretion(driver)
                entry["is_inappropriate"] = is_inappropriate

                entry.update(get_video_info(driver))

                # Checks for ads and skips, returns None for each variable if no ad found
                # targetinginfo, adurl, adbaseurl, adtype, adid = check_for_ads(driver)
                # print('adid:', adid)
                check_for_premium_ad(driver)

                entry.update(get_ad_info(driver))

                # get new video from the sidebar of recommended videos
                # if there are no recommended videos get from the previous set
                # of recommendations
                if len(entry["recommended_videos"]) == 0:
                    recommended_videos = previous_recommended_videos
                    logging.info(f"{video_id} - no recs")

                video_id = random.choice(entry["recommended_videos"][:10])["id"]

                previous_recommended_videos = recommended_videos

            data.append(entry)

    except Exception as e:
        logging.error("Error in main loop, cleaning up")
        exit()

    with open(Path(f"tests/{TEST_STR}.json"), "w") as outfile:
        json.dump(data, outfile)

    with open(seen_path, "w") as watched_videos:
        watched_videos.write(data[0]["video_id"] + "\n")

    logging.info("Closing driver.")
    driver.quit()
    logging.info("Goodbye.\n")


if __name__ == "__main__":
    main()
