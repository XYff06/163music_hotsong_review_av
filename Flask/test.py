import jieba
import pandas as pd
from matplotlib import pyplot as plt
from wordcloud import WordCloud

df = pd.read_csv("data/test.csv")
text = " ".join(df["content"].astype(str))

words = jieba.lcut(text)
text_cut = " ".join(words)

wc = WordCloud(
    font_path="source/myttf.TTF",  # 字体文件，从这里"C:\Windows\Fonts"拿一个喜欢的字体
    background_color="white",
    width=1000,
    height=700,
    max_words=200,
    stopwords={""},
).generate(text_cut)
plt.imshow(wc, interpolation="bilinear")
plt.axis("off")
plt.show()
wc.to_file("data/wordcloud.png")


class Process_Content_Pipeline:
    def process_item(self, item, spider):
        df = pd.read_csv("data/test.csv")
        text = " ".join(df["content"].astype(str))

        words = jieba.lcut(text)
        text_cut = " ".join(words)

        wc = WordCloud(
            font_path="source/myttf.TTF",  # 字体文件，从这里"C:\Windows\Fonts"拿一个喜欢的字体
            background_color="white",
            width=1000,
            height=700,
            max_words=200,
            stopwords={""},
        ).generate(text_cut)
        plt.imshow(wc, interpolation="bilinear")
        plt.axis("off")
        plt.show()
        wc.to_file("data/wordcloud.png")

    pass
