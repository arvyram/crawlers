import requests
import json
import random
import os, time
import codecs, gzip, math
import sys


class Utils:
    @classmethod
    def check_create(cls, dir_name):
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

    @classmethod
    def compress_utf8_file(cls, fullpath, delete_original = True):
        with codecs.open(fullpath, 'r', 'utf-8') as fin:
            with gzip.open(fullpath  +'.gz', 'wb') as fout:
                for line in fin:
                    fout.write(unicode(line).encode('utf-8'))

        if delete_original:
            os.remove(fullpath)
    @classmethod
    def download_video(cls, url, f_name):
        r = requests.get(url, stream = True)
        with open(f_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
        return f_name


class User:
    def search_user(self, u_name, uf_count='default'):
        url = "https://www.instagram.com/web/search/topsearch/"
        params = {}
        params['context'] = 'blended'
        params['query'] = u_name
        params['rank_token'] = random.random()
        if not uf_count is 'default':
            params['count'] = uf_count

        usersearch_header = {
            'Host': 'www.instagram.com',
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:50.0) Gecko/20100101 Firefox/50.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
        # 'Accept-Encoding': 'gzip, deflate, br'.
            'X-Requested-With': 'XMLHttpRequest',
            # 'Referer': 'https://www.instagram.com/' + u_name + '/',
            # 'Cookie': 'csrftoken=%s; mid=%s; ig_pr=1; ig_vw=1301' % ( csrf_token, mid ),
            'DNT': '1',
            'Connection': 'keep-alive',
           'Upgrade-Insecure-Requests': '1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }

        client = requests.session()
        return client.get(url, headers = usersearch_header, params = params)

    def parse_and_save(self, resp_text, dest_folder):
        Utils.check_create(dest_folder)
        dest_file = dest_folder + '/'+ 'search_data.json'
        json_resp = json.loads(resp_text)
        with open(dest_file, 'w') as outfile:
            json.dump(json_resp, outfile)
        Utils.compress_utf8_file(dest_file)
        return json_resp['users']

    def store_user_data( self, dest_folder, user_m_data ):
        au_name = user_m_data[ 'user' ][ 'username' ]
        au_pk = user_m_data[ 'user' ][ 'pk' ]
        u_folder = dest_folder + '/' + str(au_pk) + '_' + au_name  + '/'
        Utils.check_create(u_folder)
        u_file = u_folder + 'user_data.json'
        with open(u_file, 'w') as outfile:
            json.dump(user_m_data, outfile)
        Utils.compress_utf8_file(u_file)
        return u_folder

    def get_user_init_data( self, username, csrf_token, sessionid ):
        url = "https://www.instagram.com/" + username

        params = { '__a': 1 }
        userdata_header = {
            'Host': 'www.instagram.com',
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:50.0) Gecko/20100101 Firefox/50.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
        # 'Accept-Encoding': 'gzip, deflate, br'.
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.instagram.com/' + username + '/',
            'Cookie': 'csrftoken=%s; sessionid=%s; ig_pr=1; ig_vw=1301' % ( csrf_token, sessionid ),
            'DNT': '1',
            'Connection': 'keep-alive',
           'Upgrade-Insecure-Requests': '1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }

        return requests.get(url, headers = userdata_header, params = params)

    def get_user_full_data(self, username, user_id, media_after, count, csrf_token, sessionid, mid):
        query_id = open('query_id.txt', 'r').read()
        payload  = {"q":"ig_user(%s) \
                        { media.after(%s, %s) \
                        {  count, \
                         nodes {  \
                           caption,  \
                             code,  \
                               comments \
                               {      count    }\
                               ,    comments_disabled,  \
                                 date,    \
                                 dimensions {      height,      width    },  \
                                   display_src,  \
                                  id,    \
                                  is_video,    \
                                  likes {      count    },    \
                                  owner {      id    },    \
                                  thumbnail_src,    \
                                  video_views  },\
                              page_info} \
                              }" % ( user_id, media_after, count),
                          "ref":"users::show",
                          "query_id": query_id
                    }
        query_id = str(int(query_id) + 10)
        open('query_id.txt', 'w').write(query_id)

        q_header = {
            'Host': 'www.instagram.com',
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:50.0) Gecko/20100101 Firefox/50.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
        # 'Accept-Encoding': 'gzip, deflate, br'.
        'X-CSRFToken': csrf_token,
    'X-Instagram-AJAX': '1',
'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.instagram.com/' + username + '/',
            'Cookie': 'csrftoken=%s; sessionid=%s; mid=%s; ig_pr=1; s_network=; ig_vw=1301' % ( csrf_token, sessionid, mid ),
            'DNT': '1',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }

        return requests.post("https://www.instagram.com/query/", data=payload, headers=q_header)

    def store_user_full_data( self, u_folder, user_f_data ):
        u_file = u_folder + 'user_full_data.json'
        with open(u_file, 'w') as outfile:
            json.dump(user_f_data, outfile)
        Utils.compress_utf8_file(u_file)
        return u_folder

class Post:
    def get_post( self, post_id, username, csrf_token, sessionid, mid ):
        url = 'https://www.instagram.com/p/%s/' % post_id
        params = {
            'taken-by' : username,
            '__a' : 1
        }


        q_header = {
            'Host': 'www.instagram.com',
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:50.0) Gecko/20100101 Firefox/50.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://www.instagram.com/' + username + '/',
            'Cookie': 'csrftoken=%s; sessionid=%s; mid=%s; ig_pr=1; s_network=;' % ( csrf_token, sessionid, mid ),
            'DNT': '1',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }


        return requests.get(url, headers = q_header, params = params)

def crawlUser(uname, destfolder , uSearchCount = 10 , postcount = 100, vidDownloadFlag = True , chunkSize=12):

    ## input params ##
    u_name = uname
    dest_folder = destfolder + "/" +  u_name
    uf_count = uSearchCount #'default' ; no of users searched from the query
    post_count = postcount #'default'; 0 to pull posts; 10% to pull recent 10% of videos
    vid_dwld_enabled = vidDownloadFlag
    d_c = chunkSize # pagination; max = 128

    if type(post_count) == str and '%' in post_count:
        thresh_posts = 12 #min videos to fetch

    ##################


    u = User()
    user_search_resp = u.search_user(u_name, uf_count=uf_count)
    csrf_token = user_search_resp.cookies['csrftoken']
    sessionid = user_search_resp.cookies['sessionid']
    searched_users = u.parse_and_save(user_search_resp.text, dest_folder)
    if searched_users:
        for user_data in searched_users:
            u_folder = u.store_user_data( dest_folder, user_data )
            u_data = user_data['user']
            if not u_data['is_private']:

                username =  u_data['username']
                user_init_resp = u.get_user_init_data(username, csrf_token, sessionid )

                user_init_data = json.loads(user_init_resp.text)

                csrf_token = user_init_resp.cookies.get('csrftoken', csrf_token)

                sessionid = user_init_resp.cookies.get('sessionid', sessionid)
                mid = user_init_resp.cookies['mid']
                if not post_count == 'default':
                    media_data = user_init_data['user']['media']
                    if type(post_count) == str and '%' in post_count:
                        post_count = int(post_count.split('%')[0].strip())
                        post_count = math.ceil(int(media_data['count'])   * (post_count) /100.0)
                        if post_count < thresh_posts:
                            post_count = thresh_posts



                    if post_count > int(media_data['count']) or post_count==0:
                        post_count = media_data['count']

                    post_counts = [d_c] * int(math.ceil(post_count*1.0/d_c))

                    user_id = user_init_data['user']['id']
                    media_after = media_data['page_info']['end_cursor']
                    has_next = media_data['page_info']['has_next_page']
                    for pg_cnt, post_count in enumerate(post_counts):
                        if has_next:
                            user_addl_data = u.get_user_full_data(username,user_id, media_after, post_count, csrf_token, sessionid, mid) #self, user_id, media_after, count, csrf_token, sessionid
                            user_addl_data_j = json.loads(user_addl_data.text)
                            addl_med_data = user_addl_data_j['media']
                            user_init_data['user']['media']['nodes'].extend( addl_med_data['nodes'] )
                            media_after = addl_med_data['page_info']['end_cursor']
                            has_next = addl_med_data['page_info']['has_next_page']
                            user_init_data['user']['media']['page_info' + '_' + str(pg_cnt+1)] = addl_med_data['page_info']
                            time.sleep(0.1)
                user_full_data = user_init_data
                u.store_user_full_data(u_folder, user_full_data)



                ########crawl each node#####################
                post = Post()
                for node in user_full_data['user']['media']['nodes']:
                    pst_dat = post.get_post( node['code'], username, csrf_token, sessionid, mid  )
                    pst_json = json.loads(pst_dat.text)
                    p_folder = u_folder + '/' + node['code']
                    Utils.check_create(p_folder)
                    p_file = p_folder +'/' + 'post_full_data.json'
                    with open(p_file, 'w') as outfile:
                        json.dump(pst_json, outfile)
                    Utils.compress_utf8_file(p_file)
                    if vid_dwld_enabled:

                        if pst_json['media']['is_video']:
                            vid_link = pst_json['media']['video_url']
                            v_file = p_folder +'/' + vid_link.split('/')[-1]
                            Utils.download_video (vid_link, v_file )


if __name__ == '__main__':
    userFile = sys.argv[1]
    destFolder = sys.argv[2]
    if os.path.exists(userFile) and os.path.exists(destFolder):
        f = open(userFile, 'rb' )
        names = f.readlines()
        for name in names:
            crawlUser(name.strip() , destFolder )


