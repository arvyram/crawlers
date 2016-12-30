import requests
import json
import random
import os, time
import codecs, gzip, math
import sys
import cPickle as pickle
from crawler import Utils
from crawler import User
from crawler import Post

dataRoot = "/datasets/sagarj/instaPop/"
tracker = "/datasets/sagarj/instaPopTrackedVids"
global_searched_data = dataRoot + "search_data.json.gz"

def readGzipJSON(filePath):
    with gzip.open(filePath, 'rb') as f:
        file_content = f.read()
    data = json.loads(file_content)
    return data

def getFileList(dataRoot):
    users = os.listdir(dataRoot)
    allUsers = dict()
    for user in users:
        if user.split('.')[-1] == 'gz':
            continue
        directory = dataRoot + user + "/"
        subs = os.listdir(directory)
        for s in subs:
            if s.split('.')[-1] == 'gz':
                continue
            allUsers[s] = dict()
            allUsers[s]['Posts'] = dict()
            userDir = directory + s + "/"
            posts = os.listdir(userDir)
            for post in posts: 
                if post == "user_full_data.json.gz":
                    allUsers[s]['Meta'] = dict()
                    json_file = userDir + post
                    allUsers[s]['Meta'] = readGzipJSON(json_file)
                else:
                    if post.split('.')[-1] == 'gz':
                        continue
                    allUsers[s]['Posts'][post] = dict()
                    postDir = userDir + post + "/"
                    postFiles = os.listdir(postDir)
                    for f in postFiles:
                        if f == "post_full_data.json.gz":
                            json_file = postDir + f
                            allUsers[s]['Posts'][post]['Meta'] = dict()
                            allUsers[s]['Posts'][post]['Meta'] = readGzipJSON(json_file)
                        else:
                            media_file = postDir + f
                            allUsers[s]['Posts'][post]['path'] = media_file
    return allUsers

def getPrecachedPosts(trackerDir):
    postList = os.listdir(trackerDir)
    return postList

def downloadPost(downloadDir,postCode, username , csrf_token , sessionid , mid ):
    post = Post()
    pst_dat = post.get_post( postCode, username, csrf_token, sessionid, mid  )
    pst_json = json.loads(pst_dat.text)
    p_folder = downloadDir + '/' + postCode
    Utils.check_create(p_folder)
    p_file = p_folder +'/' + 'post_full_data.json'
    with open(p_file, 'w') as outfile:
        json.dump(pst_json, outfile)
    try:
        Utils.compress_utf8_file(p_file)
    except IOError:
        print "JSON dump failed, not compressing"
    
    
def getPosts(allUsers):
    uf_count = 100
    username = "kingbach"
    u = User()
    user_search_resp = u.search_user(username, uf_count=uf_count)
    
    print user_search_resp
    sessionid = ""
    csrf_token = user_search_resp.cookies['csrftoken']
    mid = user_search_resp.cookies['mid']
    user_init_resp = u.get_user_init_data(username, csrf_token, sessionid )
    
    for u in allUsers:
        if 'Meta' in allUsers[u]:
            username = allUsers[u]['Meta']['user']['username']
            print "tracking posts by %s"%u
            for p in allUsers[u]['Posts']:
                if allUsers[u]['Posts'][p]['Meta']['media']['is_video']:
                    print "Downloading recent meta for Post %s" %p
                    try:
                        downloadedPosts = getPrecachedPosts(tracker)
                        if p in downloadedPosts:
                            print "This post is already tracked in this folder!!"
                            continue
                        downloadPost(tracker , p , username , csrf_token, sessionid , mid)
                        time.sleep(2)
                    except ValueError:
                        print "Had exception in decoding JSON!!! "


                
                
if __name__ == "__main__":
    allUsers = getFileList(dataRoot)
    getPosts(allUsers)
    
    
