ADDONS = {}
BOT_NAME = "review_av"
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 5
DOWNLOADER_MIDDLEWARES = {
    "review_av.middlewares.ReviewAvDownloaderMiddleware": 543,
}
FEED_EXPORT_ENCODING = "utf-8"
ITEM_PIPELINES = {
    # "review_av.pipelines.Data_Save_CSV_Pipeline": 100,
    "review_av.pipelines.Data_Save_MySQL_Pipeline": 100,
}
LOG_ENABLED = True  # 开启日志
LOG_ENCODING = "utf-8"  # 编码
LOG_FILE = "logs/scrapy.log"  # 日志输出文件路径
LOG_STDOUT = True  # 把标准输出(print)也写入日志文件
MYSQL = {
    "host": "localhost",  # 数据库地址
    "port": 3306,
    "user": "root",  # 用户名
    "password": "root",  # 密码
    "database": "music_163_review",  # 数据库名，如果不存在需要先创建(create database music_163_review;)
    "charset": "utf8mb4",
    "connect_timeout": 5  # 连接超时时间，单位秒
}
NEWSPIDER_MODULE = "review_av.spiders"
ROBOTSTXT_OBEY = False
SPIDER_MODULES = ["review_av.spiders"]
