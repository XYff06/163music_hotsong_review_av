# https://curlconverter.com/
import os
from datetime import datetime

import pandas as pd
import pymysql

from review_av.settings import MYSQL


class Data_Save_CSV_Pipeline:
    """用于临时调试，方便查看数据"""

    def open_spider(self, spider):
        self.file_path = "data/test.csv"
        self.items = []  # 暂存所有item

        # 如果文件不存在，则新建并写入列名
        if not os.path.exists("data"):
            os.makedirs("data")

        # 如果文件已存在，不重复写入表头
        self.file_exists = os.path.exists(self.file_path)

    def close_spider(self, spider):
        if not self.items:
            return  # 没有数据就不写入

        df = pd.DataFrame(self.items)

        # 写入CSV
        df.to_csv(
            self.file_path,
            mode="a",  # 追加写入
            header=not self.file_exists,  # 若文件存在则不写表头
            index=False,
            encoding="utf-8-sig"
        )

    def process_item(self, item, spider):
        # print(item)

        # 将item转为dict并保存到内存中
        self.items.append({
            "href": item.get("href"),
            "title": item.get("title"),
            "id": item.get("id"),
            "userId": item.get("userId"),
            "nickname": item.get("nickname"),
            "commentId": item.get("commentId"),
            "content": item.get("content"),
            "time": item.get("time"),
            "likedCount": item.get("likedCount"),
            "replyCount": item.get("replyCount"),
            "parentCommentId": item.get("parentCommentId"),
            "ext_dislike": item.get("ext_dislike"),
            "is_hot_comment": item.get("is_hot_comment"),
        })
        if len(self.items) >= 1000:
            self.flush_to_csv()
            self.items.clear()

        return item

    def flush_to_csv(self):
        df = pd.DataFrame(self.items)
        df.to_csv(
            self.file_path,
            mode="a",
            header=not os.path.exists(self.file_path),
            index=False,
            encoding="utf-8-sig"
        )


class Data_Save_MySQL_Pipeline:
    def open_spider(self, spider):
        try:
            # 连接数据库，先在settings.py里配置mysql，然后在pipelines.py里添加from review_av.settings import MYSQL
            """
            MYSQL = {
                "host": "localhost",  # 数据库地址
                "port": 3306,
                "user": "root",  # 用户名
                "password": "root",  # 密码
                "database": "music_163_review",  # 数据库名，如果不存在需要先创建(create database music_163_review;)
                "charset": "utf8mb4",
                "connect_timeout": 5  # 连接超时时间，单位秒
            }
            """
            self.conn = pymysql.connect(**MYSQL)
            print("✅ MySQL连接成功!")

            # 执行简单查询测试
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT VERSION();")
                version = cursor.fetchone()
                print(f"MySQL版本:{version[0]}")

        except pymysql.MySQLError as e:
            print(f"❌ MySQL连接失败!\n错误信息:{e}")

    def close_spider(self, spider):
        if self.conn:
            self.conn.close()

    def process_item(self, item, spider):
        with self.conn.cursor() as cursor:
            try:
                insert_sql = """INSERT INTO comments (href,
                                                      title,
                                                      song_id,
                                                      user_id,
                                                      nickname,
                                                      comment_id,
                                                      content,
                                                      comment_time,
                                                      liked_count,
                                                      reply_count,
                                                      parent_comment_id,
                                                      ext_dislike,
                                                      is_hot_comment)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                cursor.execute(insert_sql, (
                    item.get("href"),
                    item.get("title"),
                    item.get("id"),
                    item.get("userId"),
                    item.get("nickname"),
                    item.get("commentId"),
                    item.get("content"),
                    datetime.fromtimestamp(int(item["time"]) / 1000),
                    int(item.get("likedCount", 0)),
                    int(item.get("replyCount", 0)),
                    int(item.get("parentCommentId", 0)),
                    int(item.get("ext_dislike", 0)),
                    1 if item.get("is_hot_comment") == "YES" else 0,
                ))
                self.conn.commit()
            except Exception as e:
                self.conn.rollback()
            finally:
                if cursor:
                    cursor.close()

        return item
