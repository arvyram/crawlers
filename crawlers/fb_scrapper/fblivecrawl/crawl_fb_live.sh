while true
do
	scrapy crawl fbspider -a level=${1}
	sleep 4
done