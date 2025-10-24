import requests
from fake_useragent import UserAgent
from scrapy import signals
from scrapy.http.response.html import TextResponse


class ReviewAvSpiderMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        pass

    async def process_start(self, start):
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class ReviewAvDownloaderMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # 处理parse发送过来的请求
        if request.meta.get("use_requests"):
            headers = {
                "User-Agent": UserAgent(browsers="Chrome").random,
                "referer": "https://music.163.com/" if request.meta.get("cur_count") == 0
                else f"https://music.163.com/song?id={request.meta.get("id")}",
                # referer：第一页评论是"https://music.163.com/"后面的是"https://music.163.com/song?id=XXX"
                "content-type": "application/x-www-form-urlencoded",
            }
            # time.sleep(2)  # 限制爬虫效率
            resp = requests.post(
                url=request.meta.get("get_comments_url"),
                params=request.meta.get("params"),  # 处理Query String Parameters
                data=request.meta.get("post_data"),  # 处理Form Data
                headers=headers,
            )
            # print(resp.text)

            return TextResponse(
                url=resp.url,
                status=resp.status_code,
                body=resp.content,
                encoding="utf-8",
                request=request,
            )

        return None

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
