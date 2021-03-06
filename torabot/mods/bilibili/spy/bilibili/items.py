# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class Bangumi(Item):

    kind = Field()
    query = Field()
    content = Field()

    def __init__(self, **kargs):
        kargs.update(kind='bangumi')
        Item.__init__(self, **kargs)


class User(Item):

    kind = Field()
    query = Field()
    posts = Field()

    def __init__(self, **kargs):
        kargs.update(kind='user')
        Item.__init__(self, **kargs)


class Post(Item):

    title = Field()
    uri = Field()
    cover = Field()
    kind = Field()
    ctime = Field()
    desc = Field()
