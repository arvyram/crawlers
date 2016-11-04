# -*- coding: utf-8 -*-
import scrapy
import time, random
import urllib, urlparse
import json
import os
from fblivecrawl.items import Video_stream
import pandas as pd
import itertools
import codecs
from fblivecrawl.settings import LOG_FOLDER #DONT FORGET THE END /

from scrapy.selector import Selector

lower_a = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
num = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

req_ids = [''.join(i) for i in itertools.product(lower_a,  num + lower_a)]


class Vars:
    # https://www.facebook.com/ajax/livemap/map/data/?
    # level=0&video_count=300&dpr=1&__user=0&__a=1&_
    # _dyn=7xeXxaAcg42S5o9EdpbGEW8xdLFwgoqwXCwAxu13wIwHx27RyUrxuE98KaxeUW2y5pQ12VVojxC4oXUCu58nyokz8boaofoO6Egx61YCBxOA589o84ifmezEW
    # &__af=o&__req=1&__be=-1&__pc=EXP1%3ADEFAULT&__rev=2654378&__srp_t=1477927131
    # pc = 'EXP1:DEFAULT'
    pc ='PHASED:packager_control_pkg'
    levels = [0, 1, 2]
    reqs = []
    st_params = {
        'video_count': 300,
        'dpr': 1,
        '__user': 0,
        '__a': 1,
        '__dyn': '7xeXxaAcg42S5o9EdpbGEW8xdLFwgoqwXCwAxu13wIwHx27RyUrxuE98KaxeUW2y5pQ12VVojxC4oXUCu58nyokz8boaofoO6Egx61YCBxOA589o84ifmezEW',
        '__af':'o',
        '__rev':2654378,
        '__pc':pc,
        '__srp_t': time.strftime('%s'),
        '__req':random.choice(req_ids),
    }

def build_st_params(level):
    params = Vars.st_params
    params['level'] = level
    return urllib.urlencode( params)

def replace_url_to_str(url):
    p_url = urlparse.urlparse(url)
    i_s = p_url.path.split('/')[-2]
    params = urlparse.parse_qs(p_url.query)
    t_s = params.get('__srp_t', [str(12345)])[0]
    v_s = params.get('video_id', ['data_dump'])[0]
    return i_s + '_' + t_s + '_' + v_s + '_' + str(random.randint(1,1000)) +'.txt' 

class FacebookSpider(scrapy.Spider):

    name = "fbspider"
    allowed_domains = ["facebook.com"]
    folder_path = LOG_FOLDER #+ time.strftime('%d-%b-%Y_%w')
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    

    def __init__(self, level=0, *args, **kwargs):
        super(FacebookSpider, self).__init__(*args, **kwargs)
        self.level = level

        self.start_urls = [
            'https://www.facebook.com/ajax/livemap/map/data/?' + build_st_params( self.level ) 
        ]

    def parse(self, response):
        # open('tmp.txt', 'w').write(str( response.text))
        self.streams = []
        r_time = time.time()
        stream_response = response.text
        stream_response = stream_response[9:]
        json_stream_response = json.loads( stream_response )
        lid = json_stream_response[ 'lid' ]
        payload = json_stream_response[ 'payload' ]
        level = payload['level']
        for p_stream in payload['streams']:
            stream = {}
            stream[ 'r_time' ] = r_time
            stream['level'] = level
            stream[ 'video_id' ] = p_stream[ 'videoID']
            stream['lat'] = p_stream['lat']
            stream['lon'] =  p_stream['long']
            stream['name'] = p_stream['name']
            stream['start_time'] = p_stream['startTime']
            stream['preview_image'] = p_stream['previewImage']
            stream['viewer_count'] = float(p_stream['viewerCount'])
            stream['formatted_count'] = p_stream['formattedCount']
            stream['publisher_category'] = p_stream['publisherCategory']
            stream['profile_picture'] = p_stream['profilePicture']
            stream['v_width'] = p_stream['width']
            stream['v_height'] = p_stream['height']
            stream['message'] = p_stream['message']
            stream['message_ranges'] = p_stream['messageRanges']
            stream['u_profile'] = p_stream['url']
            stream['lid'] = lid
            
            self.save_at = FacebookSpider.folder_path + '/' + str(level) +'/'+ stream[ 'video_id' ] + '/'
            if not os.path.exists(self.save_at):
                os.makedirs(self.save_at)

            init_data = self.save_at + "vid_data.csv"
            if not os.path.isfile( init_data):
                pd.DataFrame([stream]).to_csv( init_data, encoding ='utf-8')
            else:
                pd.DataFrame([stream]).to_csv( init_data, encoding ='utf-8', mode='a', header=False )
            

            vid_id = stream[ 'video_id' ]

            if stream['viewer_count'] > 10:
                interaction_file = self.save_at + "interaction_data.csv"
                
                interaction_request = self.construct_interact_request(vid_id, stream['viewer_count'])
                yield scrapy.Request( interaction_request,
                                         meta={'append_to': interaction_file,
                                         'saved_dir': self.save_at}, 
                                         callback = self.save_interaction )
            
            video_request =self.construct_vid_request(vid_id)
            yield scrapy.Request( video_request,  
                meta={ 'saved_dir': self.save_at}, 
                callback = self.save_vid_meta )



            view_detail = self.construct_detail_request(vid_id)
            view_data_file = self.save_at + "view_data.csv"
            self.vd_dir = self.save_at + 'video_views/'
            yield scrapy.Request( view_detail,  
                meta={'append_to': view_data_file,
                     'saved_dir': self.save_at}, 
                callback = self.save_view_details )


    def save_vid_meta(self, response):        
        saved_dir = response.meta['saved_dir']

        dump_dir = saved_dir + 'meta_dat_dump/'
        if not os.path.exists(dump_dir):
            os.makedirs(dump_dir)
        dump_file = dump_dir + '/' +  str(time.time()) + '.txt'
        resp_text = response.text
        with codecs.open(dump_file, 'w', "utf-8") as f:
            f.write(resp_text)


    def save_interaction(self, response):        
        saved_dir = response.meta['saved_dir']

        dump_dir = saved_dir + 'interaction_dump/'
        if not os.path.exists(dump_dir):
            os.makedirs(dump_dir)
        dump_file = dump_dir + '/' +  str(time.time())  + '.txt'
        resp_text = response.text
        with codecs.open(dump_file, 'w', "utf-8") as f:
            f.write(resp_text)

        f_name = response.meta['append_to']

        resp_dict = self.get_parsed_interaction_dict(resp_text)
        if not os.path.isfile( f_name):
            pd.DataFrame([resp_dict]).to_csv(f_name, encoding ='utf-8')
        else:
            pd.DataFrame([resp_dict]).to_csv( f_name, encoding ='utf-8', mode='a', header=False  )


    def save_view_details(self, response):        
        saved_dir = response.meta['saved_dir']
        dump_dir = saved_dir + 'vid_details_dump/'
        if not os.path.exists(dump_dir):
            os.makedirs(dump_dir)
        dump_file = dump_dir + '/' +  str(time.time())  + '.txt'
        resp_text = response.text
        with codecs.open(dump_file, 'w', "utf-8") as f:
            f.write(resp_text)

        f_name = response.meta['append_to']

        resp_dict = self.get_parsed_view_dat_dict(resp_text)
        if not os.path.isfile( f_name):
            pd.DataFrame([resp_dict]).to_csv(f_name, encoding ='utf-8')
        else:
            pd.DataFrame([resp_dict]).to_csv( f_name, encoding ='utf-8', mode='a', header=False )





    def construct_interact_request(self, vid_id, view_count):
        # https://www.facebook.com/ajax/livemap/videos/viewers/?video_id=10207577483176784&live_viewers_count=200&dpr=1&__user=0&__a=1&__dyn=7xeXxaAcg42S5o9EdpbGEW8xdLFwgoqwXCwAxu13wIwHx27RyUrxuE98KaxeUW2y5pQ12VVojxC4oXUCu58nyokz8boaofoO6Egx61YCBxOA589o84ifmezEW&__af=o&__req=8&__be=-1&__pc=EXP1%3ADEFAULT&__rev=2654373&__srp_t=1477927131

        req_str = "https://www.facebook.com/ajax/livemap/videos/viewers/?"
        params =  {  'video_id': vid_id,
            'live_viewers_count': str(int(view_count)),
            'dpr': 1,
            '__user': 0,
            '__a': 1,
            '__be':-1,
            '__dyn': '7xeXxaAcg42S5o9EdpbGEW8xdLFwgoqwXCwAxu13wIwHx27RyUrxuE98KaxeUW2y5pQ12VVojxC4oXUCu58nyokz8boaofoO6Egx61YCBxOA589o84ifmezEW',
            '__af':'o',
            '__rev':2654378,
            '__pc':'EXP1:DEFAULT',
            '__srp_t': time.strftime('%s'),
            '__req':random.choice(req_ids),
        }
        return req_str + urllib.urlencode( params)


    def construct_vid_request(self, vid_id):
        # ttps://www.facebook.com/video/video_data/?video_id=854883404646463&supports_html5_video=true&dpr=1&__user=0&__a=1&__dyn=7xeXxaAcg42S5o9EdpbGEW8xdLFwgoqwXCwAxu13wIwHx27RyUrxuE98KaxeUW2y5pQ12VVojxC4oXUCu58nyokz8boaofoO6Egx61YCBxOA589o84ifmezEW&__af=o&__req=iy&__be=-1&__pc=PHASED%3Apackager_control_pkg&__rev=2656378&__srp_t=1478025229
        req_str = "https://www.facebook.com/video/video_data/?"
        params =  {  'video_id': vid_id,
            'supports_html5_video': 'true',
            'dpr': 1,
            '__user': 0,
            '__a': 1,
            '__be':-1,
            '__dyn': '7xeXxaAcg42S5o9EdpbGEW8xdLFwgoqwXCwAxu13wIwHx27RyUrxuE98KaxeUW2y5pQ12VVojxC4oXUCu58nyokz8boaofoO6Egx61YCBxOA589o84ifmezEW',
            '__af':'o',
            '__rev':2654378,
            '__pc':Vars.pc,
            '__srp_t': time.strftime('%s'),
            '__req':random.choice(req_ids),
        }
        return req_str + urllib.urlencode( params)

    def construct_detail_request(self, vid_id):
        # https://www.facebook.com/video/channel/view/details/async/642322782643764/?caller=live_map&dpr=1&__user=0&__a=1&__dyn=7xeXxaAcg42S5o9FEbFbGEW8xdLFwgoqwXCwAxu13wIwHx27RyUrxuE98KaxeUW2y5pQ12VVojxCaxnUCu58nyp8-cwJwFwZADxG48hwv9FosF1i2m214zRzEWew&__af=o&__req=5c&__be=-1&__pc=EXP1%3ADEFAULT&__rev=2654373&__srp_t=1477928354

        req_str = "https://www.facebook.com/video/channel/view/details/async/" + str(vid_id) +'/' + "?"


        params = {'caller': 'live_map',
                    'dpr': 1,
                '__user': 0,
                '__a': 1,
                '__be':-1,
                '__dyn': '7xeXxaAcg42S5o9EdpbGEW8xdLFwgoqwXCwAxu13wIwHx27RyUrxuE98KaxeUW2y5pQ12VVojxC4oXUCu58nyokz8boaofoO6Egx61YCBxOA589o84ifmezEW',
                '__af':'o',
                '__rev':2654378,
                '__pc':Vars.pc,
                '__srp_t': time.strftime('%s'),
                '__req':random.choice(req_ids),
        }

        return req_str + urllib.urlencode( params)


    def get_parsed_interaction_dict(self,resp_text):
        resp_dict = {}
        resp_dict['lat_lons'] = []
        resp_dict['interation_count'] = -1
        if resp_text.startswith('for'):
            resp_json = json.loads(resp_text[9:])
            resp_dict['r_time'] = time.time()
            resp_dict['lat_lons'] = resp_json["payload"]["lat_longs"]
            resp_dict['interation_count'] = len(resp_dict['lat_lons'])
            resp_dict['lid'] = resp_json["lid"]
        return resp_dict


    def deep_search(self, needles, haystack):
        found = {}
        if type(needles) != type([]):
            needles = [needles]

        if type(haystack) == type(dict()):
            for needle in needles:
                if needle in haystack.keys():
                    found[needle] = haystack[needle]
                elif len(haystack.keys()) > 0:
                    for key in haystack.keys():
                        result = self.deep_search(needle, haystack[key])
                        if result:
                            for k, v in result.items():
                                found[k] = v
        elif type(haystack) == type([]):
            for node in haystack:
                result = self.deep_search(needles, node)
                if result:
                    for k, v in result.items():
                        found[k] = v
        return found

    def get_parsed_view_dat_dict(self,resp_text):
        resp_dict = {}
        resp_dict['r_time'] = time.time()
        if resp_text.startswith('for'):
            resp_json = json.loads(resp_text[9:])
            keys = ['source','fluentContentToken','isPage','islivestreaming','commentcount', 'likecount',
            'sharecount','isLiveVOD','lid' ,'location','permalink','ownerid', 'ownerName', 'servertime']
    
            d_1 = self.deep_search(keys, resp_json)
            resp_dict['source'] = d_1['source']
            resp_dict['post_id'] = d_1['fluentContentToken']
            # resp_dict['profile_link'] = s.xpath('//abbr/parent::a/@href').extract()[0]
            # resp_dict['profile_name'] = s.xpath('//span[@class="profileLink"]/text()').extract()[0]
            # resp_dict['post_time'] = s.xpath('//abbr[@class="timestamp"]/@data-utime').extract()[0]
            resp_dict['is_page'] = d_1['isPage']
            resp_dict['is_live_streaming'] =  d_1['islivestreaming']
            resp_dict['comment_count'] = d_1['commentcount']
            resp_dict['like_count'] = d_1['likecount']
            resp_dict['share_count'] = d_1['sharecount']
            resp_dict['is_live_vod'] = d_1['isLiveVOD']
            resp_dict['lid'] = d_1['lid']
            resp_dict['location'] = d_1['location']
            resp_dict['video_link'] = d_1['permalink']
            resp_dict['owner_id'] = d_1['ownerid']
            resp_dict['owner_name'] = d_1['ownerName']
            resp_dict['server_time'] = d_1['servertime']
        return resp_dict


