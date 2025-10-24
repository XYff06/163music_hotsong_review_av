import scrapy


class ReviewAvItem(scrapy.Item):
    href = scrapy.Field()
    title = scrapy.Field()
    id = scrapy.Field()
    userId = scrapy.Field()
    nickname = scrapy.Field()
    commentId = scrapy.Field()
    content = scrapy.Field()
    time = scrapy.Field()
    likedCount = scrapy.Field()
    replyCount = scrapy.Field()
    parentCommentId = scrapy.Field()
    ext_dislike = scrapy.Field()
    is_hot_comment = scrapy.Field()
