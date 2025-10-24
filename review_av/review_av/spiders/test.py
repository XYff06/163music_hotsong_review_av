import base64
import json
import warnings

import execjs
import redis
import scrapy
from Crypto.Cipher import AES
from fake_useragent import UserAgent
from scrapy import signals
from scrapy.exceptions import ScrapyDeprecationWarning

from review_av.items import ReviewAvItem


class TestSpider(scrapy.Spider):
    name = "test"
    # allowed_domains = ["music.163.com"]
    start_urls = ["https://music.163.com/discover/toplist"]  # hot_song_list_url

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        s = cls(*args, **kwargs)
        s._set_crawler(crawler)
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    def spider_opened(self, spider):
        # 连接Redis
        self.r = redis.StrictRedis(
            host='127.0.0.1',
            port=6379,
            password=None,  # 如果设置了密码，则写上，如password="yourpassword"
            db=0,
            decode_responses=True  # 返回字符串而不是字节
        )
        # 测试连接
        print(f"PING：{self.r.ping()}")
        pass

    def spider_closed(self, spider):
        self.r.save()
        self.r.close()
        pass

    def start_requests(self):
        warnings.warn(
            (
                "The Spider.start_requests() method is deprecated, use "
                "Spider.start() instead. If you are calling "
                "super().start_requests() from a Spider.start() override, "
                "iterate super().start() instead."
            ),
            ScrapyDeprecationWarning,
            stacklevel=2,
        )
        if not self.start_urls and hasattr(self, "start_url"):
            raise AttributeError(
                "Crawling could not start: 'start_urls' not found "
                "or empty (but found 'start_url' attribute instead, "
                "did you miss an 's'?)"
            )
        for url in self.start_urls:
            headers = {
                "User-Agent": UserAgent(browsers="Chrome").random,
            }
            """设置随机UA"""

            formdata = {
                "id": "3778678",
            }
            """通过formdata里的id来识别要爬取的页面，可以视情况更改"""

            # 发送get请求，带有Query String Parameters，不能过滤，FormRequest+formdata可以实现
            yield scrapy.FormRequest(url=url, method="GET", headers=headers, formdata=formdata, dont_filter=True)

    def parse(self, response, **kwargs):
        """
        # 1. 获取网易云音乐的热歌榜里的音乐链接、标题和id
        :param response:
        :param kwargs:
        :return:
        """

        get_comments_url = "https://music.163.com/weapi/comment/resource/comments/get"
        """获得评论的url"""
        li_list = response.xpath("//ul[@class='f-hide']/li")

        i = 0
        """用于测试的时候限制爬虫的歌曲数量"""

        for li in li_list:
            href = response.urljoin(li.xpath("./a/@href").extract_first())
            """音乐的网址"""

            title = li.xpath("./a/text()").extract_first()
            """音乐的名字"""

            id = href.split("id=")[-1]
            """音乐的id，用于后面获取歌曲对应评论的关键信息"""

            # print(href, title, id)
            csrf_token = "48818d4e2467d2d34b28d7d7a3f15159"
            """用户标识码"""

            params = {
                "csrf_token": csrf_token
            }
            """发送post请求时，Query String Parameters里的参数"""

            get_params, get_encSecKey = self.get_params_and_encSecKey(
                csrf_token=csrf_token,
                cursor=-1,
                offset=0,
                orderType=1,
                pageNo=1,
                pageSize=20,
                id=id
                # id=1896022869  # 测试能否抵达最后一页的评论以及是否会正常停止爬取时启用
            )
            post_data = {
                "params": get_params,
                "encSecKey": get_encSecKey
            }
            """发送post请求时，Form Data里的参数"""

            # 发送新的请求，去获得评论，由于url相同，所以不能过滤，由于使用scrapy.Request发送请求会出现问题，所以使用requests发送请求，需要更改并启用下载器中间件
            """
            yield scrapy.Request(
                url=get_comments_url + "?" + urlencode(params),
                method="POST",
                body=urlencode(post_data),
                callback=self.parse_1,
                meta={
                    "href": href,
                    "title": title,
                    "id": id,
                },
                dont_filter=True,
            )
            """

            yield scrapy.Request(
                url=get_comments_url,
                meta={
                    "href": href,
                    "title": title,
                    "id": id,
                    # "id": 1896022869,  # 测试能否抵达最后一页的评论以及是否会正常停止爬取时启用
                    "csrf_token": csrf_token,
                    "params": params,
                    "post_data": post_data,
                    "get_comments_url": get_comments_url,
                    "cur_count": 0,
                    "use_requests": True
                },
                callback=self.parse_1,
                dont_filter=True,
            )

            i += 1  # 测试时放开
            if i > 2:
                break
            # break  # 测试时放开
        pass

    def parse_1(self, response, **kwargs):
        """
        # 2. 获取网易云音乐的热歌榜里的每一首歌曲里的评论、链接、标题和id，然后交给管道进行处理，然后继续发送请求，新的请求需要修改cursor、orderType、pageNo、pageSize
        :param response:
        :param kwargs:
        :return:
        """

        # print(response.text)
        # response.url：https://music.163.com/weapi/comment/resource/comments/get?csrf_token=48818d4e2467d2d34b28d7d7a3f15159
        # print(response.url)
        # response.request.url：https://music.163.com/weapi/comment/resource/comments/get
        # print(response.request.url)
        # print(response.request.meta)
        # print(response.json())  # 评论(需要处理)

        totalCount = response.json()["data"]["totalCount"]

        def set_item(s, item, flag):
            item["href"] = response.request.meta.get("href")
            item["title"] = response.request.meta.get("title").replace("\n", "").replace(",", "，")
            item["id"] = response.request.meta.get("id")
            item["userId"] = s["user"]["userId"]
            item["nickname"] = s["user"]["nickname"].replace("\n", "").replace(",", "，")
            item["commentId"] = s["commentId"]
            item["content"] = s["content"].replace("\n", "").replace(",", "，")
            item["time"] = s["time"]
            item["likedCount"] = s["likedCount"]
            item["replyCount"] = s["replyCount"]
            item["parentCommentId"] = s["parentCommentId"]
            item["ext_dislike"] = s["extInfo"].get("statistics").get("ext_dislike") \
                if s["extInfo"].get("statistics") else 0
            item["is_hot_comment"] = "YES" if flag else "NO"

            dic_base = {
                "href": item["href"],  # 一般不变
                "title": item["title"],  # 一般不变
                "id": item["id"],  # 一般不变
                "userId": item["userId"],  # 一般不变
                # "nickname": item["nickname"],
                "commentId": item["commentId"],  # 一般不变
                "content": item["content"],  # 一般不变
                "time": item["time"],  # 一般不变
                # "likedCount": item["likedCount"],
                # "replyCount": item["replyCount"],
                "parentCommentId": item["parentCommentId"],  # 一般不变
                # "ext_dislike": item["ext_dislike"],
                "is_hot_comment": item["is_hot_comment"],
            }
            return item, dic_base

        hot_comments = response.json()["data"].get("hotComments")
        if hot_comments:
            for hot_comment in hot_comments:
                hot_comment_item = ReviewAvItem()
                hot_comment_item, dic = set_item(s=hot_comment, item=hot_comment_item, flag=True)

                if self.r.sismember(f"music_163:{response.request.meta.get("id")}:hot_comments:", json.dumps(dic)):
                    continue

                self.r.sadd(f"music_163:{response.request.meta.get("id")}:hot_comments:", json.dumps(dic))
                yield hot_comment_item

        comments = response.json()["data"]["comments"]
        for comment in comments:
            # 如果数据已经存在了且数据量正确，那么可以中断了
            if totalCount == self.r.scard(f"music_163:{response.request.meta.get("id")}:comments:"):
                return
            else:
                comment_item = ReviewAvItem()
                comment_item, dic = set_item(s=comment, item=comment_item, flag=False)

                # 如果数据已经存在了但数据量不正确，那么continue
                if self.r.sismember(f"music_163:{response.request.meta.get("id")}:comments:", json.dumps(dic)):
                    continue

                self.r.sadd(f"music_163:{response.request.meta.get("id")}:comments:", json.dumps(dic))
                yield comment_item

        cursor = response.json()["data"]["cursor"]
        cur_count = response.request.meta.get("cur_count") + 20

        if (totalCount - cur_count) <= 0:
            return

        csrf_token = response.request.meta.get("csrf_token")
        """用户标识码"""

        params = {
            "csrf_token": csrf_token
        }
        """发送post请求时，Query String Parameters里的参数"""

        get_params, get_encSecKey = self.get_params_and_encSecKey(
            csrf_token=csrf_token,
            cursor=0 if (totalCount - cur_count) <= 20 else cursor,
            offset=0,
            orderType=0 if (totalCount - cur_count) <= 20 else 1,
            pageNo=(cur_count // 20) + 1,
            pageSize=(totalCount - cur_count) % 20 if (totalCount - cur_count) <= 20 else 20,
            id=response.request.meta.get("id")
        )
        post_data = {
            "params": get_params,
            "encSecKey": get_encSecKey
        }
        """发送post请求时，Form Data里的参数"""

        yield scrapy.Request(
            url=response.request.meta.get("get_comments_url"),
            meta={
                "href": response.request.meta.get("href"),
                "title": response.request.meta.get("title"),
                "id": response.request.meta.get("id"),
                "csrf_token": response.request.meta.get("csrf_token"),
                "params": params,
                "post_data": post_data,
                "get_comments_url": response.request.meta.get("get_comments_url"),
                "cur_count": cur_count,
                "use_requests": True
            },
            callback=self.parse_1,
            dont_filter=True,
        )

    def get_params_and_encSecKey(self, csrf_token, cursor, offset, orderType, pageNo, pageSize, id):
        """
        获得Form Data里的params和encSecKey
        :param csrf_token: 用户识别码
        :param cursor: 当前歌曲的当前评论的位置
        :param id: 歌曲识别码
        :return: params, encSecKey
        """

        # print("正在生成params和encSecKey！！！")

        """
        Form Data里的params和encSecKey生成的来源
        var bLa9R = window.asrsea(JSON.stringify(i1x), bvq7j(["流泪", "强"]), bvq7j(zK7D.md), bvq7j(["爱心", "女孩", "惊恐", "大笑"]));
        e1x.data = j1x.cr2x({
            params: bLa9R.encText,
            encSecKey: bLa9R.encSecKey
        })
        """
        # 整体的逻辑大概是，调用window.asrsea(str1, str2, str3, str4)来生成bLa9R，params=bLa9R.encText，encSecKey=bLa9R.encSecKey

        # i1x实际上是一个JSON，不同的id对应不同的歌曲，通过id来获得对应歌曲的评论
        # bvq7j(["流泪", "强"])，实际上是，'010001'
        # zK7D.md，在js是可以找到的，它是一个固定值，bvq7j(zK7D.md)，实际上是，'00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
        # bvq7j(["爱心", "女孩", "惊恐", "大笑"])，实际上是，'0CoJUm6Qyw8W8jud'

        function_d_d = {
            "csrf_token": csrf_token,
            "cursor": f"{cursor}",
            "offset": f"{offset}",
            "orderType": f"{orderType}",
            "pageNo": f"{pageNo}",
            "pageSize": f"{pageSize}",
            "rid": f"R_SO_4_{id}",
            "threadId": f"R_SO_4_{id}",
        }
        """
        window.asrsea的str1
        csrf_token：用户识别码
        cursor：当前评论的当前位置，由上一页的响应获得(恒不为0)，第一页是-1，最后一页是0(要手动构造)
        offset：逐页获取评论的情况下不会变化，可以理解为，俩页的评论在数据库中的位置(最新的评论在第一行)的(最小差值-1)，如第一页的评论位置为1-20，第二页的评论位置为21-40，第三页的评论位置为41-60，那么从第一页开始获取第二页的评论，offset=21-20-1=0，从第一页开始获取第三页的评论，offset=41-20-1=20，这个offset一定是一个非负数(无论从哪一页到哪一页)
        orderType：最后一页是0，其他都是1，理论上，作为热歌，应该不会出现总评论数小于20的情况，如果出现了，目前也没有办法，因为总评论数是从响应获得的，第一次响应请求失败了那么就没有后续了
        pageNo：爬取第pageNo页的评论
        pageSize：爬取第pageNo页时，评论的数量，一般是20，最后一页需要计算得来
        """
        function_d_d = json.dumps(function_d_d)

        function_d_e = "010001"
        """window.asrsea的str2"""

        function_d_f = "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7"
        """window.asrsea的str3"""

        function_d_g = "0CoJUm6Qyw8W8jud"
        """window.asrsea的str4"""

        """
        通过asrsea可以定位到调用了这个函数：
        function d(d, e, f, g) {
            var h = {}, i = a(16);
            return h.encText = b(d, g), h.encText = b(h.encText, i), h.encSecKey = c(i, e, f), h
        }

        a(16)调用的是函数是：
        function a(a) {
            var d, e, b = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", c = "";
            for (d = 0; a > d; d += 1)
                e = Math.random() * b.length, e = Math.floor(e), c += b.charAt(e);
            return c
        }

        h.encText = b(d, g)和h.encText = b(h.encText, i)调用的函数是：
        function b(a, b) {
            var c = CryptoJS.enc.Utf8.parse(b);
            var d = CryptoJS.enc.Utf8.parse("0102030405060708");
            var e = CryptoJS.enc.Utf8.parse(a);
            var f = CryptoJS.AES.encrypt(e, c, {
                iv: d,
                mode: CryptoJS.mode.CBC
            });
            return f.toString()
        }

        h.encSecKey = c(i, e, f)调用的函数是：
        function c(a, b, c) {
            var d, e;
            return setMaxDigits(131), d = new RSAKeyPair(b, "", c), e = encryptedString(d, a)
        }

        最后返回了h，h是一个对象
        """

        # 对于a(16)，它的作用是生成一个长度为16的随机字符串，其中字符串只有字母和数字这俩种字符
        # 1. 将字符集定死为常量，可以减少内存占用
        # 2. 可以直接通过execjs执行a(16)
        # 由于目标是为了定期获取评论，为防止封号，保险起见，选择第二种方法

        with open("test.js", mode="r", encoding="utf-8") as f:
            js_code = f.read()
        ret = execjs.compile(js_code)

        function_d_i = ret.call("a", 16)
        """function d(...){...}里的i参数，即a(16)"""
        # print(f"function_d_i：\n{function_d_i}\n")

        # b函数的意思是，传入明文和密钥俩参数，其中：
        # 明文是function_d_d和enc_plaintext_1
        # 密钥是function_d_g和function_d_i(需要转换为字节，即.encode("utf-8"))
        # iv="0102030405060708".encode("utf-8")
        # mode: CryptoJS.mode.CBC(CryptoJS.AES.encrypt)表示用的是AES加密，mode=AES.MODE_CBC

        enc_plaintext_1 = self.enc_plaintext(function_d_d, function_d_g.encode("utf-8"))
        """h.encText = b(d, g)"""

        enc_plaintext_2 = self.enc_plaintext(enc_plaintext_1, function_d_i.encode("utf-8"))
        """h.encText = b(h.encText, i)"""

        params = enc_plaintext_2
        """params=bLa9R.encText"""
        # print(f"params：\n{params}\n")

        """
        对于h.encSecKey = c(i, e, f)调用的函数，由于其内部调用了过多的函数，导致难以分析，但是经过分析发现，这个JS代码是原生态JavaScript，故可以使用execjs来获取encSecKey
        """

        encSecKey = ret.call("c", function_d_i, function_d_e, function_d_f)
        """encSecKey=bLa9R.encSecKey"""
        # print(f"encSecKey：\n{encSecKey}\n")

        return params, encSecKey

    def enc_plaintext(self, plaintext: str, key: bytes) -> str:
        """
        AES.new(key, mode=AES.MODE_CBC, iv="0102030405060708".encode("utf-8"))
        :param plaintext: 明文(str)
        :param key: 密钥(bytes)
        :return: 密文(str)
        """
        # Data must be padded to 16 byte boundary in CBC mode
        # 对于CBC来说，填充的最好方案是：缺少的位数*chr(缺少的位数)
        plaintext += (16 - len(plaintext) % 16) * chr((16 - len(plaintext) % 16))

        # 创建加密器
        cipher = AES.new(key, mode=AES.MODE_CBC, iv="0102030405060708".encode("utf-8"))

        # 加密明文，得到的是bytes
        enc_plaintext = cipher.encrypt(plaintext.encode("utf-8"))

        # 用Base64对字节进行编码，再把Base64编码结果(仍是字节)解码成字符串形式
        enc_plaintext = base64.b64encode(enc_plaintext).decode("utf-8")
        return enc_plaintext
