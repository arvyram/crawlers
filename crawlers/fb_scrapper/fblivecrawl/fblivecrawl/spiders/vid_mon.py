import scrapy
import glob
import time, os, csv
import pandas as pd
import demjson
from scrapy.selector import Selector
import itertools
from fblivecrawl.settings import LOG_FOLDER

from fblivecrawl.items import Video_stream
import shlex, codecs, gzip

import random
from utils import Utils as ut

from datetime import date
from datetime import timedelta


lower_a = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
num = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

req_ids = [''.join(i) for i in itertools.product(lower_a,  num + lower_a)]


def compress_utf8_file(fullpath, delete_original = True):
    """Compress a UTF-8 encoded file using GZIP compression named *.gz. If `delete_original` is `True` [default: True],
    the original file specified by `delete_original` is removed after compression."""
    with codecs.open(fullpath, 'r', 'utf-8') as fin:
        with gzip.open(fullpath + '.gz', 'wb') as fout:
            for line in fin:
                fout.write(unicode(line).encode('utf-8'))
    if delete_original:
	os.remove(fullpath)


def construct_vid_pg_request( vid_url):
        print 'looking for: ', vid_url
        req_str = "https://www.facebook.com" + vid_url if 'https:' not in vid_url else vid_url
        return req_str

class FacebookVidSpider(scrapy.Spider):
    name = "fbvidspider"
    allowed_domains = ["facebook.com", "fbcdn.net"]
    log_folder = LOG_FOLDER + '0.1'

    def __init__(self, fold='', *args, **kwargs):
        super(FacebookVidSpider, self).__init__(*args, **kwargs)
        self.log_folder = LOG_FOLDER #+ 'video_logs/'# + str(level) + '/'
        self.lfs = os.path.abspath(os.path.join(self.log_folder, os.pardir))
        #print 'initing', self.lfs 
        #folds = [(today - timedelta(days=i)).strftime('%d-%b-%y') for i in range(0,7)]      
        self.logfolders = []
        #for fold in folds:
        fold_path = self.lfs +'/' + fold  
        if os.path.isdir(fold_path):
            self.logfolders.append (fold_path + '/video_logs/')   
        print self.logfolders
        #self.level = level

    def start_requests(self):
#        while True:
          for lf in self.logfolders:  
            log_folder = lf
            st_time = time.time()
            fls =  open( log_folder+'/video_ids.txt', 'r').read()
            fls = fls.split('\n')
           # print fls
            for video_log in fls:
              if video_log:
                video_log = log_folder + video_log 
                loc_time = time.time()
                f_name = video_log + '/' + 'post_bcast.csv'
                server_time  = 0
                min_t = 0
                if not os.path.isfile(f_name) and os.path.isfile(video_log+'/'+'view_data.csv'):
                    vid_dat = pd.read_csv(video_log+'/'+'view_data.csv', error_bad_lines=False)
                    if 'is_live_streaming' in vid_dat.columns:
                         bools = [eval(str(t_val)) for t_val in vid_dat['is_live_streaming'].unique()]
		        # print bools
                         if bools and not any(bools):
                           
                            server_time = int(vid_dat['r_time'].max())#vid_dat['server_time'].max()
                            min_t = int(vid_dat[vid_dat.r_time != -1].r_time.min())#vid_dat['server_time'].min()
		    #if vid_dat.video_link.unique():
                        
                elif os.path.isfile(f_name):
                    # f_name = video_log +  '/view_data.csv'
                    vid_dat = pd.read_csv(f_name, error_bad_lines=False)
                    
                    server_time = int(vid_dat['r_time'].max()) 
                    min_t = int(vid_dat['r_time'].min() )
		
		
                if  (loc_time - server_time >= 900):
                 #   print 'vide0--mon', loc_time - server_time, 'ttt', loc_time - min_t 
                    vid_link = []
                    if 'video_link' in vid_dat.columns: 
                        vid_link = vid_dat.dropna().video_link.unique()
                    elif  os.path.isfile(video_log+'/'+'view_data.csv'):  #os.path.isfile(video_log+'/'+'view_data.csv)':
			tmp_df = pd.read_csv(video_log+'/'+'view_data.csv' )
                        print tmp_df
                        if 'video_link' in tmp_df.columns:
                            vid_link = tmp_df.dropna().video_link.unique()
                    
                    print 'vid:',vid_link    
                    if len(vid_link) != 0: 
                        vid_page_url =  construct_vid_pg_request(vid_link[0])
                        #print 'url', vid_page_url
                        yield scrapy.Request( vid_page_url, meta={'vid_page_url': vid_page_url,'save_dir': video_log}, callback = self.pull_video_data )
                else:
                    continue

            # while (time.time() - st_time) <= 1800 :
            #     time.sleep(3)



    def save_dump(self, resp_text, save_dir):        
        saved_dir = save_dir
        dump_dir = saved_dir + '/video_pg_pb_dump/'
        if not os.path.exists(dump_dir):
            os.makedirs(dump_dir)
        dump_file = dump_dir + '/' +  str(time.time()) + '.txt'
        with codecs.open(dump_file, 'w', "utf-8") as f:
            f.write(resp_text)
        compress_utf8_file(dump_file)
    def construct_comment_request(self, video_id, no_comments):

        # viewas&source=2&offset=55&length=4&orderingmode=filtered&feed_context=%7B%22is_viewer_page_admin%22%3Afalse%2C%22is_notification_preview%22%3Afalse%2C%22autoplay_with_channelview_or_snowlift%22%3Afalse%2C%22fbfeed_context%22%3Atrue%2C%22location_type%22%3A5%2C%22outer_object_element_id%22%3A%22u_0_9%22%2C%22object_element_id%22%3A%22u_0_9%22%2C%22is_ad_preview%22%3Afalse%2C%22is_editable%22%3Afalse%2C%22mall_how_many_post_comments%22%3A2%2C%22story_width%22%3A502%2C%22shimparams%22%3A%7B%22page_type%22%3A16%2C%22actor_id%22%3A218800021%2C%22story_id%22%3A559256046429%2C%22ad_id%22%3A0%2C%22_ft_%22%3A%22%22%2C%22location%22%3A%22permalink%22%7D%7D&numpagerclicks&clientcommentcount=59&av=&__user=0&__a=1&__dyn=7AzHK4GgN1t2u6XomwBCwKAKGzEy4S-C11xG3Kq2i5U4e1ox27RyUrxuE98KaxeUW2y5pQ12VVojxCaxnUCu5omyp8-cwJwpV9Uqx24o9E5mqm7Q59ovwCzQ48W&__af=o&__req=5&__be=-1&__pc=EXP1%3Apackager_control_pkg&lsd=AVqB9Vhs&__rev=2664624&__srp_t=1478290391
        form_data = {

            'ft_ent_identifier': str(video_id),
            'viewas':'',
            'source':'2',
            'offset':'1',
            'length': str(no_comments),
            'orderingmode': 'filtered',
            # 'feed_context': '{"is_viewer_page_admin":false,"is_notification_preview":false,"autoplay_with_channelview_or_snowlift":false,"fbfeed_context":true,"location_type":5,"outer_object_element_id":"u_0_9","object_element_id":"u_0_9","is_ad_preview":false,"is_editable":false,"mall_how_many_post_comments":2,"story_width":502,"shimparams":{"page_type":16,"actor_id":218800021,"story_id":559256046429,"ad_id":0,"_ft_":"","location":"permalink"}}'
            'numpagerclicks': '1',
            'clientcommentcount': str(no_comments),
            'av':'',
            '__user':'0',
            '__dyn':'7AzHK4GgN1t2u6XomwBCwKAKGzEy4S-C11xG3Kq2i5U4e1ox27RyUrxuE98KaxeUW2y5pQ12VVojxCaxnUCu5omyp8-cwJwpV9Uqx24o9E5mqm7Q59ovwCzQ48W',
            '__a':'1',
            '__af':'0',
            '__req':random.choice(req_ids),
            '__pc':"EXP1:packager_control_pkg",
            '__rev':'2664624',
            '__srp_t': time.strftime('%s')
        }

        return form_data

    def pull_video_data(self, response):
        response_text = response.text
        scripts = [i for i in response.xpath('//script/text()').extract()]
        keys = ['commentcount', 'viewCount', 'likecount', 'sharecount', 'hd_src_no_ratelimit', 'sd_src_no_ratelimit', 'hd_tag', 'sd_tag', 
        'stream_type', 'hd_tag', 'hd_tag', 'minQuality', 'maxQuality', 'sd_src', 'hd_src', 'isPage', 'page_gen_time', 'islivestreaming', 'ownerName', 'isLiveVOD', 'video_id', 'video_url', 'video_channel_id']
            
        save_dir = response.meta['save_dir']
        f_name = save_dir + '/post_bcast.csv'
        self.save_dump(response_text, save_dir)
        all_dicts = ut.str_to_dict(response_text)
        resp_dict = {}
        #print all_dicts
        for k in keys:
           resp_dict[k] = all_dicts.get(k, '-1')
        resp_dict['r_time'] = time.time()
        print 'resp_dict:', resp_dict 
        vals = [] 
        #for key in keys:                                                                                                                         
         #   x = response_text.find(key)                                                                                                                   
          #  if x != -1:
           #     rt = response_text[x : x +response_text[x:].find(',')]
            #    if ':"' in rt:
             #       rt = response_text[x : x +response_text[x:].find('",') + 1]
              #  if '":' in rt:
               #     rt = response_text[x-1 : x +response_text[x:].find(',')]
               # rt = rt.encode ('UTF-8')
               # vals.append( rt)
        #for tt in csv.reader(vals, delimiter=':', quotechar='"'):
         #   resp_dict [tt[0].strip()] = tt[1].strip() 

        resp_dict['video_link'] = response.meta['vid_page_url']
        keys.append('video_link')
        keys.append('r_time')

        video_id = resp_dict['video_link'].split('/')[-2]

        
        if not os.path.isfile( f_name):
            pd.DataFrame([resp_dict]).to_csv(f_name, encoding ='utf-8', columns=keys)
 #           vid_raw_url =""
        else:
            #print f_name
            pd.DataFrame([resp_dict]).to_csv( f_name, encoding ='utf-8', mode='a', header=False )
        vid_raw_url =""
        if resp_dict.get( 'hd_src_no_ratelimit'):
            vid_raw_url = resp_dict['hd_src_no_ratelimit']
        elif resp_dict.get( 'sd_src_no_ratelimit'):
            vid_raw_url = resp_dict['sd_src_no_ratelimit']

        elif resp_dict.get( 'sd_src'):
            vid_raw_url = resp_dict['sd_src']
        print resp_dict
        print 'save_ir', save_dir
        bool_dir = os.path.isfile( LOG_FOLDER + '/' + str(video_id) + '/' +  str(video_id) + '.mp4')
        print bool_dir
        if str(vid_raw_url) != '-1' and vid_raw_url and (not bool_dir ): 
            yield scrapy.Request( vid_raw_url, meta={'save_dir': save_dir, 'vid_id':video_id, 'download_timeout': 3600}, 
                    callback = self.download_video )
            # if resp_dict.get('commentcount'):
            #     yield scrapy.FormRequest( url="https://www.facebook.com/ajax/ufi/comment_fetch.php?dpr=1", 
            #     formdata = self.construct_comment_request(video_id, resp_dict['commentcount']), 
            #     callback=self.fetch_comment, meta={'save_dir': save_dir})

       # else:
        #    #print f_name
         #   pd.DataFrame([resp_dict]).to_csv( f_name, encoding ='utf-8', mode='a', header=False )


    def fetch_comment( self, response ):
        saved_dir = response.meta['save_dir']
        dump_dir = saved_dir + '/comment_dump/'
        if not os.path.exists(dump_dir):
            os.makedirs(dump_dir)
        dump_file = dump_dir + '/' +  str(time.time()) + '.txt'
        with codecs.open(dump_file, 'w', "utf-8") as f:
            f.write(response.text)
        compress_utf8_file(dump_file)

    def download_video(self, response):
        save_dir = response.meta.get("save_dir")
        video = response.body
        video_basename =  response.meta.get("vid_id") + '.mp4'
        new_filename = os.path.join(save_dir, video_basename)
        f = open(new_filename, 'wb')
        f.write(video)
        f.close()
