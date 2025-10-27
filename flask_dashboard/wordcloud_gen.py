import logging
from datetime import datetime

import jieba
import pandas as pd
from apscheduler.schedulers.background import BlockingScheduler
from wordcloud import WordCloud

from utils import get_conn, STOPWORDS

# 日志配置
logging.basicConfig(
    filename="logs/scheduler.log",  # 日志文件路径
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)


def generate_wordcloud():
    """
    生成词云
    :return:
    """
    conn = get_conn()
    logging.info(f"开始运行生成词云任务 at {datetime.now()}")
    try:
        song_id_list = pd.read_sql("SELECT song_id FROM comments GROUP BY song_id", conn)
        for _, row in song_id_list.iterrows():
            df = pd.read_sql(f"SELECT content FROM comments WHERE song_id={row["song_id"]}", conn)
            # 拼接评论并分词
            text = " ".join(df["content"].astype(str).tolist())
            cut_text = " ".join(jieba.cut(text))

            # 生成词云
            wc = WordCloud(
                font_path="static/myttf.ttf",
                width=800,
                height=600,
                background_color="white",
                max_words=200,
                stopwords=STOPWORDS,
            ).generate(cut_text)

            # 保存词云图到static/img文件夹，每首歌一个
            filename = f"static/img/wordcloud_{row["song_id"]}.png"
            wc.to_file(filename)
            logging.info(f"已生成 {row["song_id"]} 的词云图")
            print(f"已生成 {row["song_id"]} 的词云图")
    except Exception as e:
        logging.error(f"运行生成词云任务出错:{e}")
    finally:
        conn.close()
    logging.info(f"生成词云任务结束 at {datetime.now()}")


if __name__ == "__main__":

    generate_wordcloud()  # 首次生成

    scheduler = BlockingScheduler(timezone="Asia/Shanghai")

    # 每隔30分钟执行一次
    scheduler.add_job(generate_wordcloud, "interval", minutes=30)

    logging.info("定时生成词云调度器启动，每30分钟执行一次任务")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("定时器已停止")
