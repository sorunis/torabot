# coding: utf-8
# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

import re
import json
from itertools import chain
from urlparse import urljoin, urlparse, parse_qs
from urllib import urlencode
from scrapy import log
from scrapy.selector import Selector
from scrapy.http import Request
from torabot.spy.spiders.redis import RedisSpider
from torabot.spy.items import Result
from ..items import Art, Page, SearchUserPage, Recommendation, RecommendationImage


BASE_URL = 'http://www.pixiv.net/'
USER_ILLUSTRATIONS_URL = 'http://www.pixiv.net/member_illust.php'
USER_URL = 'http://www.pixiv.net/member.php'
USER_ILLUSTRATIONS_URL_TEMPLATE = USER_ILLUSTRATIONS_URL + '?id=%s'
RANKING_URL = 'http://www.pixiv.net/ranking.php'
SEARCH_USER_URL = 'http://www.pixiv.net/search_user.php'


class Pixiv(RedisSpider):

    name = 'pixiv'

    def __init__(self, max_arts, phpsessid, life=60, *args, **kargs):
        super(Pixiv, self).__init__(*args, life=life, **kargs)
        self.max_arts = int(max_arts)
        self.phpsessid = phpsessid

    def make_requests_from_query(self, query):
        query = json.loads(query)
        for req in {
            'user_id': self.make_user_id_requests,
            'user_uri': self.make_user_uri_requests,
            'user_illustrations_uri': self.make_user_illustrations_uri_requests,
            'ranking': self.make_ranking_uri_requests,
            'username': self.make_username_requests,
        }[query['method']](query):
            yield req

    def make_user_id_requests(self, query):
        yield self._make_user_illustrations_uri_request(
            USER_ILLUSTRATIONS_URL_TEMPLATE % query['user_id'],
            query
        )

    def _make_headers(self):
        return {
            'Cookie': ' '.join([
                'p_ab_id=3;',
                'login_ever=yes;',
                'manga_viewer_expanded=1;',
                'bookmark_tag_type=count;',
                'bookmark_tag_order=desc;',
                'visit_ever=yes;',
                'PHPSESSID=%s;' % self.phpsessid,
            ])
        }

    def make_username_requests(self, query):
        yield Request(
            SEARCH_USER_URL + '?' + urlencode({
                's_mode': 's_usr',
                'nick_mf': 1,
                'nick': query['username'].encode('utf-8'),
            }),
            headers=self._make_headers(),
            callback=self.parse_username,
            meta=dict(query=query),
            dont_filter=True,
        )

    def make_ranking_uri_requests(self, query):
        page_count = 10
        pages = [None] * page_count
        for page in range(page_count):
            yield Request(
                make_ranking_json_uri(query, page),
                headers=self._make_headers(),
                callback=self.parse_ranking_uri,
                meta=dict(
                    page=page,
                    pages=pages,
                    query=query,
                ),
                dont_filter=True,
            )

    def parse_ranking_uri(self, response):
        query = response.meta['query']
        try:
            pages = response.meta['pages']
            d = json.loads(response.body_as_unicode())
            pages[response.meta['page']] = [] if 'error' in d else d['contents']
            if None not in pages:
                arts = list(chain(*pages))
                return Page(
                    query=query,
                    uri=make_ranking_uri(query),
                    total=len(arts),
                    arts=arts,
                )
        except Exception as e:
            return failed(query, str(e))

    def make_user_uri_requests(self, query):
        d = parse_qs(urlparse(query['uri']).query)
        assert 'id' in d
        yield self._make_user_illustrations_uri_request(
            USER_ILLUSTRATIONS_URL_TEMPLATE % d['id'][0],
            query
        )

    def make_user_illustrations_uri_requests(self, query):
        yield self._make_user_illustrations_uri_request(query['uri'], query)

    def _make_user_illustrations_uri_request(self, uri, query):
        return Request(
            uri,
            headers=self._make_headers(),
            callback=self.parse_user_illustrations_uri,
            meta=dict(
                uri=uri,
                query=query,
            ),
            dont_filter=True,
        )

    def parse_user_illustrations_uri(self, response):
        query = response.meta['query']
        uri = response.meta['uri']
        log.msg(u'got response of query %s' % uri)

        def gen(sel):
            author = sel.xpath('//h1[@class="user"]/text()').extract()[0]
            for a in sel.xpath('//a[@class="work"]')[:self.max_arts]:
                yield Art(
                    title=a.xpath('h1/@title').extract()[0],
                    author=author,
                    uri=urljoin(BASE_URL, a.xpath('@href').extract()[0]),
                    thumbnail_uri=a.xpath('img/@src').extract()[0],
                )

        sel = Selector(response)
        try:
            return Page(
                query=query,
                uri=uri,
                total=int(sel.xpath('//*[@id="wrapper"]/div[1]/div[1]/div/span/text()').re(r'\d+')[0]),
                arts=list(gen(sel)),
            )
        except Exception as e:
            return failed(query, str(e))

    def parse_username(self, response):
        query = response.meta['query']
        sel = Selector(response)
        try:
            items = list(sel.xpath('//li[@class="user-recommendation-item"]'))
            if items:
                user_id = items[0].xpath('.//a[@class="title"]/@href').extract()[0].split('=')[-1]
                check_user_id(user_id)
                return self._make_user_illustrations_uri_request(
                    USER_ILLUSTRATIONS_URL_TEMPLATE % user_id,
                    query
                )
            return Request(
                SEARCH_USER_URL + '?' + urlencode({
                    's_mode': 's_usr',
                    'nick': query['username'].encode('utf-8'),
                }),
                headers=self._make_headers(),
                callback=self.parse_username_recommendations,
                meta=dict(query=query),
                dont_filter=True,
            )
        except Exception as e:
            return failed(query, str(e))

    def parse_username_recommendations(self, response):
        query = response.meta['query']
        sel = Selector(response)
        try:
            return SearchUserPage(
                query=query,
                uri=response.url,
                total=0,
                arts=[],
                recommendations=list(gen_recommendations(sel))
            )
        except Exception as e:
            return failed(query, str(e))


def gen_recommendations(sel):
    for item in sel.xpath('//li[@class="user-recommendation-item"]'):
        yield make_recommendation(item)


def make_recommendation(item):
    return Recommendation(
        user_uri=urljoin(BASE_URL, item.xpath('.//a[@class="title"]/@href').extract()[0]),
        icon_uri=item.xpath('.//a[@class="user-icon-container ui-scroll-view"]/@data-src').extract()[0],
        title=item.xpath('.//a[@class="title"]/text()').extract()[0],
        illustration_count=int(item.xpath('.//dl/dd/a/text()').extract()[0]),
        caption=''.join(item.xpath('.//p[@class="caption"]/text()').extract()),
        images=list(gen_recommendation_images(item.xpath('.//ul[@class="images"]/li'))),
    )


def gen_recommendation_images(images):
    for image in images:
        yield RecommendationImage(
            uri=image.xpath('.//a/@href').extract()[0],
            thumbnail_uri=image.xpath('@data-src').extract()[0],
        )


def check_user_id(id):
    assert re.match(r'^\d+$', id)


def failed(query, message):
    log.msg('parse failed: %s' % message, level=log.ERROR)
    return Result(ok=False, query=query, message=message)


def make_ranking_json_uri(query, page):
    return 'http://www.pixiv.net/ranking.php?format=json&mode=%(mode)s&p=%(page)d' % dict(
        mode=query['mode'],
        page=page + 1,
    )


def make_ranking_uri(query):
    return 'http://www.pixiv.net/ranking.php?mode=%(mode)s' % query
