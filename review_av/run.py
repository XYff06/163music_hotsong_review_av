import logging
import subprocess
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

# 日志配置
logging.basicConfig(
    filename="logs/scheduler.log",  # 日志文件路径
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)


def run_spider():
    """执行爬虫"""
    logging.info(f"开始运行爬虫任务 at {datetime.now()}")
    try:
        # 使用subprocess启动独立进程
        subprocess.run("scrapy crawl test".split())
    except Exception as e:
        logging.error(f"爬虫运行出错：{e}")
    logging.info(f"爬虫任务结束 at {datetime.now()}")


if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone="Asia/Shanghai")

    # 每隔1分钟执行一次
    scheduler.add_job(run_spider, "interval", minutes=1, id="test_spider_job")

    logging.info("定时爬虫调度器启动，每1分钟执行一次任务")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("定时器已停止")
