import pandas as pd
from flask import Flask, render_template

from utils import get_conn, get_tfidf_data

app = Flask(__name__)


@app.route("/")
def index():
    """
    首页(展示歌曲列表及评论统计)
    :return:
    """
    conn = get_conn()

    # 查询所有歌曲及评论数
    query = """
            SELECT song_id, title, href, COUNT(*) AS comment_count
            FROM comments
            GROUP BY song_id, title, href
            ORDER BY song_id
            """
    songs = pd.read_sql(query, conn)
    conn.close()

    # 将DataFrame转换为字典列表以传递给模板
    return render_template("index.html", songs=songs.to_dict(orient="records"))


@app.route("/song/<int:song_id>")
def song_detail(song_id):
    """
    单曲详情页(评论数量增长趋势、词云图、TF-IDF关键词)
    :param song_id:
    :return:
    """
    conn = get_conn()

    # 获取歌曲信息(取第一条评论中的基础信息)
    song_info_query = "SELECT * FROM comments WHERE song_id=%s LIMIT 1"
    song_info = pd.read_sql(song_info_query, conn, params=[song_id])

    if song_info.empty:
        conn.close()
        return f"❌ 未找到歌曲ID={song_id}的记录!"

    # 获取评论时间分布
    time_query = """
                 SELECT DATE(comment_time) AS date, COUNT(*) AS daily_count
                 FROM comments
                 WHERE song_id=%s
                 GROUP BY DATE(comment_time)
                 ORDER BY date
                 """
    df = pd.read_sql(time_query, conn, params=[song_id])

    # 计算累计评论数量
    df["cumulative_count"] = df["daily_count"].cumsum()

    # 提取TF-IDF关键词
    tfidf_data = get_tfidf_data(song_id, conn)

    conn.close()

    # 词云图片路径
    wordcloud_path = f"img/wordcloud_{song_id}.png"

    # 渲染模板
    return render_template(
        "song_detail.html",
        song=song_info.iloc[0].to_dict(),
        data=df.to_dict(orient="records"),
        tfidf=tfidf_data,
        wordcloud_path=wordcloud_path,
    )


if __name__ == "__main__":
    app.run(debug=True)
