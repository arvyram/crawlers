kill -9 `ps aux | grep "bash crawl_fb_live.sh" | awk {'print $2'}`
kill -9 `ps aux | grep "bash mon_post_live.sh" | awk {'print $2'}`