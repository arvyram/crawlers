
kill -9 `ps aux | grep "scrapy crawl perispider" | awk {'print $2'}`

