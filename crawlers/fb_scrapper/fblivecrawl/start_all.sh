
bash crawl_fb_live.sh 0 &
sleep 1
bash crawl_fb_live.sh 1 &
sleep 1
bash crawl_fb_live.sh 2 &
sleep 1

bash mon_post_live.sh 0 &
sleep 1
bash mon_post_live.sh 1 &
sleep 1
bash mon_post_live.sh 2 &
sleep 1

