# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class Video_stream(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    level = scrapy.Field()
    r_time = scrapy.Field()
    video_id = scrapy.Field()
    lat = scrapy.Field()
    lon = scrapy.Field()
    name = scrapy.Field()
    start_time = scrapy.Field()
    preview_image = scrapy.Field()
    viewer_count = scrapy.Field()
    formatted_count = scrapy.Field()
    publisher_category = scrapy.Field()
    profile_picture = scrapy.Field()
    v_width = scrapy.Field()
    v_height = scrapy.Field()
    message = scrapy.Field()
    message_ranges = scrapy.Field()
    u_profile = scrapy.Field()
    lid = scrapy.Field()
    # image_urls = scrapy.Field()
    # images = scrapy.Field()
    

class Video_interaction(scrapy.Item):
    r_time = scrapy.Field()
    video_id = scrapy.Field()
    watched_at =  scrapy.Field()

class Video_metadata(scrapy.Item):
    r_time = scrapy.Field()
    video_id = scrapy.Field()
    aspect_ratio = scrapy.Field()
    dash_manifest = scrapy.Field()
    dash_prefetched_representation_ids = scrapy.Field()
    hd_src = scrapy.Field()
    is_hds = scrapy.Field()
    is_live_stream = scrapy.Field()
    live_routing_token = scrapy.Field()
    player_version_overwrite = scrapy.Field()
    projection = scrapy.Field()
    rotation = scrapy.Field()
    sd_src = scrapy.Field()
    stream_type = scrapy.Field()
    subtitles_src = scrapy.Field()



