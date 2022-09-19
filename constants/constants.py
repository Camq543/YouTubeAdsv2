url_matcher = "^https?:\/\/[^#?\/]+"
video_id_matcher = "watch\?v=[-\w]+"

base_url = 'https://www.youtube.com/watch?v='

sample_entry = {
                'videoid' : None,
                'videoname' : None,
                'channelid' : None,
                'channelname' : None,
                'islive' : False,
                'views' : None,
                'commentsoff' : False,
                'comments' : None,
                'likes' : None,
                'descr' : None,
                'descrurls' : None,
                'adspresent' : False,
                # 'adtype' : adtype,
                # 'advertiser' : adbaseurl,
                # 'adfullurl' : adurl,
                # 'adid' : adid,
                # 'targetinginfo' : targetinginfo,
                'merch' : False,
                'merchstore' : None,
                'sponsored' : False,
                'datecollected' : None,
                'dateuploaded' : None,
                'uploadts' : None,
                'testid' : None,
                'removed' : False,
                'removalreason' : None,
                'inappropriate' : None,
                'context' : None,
                'contexttopic' : None,
                'contextlink' : None,
                'recs' : None
}