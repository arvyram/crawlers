
echo "starting crawl"
bash crawl_fb_live.sh 0 &
sleep 1
bash crawl_fb_live.sh 1 &
sleep 1
bash crawl_fb_live.sh 2 &
sleep 1

sleep 10
echo "starting monitor"


#while [ "$d" != `date --date="-1 week" +"%d-%b-%Y"` ]
#do
while true
do
  d=`date +"%d-%b-%y"`
  while [ "$d" != `date --date="-6 days" +"%d-%b-%y"` ]
  do
      bash mon_post_live.sh ${d} &
      d=$(date -d "$d - 1 day" +"%d-%b-%y")
  done
  bash mon_post_live.sh ${d}
  sleep 15
done
~     




