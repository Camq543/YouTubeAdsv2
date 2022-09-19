import re
import datetime
import random
import json



def removeprefix(instr, prefix):
    # Remove a substr from the start of a string
    # Returns new string without prefix
    if instr.startswith(prefix):
        return instr[len(prefix):]
    else:
        return instr[:]

def removesuffix(instr, suffix):
    # Remove a substr from the end of a str
    # Returns new string without suffix
    if suffix and instr.endswith(suffix):
        return instr[:-len(suffix)]
    else:
        return instr[:]

def get_test_id():
    # Generates an id for scraping run based on system time
    d = datetime.datetime.now()
    test_str = '{date:%Y_%m_%d_%H_%M_%S}'.format(date = d)
    test_id = int('{date:%Y%m%d%H%M%S}'.format(date = d))

    return test_id, test_str

def get_video_list(filename, username, num_videos):
    # Get list of videos from file based on account in config
    # Picks a random channel then a random video from that channel until we've found num_videos to watch
    # Returns list of videoids

    infile = open(filename, 'r')
    vids = dict(json.load(infile))

    video_list = []
    count = 0

    # Get list of channels and videos this username is meant to watch
    channels = list(vids['username'].keys())

    # Pick a random channel and a random video from that channel and add it to the list
    while count < num_videos:
        channel_vids = vids[username][channels[random.randint(0, len(channels) - 1)]]
        video_id = channel_vids[username][random.randint(0,len(channel_vids) - 1)]['vid_id']
        if video_id not in video_list:
            video_list.append(video_id)
            count += 1

    infile.close()

    return video_list

# def get_video_list(filename, num_videos):
#     # Get's list of videos from smaller dataset
#     # Just picks num_videos of videos randomly from a list
#     # Older function 

#     infile = open(filename, 'r')
#     video_list = []
#     for line in infile:
#         if line.strip() == "#NAME?":
#             continue
#         video_list.append(line.strip())

#     infile.close()
#     random.shuffle(video_list)

#     return video_list[:num_videos]

def get_video(filename, seen, username):
    # Gets a single video from JSON object based on account username
    # Makes sure video was not already watched (in seen list)
    f = open(filename)
    videos = json.load(f)
    channel_list = videos[username]
    channelid = random.choice(list(channel_list.keys()))
    video_list = channel_list[channelid]
    random.shuffle(video_list)

    for video in video_list:
        if video not in seen:
            return video
    
    return None

def get_descr_link(link_text):
    # Get link from stored description URLs
    # Links are stored by YouTube with certain characters changed and youtube prefix that needs to be stripped
    search = "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    temp = removeprefix(link_text, "https://www.youtube.com/")
    temp = temp.replace("%3A", ":")
    temp = temp.replace("%2F", "/")

    if re.search(search,temp) is None:
        re.search(search,temp)
        return link_text
    else:
        url = re.search(search,temp)[0]

        return url

def duration_from_text(text):
    # Get duration as seconds from string
    times = text.split(':')
    print(times)
    if len(times) == 3:
        duration = 60 * 60 * int(times[0]) + 60 * int(times[1]) + int(times[2])
    elif len(times) ==2:
        duration = 60 * int(times[0]) + int(times[1])
    else:
        duration = int(times[0])
    return duration
