import jieba
import pandas as pd
import pymysql
from sklearn.feature_extraction.text import TfidfVectorizer

# 停用词列表，可根据需要扩展
STOPWORDS = {"的", "了", "是", "我", "你", "在", "也", "就", "都", "和", "有", "吗", "啊", "哦", "呢", "吧", "就", "还",
             "要", "跟", "与", "很"}


def get_conn():
    """
    建立MySQL数据库连接
    :return: pymysql连接对象
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
    try:
        conn = pymysql.connect(**MYSQL)
        print(f"✅ MySQL连接成功!")
        return conn
    except pymysql.MySQLError as e:
        print(f"❌ MySQL连接失败:{e}")
        raise


def get_tfidf_data(song_id, conn, top_k=15):
    """
    计算某首歌曲评论的TF-IDF关键词
    :param song_id: 歌曲ID
    :param conn: 数据库连接
    :param top_k: 提取的关键词数量
    :return: list[dict]: [{"word": "关键词", "score": tfidf值}, ...]
    """
    # 读取该歌曲的所有评论
    query = "SELECT content FROM comments WHERE song_id=%s"
    df = pd.read_sql(query, conn, params=[song_id])

    if df.empty:
        return []

    # 拼接所有评论为一个长文本
    text = " ".join(df["content"].astype(str).tolist())

    # 中文分词
    words = [" ".join(jieba.cut(text))]

    # TF-IDF向量化
    vectorizer = TfidfVectorizer(max_features=top_k)
    tfidf_matrix = vectorizer.fit_transform(words)

    # 获取关键词与分数
    feature_names = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.toarray()[0]

    # 构造关键词-得分表
    tfidf_data = [
        {"word": feature_names[i], "score": float(scores[i])}
        for i in range(len(feature_names))
    ]

    # 从高到低排序
    tfidf_data.sort(key=lambda x: x["score"], reverse=True)
    print(f"🔍 TF-IDF数据(song_id={song_id}):", tfidf_data)

    return tfidf_data
