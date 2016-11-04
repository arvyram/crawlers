while true
do
	scrapy crawl fbvidspider -a level=${1}
	sleep 2
done