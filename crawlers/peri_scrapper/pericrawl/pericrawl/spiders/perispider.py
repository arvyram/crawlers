# -*- coding: utf-8 -*-
import scrapy
import random
import json, time, gzip
import os
import  cStringIO
import codecs
from string import Template

from pericrawl.settings import LOG_FOLDER


channel_url = 'https://channels.periscope.tv/v1/top/channels/broadcasts?languages=en'
channel_bcast_url =Template('https://channels.periscope.tv/v1/channels/$channel_id/broadcasts?languages=en')
bcast_url = Template('https://api.periscope.tv/api/v2/getBroadcastPublic?broadcast_id=$broadcast_id')
ad_bcast_url = Template('https://api.periscope.tv/api/v2/accessVideoPublic?broadcast_id=$broadcast_id')


def gen_random(n):
    return ''.join(random.sample(map(chr, range(48, 57) + range(65, 90) + range(97, 122)), n))


def compress_n_save(f_name, content):
    # fgz = cStringIO.StringIO()
    # gzip_obj = gzip.GzipFile(filename=f_name, mode='wb', fileobj=fgz)
    # gzip_obj.write(content)
    # gzip_obj.close()
    # f = gzip.open(f_name, 'wb')
    # f.write(content)
    # f.close()
    with codecs.open(f_name, 'w', "utf-8") as f:
        f.write(content)

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)



class PerispiderSpider(scrapy.Spider):
    name = "perispider"
    allowed_domains = ["periscope.tv"]
    # start_urls = (
    #     'https://www.periscope.tv/',
    # )

#gen session id
#get auth url
#get channels
#get videos in the in the channel
# https://api.periscope.tv/api/v2/getUserBroadcastsPublic?user_id=14331212&all=true&session_id=1WTdge-UlaJKl4g1760nQwWRLijK0SLT3On3AScMNRw4EhjGhuB3Id0EEUGmqpRer6j4y4xcJExddaIznImBzklW89Zbbre2rJZYPDL3G5J9LhCH5
    
    def yield_ch_bcast_req(self, ch_id, auth_key):
        url = channel_bcast_url.substitute({'channel_id':ch_id})
        req = scrapy.Request(url)
        req.headers['Host'] = 'channels.periscope.tv'
        req.headers['Authorization'] = auth_key
        req.headers['Origin'] = 'https://www.periscope.tv'
        req.headers['Referer'] = 'https://www.periscope.tv/'
        req.callback = self.get_bcast_data
        req.meta['ch_id'] = ch_id
        return req



    def get_session_id(self):
        return '1'+ gen_random(43) + '-' +'_'   + gen_random(7) + '_'  + gen_random(55)

    def get_bcast_data(self, response):
        json_resp = json.loads(response.text)
        dm_dir =  LOG_FOLDER + response.meta['ch_id'] + '/' + 'all_broadcasts/' 
        ensure_dir(dm_dir)
        compress_n_save( dm_dir +  str(time.time()) + '.json', response.text)

        b_casts = json_resp['Broadcasts']
        b_casts_ids = [b['BID'] for b in b_casts]
        for b_cast_id in b_casts_ids:
            yield self.b_cast_dump( b_cast_id, LOG_FOLDER + response.meta['ch_id'] + '/')

    def b_cast_dump(self, bid, folder):
        url = bcast_url.substitute({'broadcast_id': bid})
        dm_dir =  folder + '/' + str(bid) +'/'
        ensure_dir(dm_dir)
        req = scrapy.Request(url)
        req.headers['Host'] = 'channels.periscope.tv'
        req.headers['Origin'] = 'https://www.periscope.tv'
        req.headers['Referer'] = 'https://www.periscope.tv/'
        req.callback = self.save_bcast_file
        req.meta['save_fold'] = dm_dir
        return req

    def save_bcast_file(self,response):
        # json_resp = json.loads(response.text)
        file_name = response.meta['save_fold'] +  str(time.time()) + '_'+ '.json'
        compress_n_save( file_name, response.text)

    def start_requests(self):
        session_id = self.get_session_id()
        url = "https://api.periscope.tv/api/v2/authorizeTokenPublic?service=channels&session_id="+session_id
        yield scrapy.Request( url, callback=self.start_crawl )

    def start_crawl(self, response):
        resp = json.loads(response.text)
        self.auth_key = resp['authorization_token']
        req = scrapy.Request(channel_url)
        req.headers['Authorization'] = self.auth_key
        req.meta['auth_key'] = self.auth_key
        req.callback = self.parse_channels
        yield req

    def parse_channels(self, response):
        chs = {}
        ch_bcasts = json.loads(response.text)
        dm_dir =  LOG_FOLDER + 'channel_dump_dat' + '/'
        ensure_dir(dm_dir)
        compress_n_save( dm_dir +  str(time.time()) + '.json', response.text)
        # dump to <time_channels> tar.gz
        b_channels = ch_bcasts['ChannelBroadcasts']
        for b_c in b_channels:
            channel = b_c['Channel']
            chs[channel['CID']]  = channel['Name']
            yield self.yield_ch_bcast_req(channel['CID'], response.meta['auth_key'])
        compress_n_save (LOG_FOLDER + str(time.time()) + '_channel_map.json' , str(chs))


 


# q = r(z)
# z = n(342)



# # LINKS
# {"authorization_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsInZlcnNpb24iOiIyIn0.eyJleHAiOjE0NzgzODk3NTcsInBlcm1zIjoxLCJ1c2VyX2lkIjoid2ViLTQwOGQ1YWRhLWQ2OWYtNGYxZS02YzBiLTQxMmFmNDc5NzE5YSJ9.pAnj9UhlI1BztJ3UMhNWbHOp4rzgbrKgtF0zxDYiOVk"}


# https://channels.periscope.tv/v1/top/channels/broadcasts?languages=end
# Authorization:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsInZlcnNpb24iOiIyIn0.eyJleHAiOjE0NzgzODk3NTcsInBlcm1zIjoxLCJ1c2VyX2lkIjoid2ViLTQwOGQ1YWRhLWQ2OWYtNGYxZS02YzBiLTQxMmFmNDc5NzE5YSJ9.pAnj9UhlI1BztJ3UMhNWbHOp4rzgbrKgtF0zxDYiOVk


# https://channels.periscope.tv/v1/channels/17200085734281664523/broadcasts?languages=en


# # Accept:*/*
# # Accept-Encoding:gzip, deflate, sdch, br
# # Accept-Language:en-GB,en-US;q=0.8,en;q=0.6
# # Authorization:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsInZlcnNpb24iOiIyIn0.eyJleHAiOjE0NzgzODk3NTcsInBlcm1zIjoxLCJ1c2VyX2lkIjoid2ViLTQwOGQ1YWRhLWQ2OWYtNGYxZS02YzBiLTQxMmFmNDc5NzE5YSJ9.pAnj9UhlI1BztJ3UMhNWbHOp4rzgbrKgtF0zxDYiOVk
# # Connection:keep-alive
# # Cookie:mp_2cfafc1b9adfdecf0504ffceb44e4e55_mixpanel=%7B%22distinct_id%22%3A%20%2215836a9a0a322-06f5888adb690d-2c004279-100200-15836a9a0a71f4%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D; mp_mixpanel__c=0
# # Host:channels.periscope.tv
# # Origin:https://www.periscope.tv
# # Referer:https://www.periscope.tv/
# # User-Agent:Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/53.0.2785.143 Chrome/53.0.2785.143 Safari/537.36
# # X-Periscope-User-Agent:PeriscopeWeb/App (ed2b6c951d84126824a7834a5c0d34c7f8bf07bf) Chromium/53.0.2785.143 (Ubuntu;Chromium)

# # Set-Cookie:user_id=Wf_CMjdkMTU3YTEzLTY5ODQtNGI0Mi02MDZjLTc1OWNmNjJiYWIyN1smjs8EP2cQO0u2666Xni5YiQIa8F4PzWb34lhO5Zh4; Path=/; Expires=Mon, 06 Nov 2017 02:00:18 GMT


# {"ChannelBroadcasts":[{"Channel":{"CID":"946499164167249963","Name":"Blizzcon 2016","Description":"World of Warcraft and esports fans gather in Anaheim, Calif. for the 10th annual Blizzcon from Nov. 4-6","UniversalLocales":null,"NLive":1,"NReplay":0,"Featured":false,"PublicTag":"","Slug":"blizzcon-2016","ThumbnailURLs":null,"CreatedAt":"2016-11-04T08:52:47.890061646-07:00","LastActivity":"2016-11-05T15:44:44.312008882-07:00","Type":2,"OwnerId":"1xnjrzoXMyjYD","NMember":5},
# "Broadcasts":[{"BID":"1MYxNOLqLWNKw","Featured":false},{"BID":"1dRKZRPeReQKB","Featured":false},{"BID":"1YqKDjXdzlaJV","Featured":false}]},{"Channel":{"CID":"15589369555740574731","Name":"#Travel","Description":"#travel #explore #teleport #sunset \u0026 more","UniversalLocales":null,"NLive":2,"NReplay":0,"Featured":false,"PublicTag":"#travel","Slug":"travel","ThumbnailURLs":null,"CreatedAt":"0001-01-01T00:00:00Z","LastActivity":"2016-11-05T15:40:20.629676464-07:00","Type":0,"OwnerId":"","NMember":0},
# "Broadcasts":[{"BID":"1zqJVNbLvgpJB","Featured":false},{"BID":"1RDGloRdpvoKL","Featured":false},{"BID":"1ypKdAXYDadGW","Featured":false}]},{"Channel":{"CID":"17200085734281664523","Name":"#Music","Description":"#music #unplugged #acoustic #piano \u0026 more","UniversalLocales":null,"NLive":73,"NReplay":0,"Featured":false,"PublicTag":"#music","Slug":"music","ThumbnailURLs":null,"CreatedAt":"0001-01-01T00:00:00Z","LastActivity":"2016-11-05T15:49:14.624539166-07:00","Type":0,"OwnerId":"","NMember":0},
# "Broadcasts":[{"BID":"1jMKgAYEAjkJL","Featured":false},{"BID":"1gqxvRqXbYexB","Featured":false},{"BID":"1mrGmAeRjdLGy","Featured":false}]},{"Channel":{"CID":"7142379078808778763","Name":"#Sports","Description":"#sports #fitness #trainer #yoga \u0026 more","UniversalLocales":null,"NLive":1,"NReplay":0,"Featured":false,"PublicTag":"#sports","Slug":"sports","ThumbnailURLs":null,"CreatedAt":"0001-01-01T00:00:00Z","LastActivity":"2016-11-05T15:35:35.802315444-07:00","Type":0,"OwnerId":"","NMember":0},"Broadcasts":[{"BID":"1zqJVNbLmpDJB","Featured":false},{"BID":"1yoKMDeRXjYxQ","Featured":false},{"BID":"1MYxNOLABVPKw","Featured":false}]},{"Channel":{"CID":"13246746514690616331","Name":"#News","Description":"Breaking news from around the world","UniversalLocales":null,"NLive":1,"NReplay":0,"Featured":false,"PublicTag":"#news","Slug":"news","ThumbnailURLs":null,"CreatedAt":"0001-01-01T00:00:00Z","LastActivity":"2016-11-05T14:35:16.494527734-07:00","Type":0,"OwnerId":"","NMember":0},"Broadcasts":[{"BID":"1OdJrNNPXPqJX","Featured":false},{"BID":"1kvKpqnWYzbGE","Featured":false},{"BID":"1mnxejVraRvKX","Featured":false}]},{"Channel":{"CID":"9567331147320489995","Name":"#Talk","Description":"#talk #AMA #podcast #radio \u0026 more","UniversalLocales":null,"NLive":2985,"NReplay":0,"Featured":false,"PublicTag":"#talk","Slug":"talk","ThumbnailURLs":null,"CreatedAt":"0001-01-01T00:00:00Z","LastActivity":"2016-11-05T15:49:18.258642896-07:00","Type":0,"OwnerId":"","NMember":0},"Broadcasts":[{"BID":"1MnxnXLZqbjGO","Featured":false},{"BID":"1lDxLmRAVgzKm","Featured":false},{"BID":"1mnGejVoZOZJX","Featured":false}]},{"Channel":{"CID":"13705792628168431627","Name":"#Inspire","Description":"#inspire #meditation #faith #pastor \u0026 more","UniversalLocales":null,"NLive":3,"NReplay":0,"Featured":false,"PublicTag":"#inspire","Slug":"inspire","ThumbnailURLs":null,"CreatedAt":"0001-01-01T00:00:00Z","LastActivity":"2016-11-05T15:32:00.714094315-07:00","Type":0,"OwnerId":"","NMember":0},"Broadcasts":[{"BID":"1zqJVNbLvgpJB","Featured":false},{"BID":"1eaKblPpNVvJX","Featured":false},{"BID":"1YqKDjXdmqAJV","Featured":false}]},{"Channel":{"CID":"6640913102874160139","Name":"#Art","Description":"#art #painting #pottery #museum \u0026 more","UniversalLocales":null,"NLive":9,"NReplay":0,"Featured":false,"PublicTag":"#art","Slug":"art","ThumbnailURLs":null,"CreatedAt":"0001-01-01T00:00:00Z","LastActivity":"2016-11-05T15:48:43.117617698-07:00","Type":0,"OwnerId":"","NMember":0},"Broadcasts":[{"BID":"1MnGnXLeMnwxO","Featured":false},{"BID":"1BRJjAEeAedGw","Featured":false},{"BID":"1kvKpqnaVLaGE","Featured":false}]},{"Channel":{"CID":"5863950602802984971","Name":"#Food","Description":"#food #cooking #hungry #kitchen \u0026 more","UniversalLocales":null,"NLive":53,"NReplay":0,"Featured":false,"PublicTag":"#food","Slug":"food","ThumbnailURLs":null,"CreatedAt":"0001-01-01T00:00:00Z","LastActivity":"2016-11-05T15:49:13.153620148-07:00","Type":0,"OwnerId":"","NMember":0},"Broadcasts":[{"BID":"1zqKVNbLWbLKB","Featured":false},{"BID":"1djGXEvnvVdJZ","Featured":false},{"BID":"1PlJQkZrkDMKE","Featured":false}]},{"Channel":{"CID":"14844418637156755467","Name":"#Teach","Description":"#teach #science #tech #DIY \u0026 more","UniversalLocales":null,"NLive":1,"NReplay":0,"Featured":false,"PublicTag":"#teach","Slug":"teach","ThumbnailURLs":null,"CreatedAt":"0001-01-01T00:00:00Z","LastActivity":"2016-11-05T15:35:35.775387775-07:00","Type":0,"OwnerId":"","NMember":0},"Broadcasts":[{"BID":"1nAKEkVQwRAJL","Featured":false},{"BID":"1ynJOkWVEeXJR","Featured":false},{"BID":"1mnxejVkvAZKX","Featured":false}]},{"Channel":{"CID":"8566640309232210955","Name":"#Comedy","Description":"#comedy #funny #standup #improv \u0026 more","UniversalLocales":null,"NLive":1,"NReplay":0,"Featured":false,"PublicTag":"#comedy","Slug":"comedy","ThumbnailURLs":null,"CreatedAt":"0001-01-01T00:00:00Z","LastActivity":"2016-11-05T15:35:27.350966111-07:00","Type":0,"OwnerId":"","NMember":0},"Broadcasts":[{"BID":"1YqKDjXQOpVJV","Featured":false},{"BID":"1lPKqYZnrvEKb","Featured":false},{"BID":"1vAGRXgNraZxl","Featured":false}]},{"Channel":{"CID":"4455903590047465515","Name":"Sporting Green","Description":"Pro teams and players from around the world.","UniversalLocales":null,"NLive":0,"NReplay":0,"Featured":false,"PublicTag":"","ThumbnailURLs":[{"url":"https://periscope-channel-thumbnails-live.s3-us-west-2.amazonaws.com/4455903590047465515/1472850084--9CWBmDP1Y4noAPikCc_Cm940HE%3D-128x128.png","ssl_url":"","width":128,"height":128},{"url":"https://periscope-channel-thumbnails-live.s3-us-west-2.amazonaws.com/4455903590047465515/1472850084--9CWBmDP1Y4noAPikCc_Cm940HE%3D-200x200.png","ssl_url":"","width":200,"height":200},{"url":"https://periscope-channel-thumbnails-live.s3-us-west-2.amazonaws.com/4455903590047465515/1472850084--9CWBmDP1Y4noAPikCc_Cm940HE%3D-400x400.png","ssl_url":"","width":400,"height":400}],"CreatedAt":"0001-01-01T00:00:00Z","LastActivity":"2016-11-05T15:03:28.646576663-07:00","Type":2,"OwnerId":"1xnjrzoXMyjYD","NMember":2},"Broadcasts":[{"BID":"1yoKMDeRXjYxQ","Featured":false},{"BID":"1YqKDjXdBeoJV","Featured":false},{"BID":"1mrxmAeRbkVxy","Featured":false}]},{"Channel":{"CID":"14089445545703682091","Name":"Guy Fawkes Night","Description":"The 5th of November is here! Commemorate the failed Gunpowder Plot of 1605 with bonfires and fireworks and learn about Guy Fawkes from broadcasters across the United Kingdom.","UniversalLocales":["en"],"NLive":0,"NReplay":0,"Featured":false,"PublicTag":"","Slug":"guy-fawkes","ThumbnailURLs":null,"CreatedAt":"2016-11-04T17:25:20.637904386-07:00","LastActivity":"2016-11-05T14:31:37.103046027-07:00","Type":2,"OwnerId":"1ayQVvPkxeZQp","NMember":2},"Broadcasts":[{"BID":"1eaKblRQRbXJX","Featured":false},{"BID":"1djGXEvAPQBJZ","Featured":false},{"BID":"1YqJDjXwQmzKV","Featured":false}]},{"Channel":{"CID":"11804227800496464939","Name":"Serenity Now","Description":"On Stress Awareness Day, take a deep breath with Global Meditation Scopers.","UniversalLocales":["en"],"NLive":0,"NReplay":0,"Featured":false,"PublicTag":"","Slug":"serenity-now","ThumbnailURLs":null,"CreatedAt":"2016-11-03T18:07:44.9073206-07:00","LastActivity":"2016-11-05T08:21:58.626006074-07:00","Type":2,"OwnerId":"8628405","NMember":3},"Broadcasts":[{"BID":"1MnxnXLzdOkGO","Featured":false},{"BID":"1ZkJznEgmEqJv","Featured":false},{"BID":"1rmxPbnwOZqGN","Featured":false}]},{"Channel":{"CID":"17758497017733312555","Name":"Selfie Masks!","Description":"Try out our new selfie mask feature, we'll be sharing some here. #govote","UniversalLocales":null,"NLive":0,"NReplay":0,"Featured":false,"PublicTag":"","Slug":"selfie-masks","ThumbnailURLs":null,"CreatedAt":"2016-11-04T09:25:37.860937008-07:00","LastActivity":"2016-11-05T07:16:32.391107456-07:00","Type":2,"OwnerId":"1xnjrzoXMyjYD","NMember":2},"Broadcasts":[{"BID":"1zqKVNbDMMpKB","Featured":false},{"BID":"1RDxloRVRNrJL","Featured":false},{"BID":"1yNGaAPrBqbGj","Featured":false}]},{"Channel":{"CID":"7662168117650874411","Name":"Mission: Space","Description":"Space stations, rocket launches and other Periscopes from the ongoing exploration of space.","UniversalLocales":null,"NLive":0,"NReplay":0,"Featured":false,"PublicTag":"","Slug":"mission-space","ThumbnailURLs":null,"CreatedAt":"2016-10-27T23:22:54.207634962-07:00","LastActivity":"2016-11-04T10:46:36.161871526-07:00","Type":2,"OwnerId":"1MWKwdlGlPYjb","NMember":5},"Broadcasts":[{"BID":"1YpJkAqzRpYKj","Featured":false},{"BID":"1gqGvRRlqXkGB","Featured":false},{"BID":"1kvKpqqogLQGE","Featured":false}]},{"Channel":{"CID":"16337926488905615403","Name":"Beyond the Spotlight","Description":"Get up close with some of the most interesting people in entertainment.","UniversalLocales":null,"NLive":0,"NReplay":0,"Featured":false,"PublicTag":"","Slug":"beyond-the-spotlight","ThumbnailURLs":null,"CreatedAt":"0001-01-01T00:00:00Z","LastActivity":"2016-11-05T14:35:17.238478179-07:00","Type":2,"OwnerId":"1xnjrzoXMyjYD","NMember":4},"Broadcasts":[{"BID":"1gqxvRqpwNaxB","Featured":false},{"BID":"1YpKkAdyLpVJj","Featured":false},{"BID":"1vAxRXdDwkYGl","Featured":false}]},{"Channel":{"CID":"285845037590510603","Name":"First Scope","Description":"Say hi and welcome people to their first scope.","UniversalLocales":null,"NLive":102,"NReplay":0,"Featured":false,"PublicTag":"","Slug":"first-scope","ThumbnailURLs":null,"CreatedAt":"0001-01-01T00:00:00Z","LastActivity":"2016-11-05T15:49:13.906436038-07:00","Type":0,"OwnerId":"","NMember":0},"Broadcasts":[{"BID":"1djGXEvnvVdJZ","Featured":false},{"BID":"1nAKEkVQkekJL","Featured":false},{"BID":"1vAxRXgEbRVGl","Featured":false}]}]}



# https://api.periscope.tv/api/v2/getBroadcastsPublic?broadcast_ids=1MYxNOLqLWNKw,1dRKZRPeReQKB,1YqKDjXdzlaJV,1zqJVNbLvgpJB,1RDGloRdpvoKL,1ypKdAXYDadGW,1jMKgAYEAjkJL,1gqxvRqXbYexB,1mrGmAeRjdLGy,1zqJVNbLmpDJB,1yoKMDeRXjYxQ,1MYxNOLABVPKw,1OdJrNNPXPqJX,1kvKpqnWYzbGE,1mnxejVraRvKX,1MnxnXLZqbjGO,1lDxLmRAVgzKm,1mnGejVoZOZJX,1zqJVNbLvgpJB,1eaKblPpNVvJX,1YqKDjXdmqAJV,1MnGnXLeMnwxO,1BRJjAEeAedGw,1kvKpqnaVLaGE,1zqKVNbLWbLKB,1djGXEvnvVdJZ,1PlJQkZrkDMKE,1nAKEkVQwRAJL,1ynJOkWVEeXJR,1mnxejVkvAZKX,1YqKDjXQOpVJV,1lPKqYZnrvEKb,1vAGRXgNraZxl,1yoKMDeRXjYxQ,1YqKDjXdBeoJV,1mrxmAeRbkVxy,1eaKblRQRbXJX,1djGXEvAPQBJZ,1YqJDjXwQmzKV,1MnxnXLzdOkGO,1ZkJznEgmEqJv,1rmxPbnwOZqGN,1zqKVNbDMMpKB,1RDxloRVRNrJL,1yNGaAPrBqbGj,1YpJkAqzRpYKj,1gqGvRRlqXkGB,1kvKpqqogLQGE,1gqxvRqpwNaxB,1YpKkAdyLpVJj,1vAxRXdDwkYGl,1djGXEvnvVdJZ,1nAKEkVQkekJL,1vAxRXgEbRVGl



# # Accept:*/*
# # Accept-Encoding:gzip, deflate, sdch, br
# # Accept-Language:en-GB,en-US;q=0.8,en;q=0.6
# # Authorization:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsInZlcnNpb24iOiIyIn0.eyJleHAiOjE0NzgzODk3NTcsInBlcm1zIjoxLCJ1c2VyX2lkIjoid2ViLTQwOGQ1YWRhLWQ2OWYtNGYxZS02YzBiLTQxMmFmNDc5NzE5YSJ9.pAnj9UhlI1BztJ3UMhNWbHOp4rzgbrKgtF0zxDYiOVk
# # Connection:keep-alive
# # Cookie:mp_2cfafc1b9adfdecf0504ffceb44e4e55_mixpanel=%7B%22distinct_id%22%3A%20%2215836a9a0a322-06f5888adb690d-2c004279-100200-15836a9a0a71f4%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%7D; mp_mixpanel__c=0
# # Host:channels.periscope.tv
# # Origin:https://www.periscope.tv
# # Referer:https://www.periscope.tv/
# # User-Agent:Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/53.0.2785.143 Chrome/53.0.2785.143 Safari/537.36
# # X-Periscope-User-Agent:PeriscopeWeb/App (ed2b6c951d84126824a7834a5c0d34c7f8bf07bf) Chromium/53.0.2785.143 (Ubuntu;Chromium)



# {"user":
# {"class_name":"User","id":"9675947","created_at":"2015-07-30T16:48:16.988300967-07:00","is_beta_user":false,"is_employee":false,"is_twitter_verified":true,"twitter_screen_name":"YFNLUCCI","username":"YFNLUCCI","display_name":"IG: YFNLUCCI","description":"So much money on my mind dats all i remember","profile_image_urls":[{"url":"http://pbs.twimg.com/profile_images/698306116359475202/TVHUznEO_reasonably_small.jpg","ssl_url":"https://pbs.twimg.com/profile_images/698306116359475202/TVHUznEO_reasonably_small.jpg","width":128,"height":128},{"url":"http://pbs.twimg.com/profile_images/698306116359475202/TVHUznEO_200x200.jpg","ssl_url":"https://pbs.twimg.com/profile_images/698306116359475202/TVHUznEO_200x200.jpg","width":200,"height":200},{"url":"http://pbs.twimg.com/profile_images/698306116359475202/TVHUznEO_400x400.jpg","ssl_url":"https://pbs.twimg.com/profile_images/698306116359475202/TVHUznEO_400x400.jpg","width":400,"height":400}],"twitter_id":"407329869","initials":"","n_followers":41053,"n_following":56,"n_hearts":4446276},"broadcast":{"class_name":"Broadcast","id":"1OyKAOoplgOJb","created_at":"2016-11-05T17:45:57.474389214-07:00","updated_at":"2016-11-05T18:00:19.581489054-07:00","user_id":"9675947","user_display_name":"IG: YFNLUCCI","username":"YFNLUCCI","twitter_username":"YFNLUCCI","profile_image_url":"http://pbs.twimg.com/profile_images/698306116359475202/TVHUznEO_reasonably_small.jpg","state":"RUNNING","is_locked":false,"friend_chat":false,"language":"en","start":"2016-11-05T17:45:59.489760062-07:00","ping":"2016-11-05T18:00:18.114960478-07:00","has_moderation":true,"has_location":false,"city":"","country":"","country_state":"","iso_code":"","ip_lat":0,"ip_lng":0,"width":320,"height":568,"camera_rotation":5,"image_url":"https://tn.periscope.tv/uA4Futxqr2asavHk5qHvf5l2PQIOVOHsLbm6B1jzmXAKD86MabSzNBTXvKOwDMqPgTdYEG-1-lbBYu2OKw17PA/chunk_282.jpg?Expires=1793754019\u0026Signature=fNGDEmUZ7XjpDktdR1OeuTX~F3-DvqpEQ3AduEaVIpz3ESrOvHjb7anLfUg41chATH69~GgaXeoircjcaK8-uvNzqJPbiCEorLPTM5fNnMoETPFW-XEBj5VsdSPLy5FQK71Nwz~Xos-66qUOjNQh2WqqFKvLF9TlKc2t5tnx4yHAhPYCRYo-mg~b3d2rXSsHt5~VKg7-RCnKKess6x~xrIzJta0APzijnoE65CLi4mze0MTCLKjwE4NsbSpL4QB6YARuVseTyl7GRdKC-CvyRhYQOANrQr1V3npHcIBogus1jGF3w2OPMNJE3ZdhPg0UuYSMImwaovmPhQ21jBSJpQ__\u0026Key-Pair-Id=APKAIHCXHHQVRTVSFRWQ","image_url_small":"https://tn.periscope.tv/uA4Futxqr2asavHk5qHvf5l2PQIOVOHsLbm6B1jzmXAKD86MabSzNBTXvKOwDMqPgTdYEG-1-lbBYu2OKw17PA/chunk_282_thumb_128.jpg?Expires=1793754019\u0026Signature=GmaHo2s0BHfJkS30qnzkGIZEFe-0h4xVYDopLA31IuPn178cxCMT~yHYri4EsE~UGmIeuw3ch1YaFXDW8OMRk2NWBJbEWz5R14WgDcs7ukfn4w6lPSB8-~pbiYTX5eruYeNpn1tRdBIHtbXFZU0U2xFekXdqRc6r5tp1Nf0jNQ2OY1ZY6iFsMnOg~O6wrwYjGc-3LevVFrLIjzCr5QLeFcO1-U77ANrjiplrarsfHr6~3-KgEoLte1kN88IuNf0Fz5EB1cZ5-tQT91tcdvl-jfJ1mqMg4w5b0H~lbJCoECd3K10vxCLRknnsx~l4~Oy8MdH4f2mUbA7yc3d2Tn0biA__\u0026Key-Pair-Id=APKAIHCXHHQVRTVSFRWQ","status":"","available_for_replay":true,"featured":false,"expiration":-1},"n_watching":110,"n_watched":1519}
