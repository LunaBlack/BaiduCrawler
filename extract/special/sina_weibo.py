#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import re
import time
import lxml
import json
import random
import requests
from utils.utils import Utils, USER_AGENTS
import lxml.html.soupparser as soupparser

from crawl.item import Item
from utils.time_transform import TimeTransform



# 该类提取新浪微博（仅限短微博）
class SinaWeiboShortExtract(object):

    def __init__(self):
        self.publishedtime_xpath = "//div[@id='M_']//span[@class='ct']/text()"
        self.content_xpath = "//div[@id='M_']//span[@class='ctt']/a/text() | //div[@id='M_']//span[@class='ctt']/text()"

        self.user_agents = USER_AGENTS
        self.try_times = 3
        self.time_out = 4


    # 将电脑版网页转换为客户端网页
    def re_request(self, response, item):
        url = item.url.replace('weibo.com', 'weibo.cn')
        if url == item.url:
            return response

        for _ in range(self.try_times):
            try:
                header = {'User-Agent': USER_AGENTS[random.randint(0, len(USER_AGENTS) - 1)]}
                response = requests.get(url, headers=header, timeout=self.time_out)
                if response.status_code == 200:
                    return response

            except Exception as e:
                pass
            time.sleep(random.randint(1, 3))

        return None


    def extract_publishedtime(self, tree):
        t = tree.xpath(self.publishedtime_xpath)[0].strip()
        t = time.strptime(t, "%Y-%m-%d %H:%M:%S")
        t = TimeTransform.struct_to_string(t)
        return t


    def extract_content(self, tree):
        content = tree.xpath(self.content_xpath)
        content = ''.join(content)
        content = Utils.transform_coding(content.strip('\n'))
        if content.startswith(':'.decode('utf8')):
            content = content[1:]
        return content


    def parse_response(self, response, item):
        response = self.re_request(response, item)
        if response is None:
            item.urlhash = None
            return

        html = response.content
        tree = lxml.etree.HTML(html)
        try:
            item.publishedtime = self.extract_publishedtime(tree)
            item.content = self.extract_content(tree)
        except Exception as e:
            item.urlhash = None



# 该类提取新浪微博（仅限长微博）
class SinaWeiboArticleExtract(object):

    def __init__(self):
        self.title_xpath = '//div/h1[@class="title"]/text()'
        self.publishedtime_xpath = '//div[@class="info clearfix"]//span[@class="time"]/text()'
        self.content_xpath = "//div[@class='WBA_content clearfix']//text()"

        self.user_agents = USER_AGENTS
        self.try_times = 3
        self.time_out = 4


    # 将页面转换为便于提取信息的形式
    def re_request(self, item):
        cid = item.url[item.url.index('weibo.com/p/')+12: item.url.index('?from=')]
        url = 'http://card.weibo.com/article/aj/articleshow?cid=' + cid

        for _ in range(self.try_times):
            try:
                header = {'User-Agent': USER_AGENTS[random.randint(0, len(USER_AGENTS) - 1)]}
                response = requests.get(url, headers=header, timeout=self.time_out)
                if response.status_code == 200:
                    return response

            except Exception as e:
                pass
            time.sleep(random.randint(1, 3))

        return None


    def extract_title(self, tree):
        title = tree.xpath(self.title_xpath)[0].strip()
        title = Utils.transform_coding(title.strip())
        return title


    def extract_publishedtime(self, tree):
        t = tree.xpath(self.publishedtime_xpath)[0].strip()
        t = time.strptime(t, "%Y-%m-%d %H:%M")
        t = TimeTransform.struct_to_string(t)
        return t


    def extract_content(self, tree):
        content = tree.xpath(self.content_xpath)
        content = ''.join(content).replace(' ', '\n')
        r = re.compile(r'''\n+''', re.M|re.S)
        content = r.sub('\n', content)

        content = Utils.transform_coding(content.strip('\n'))
        if content.startswith(':'.decode('utf8')):
            content = content[1:]
        return content


    def parse_response(self, response, item):
        response = self.re_request(item)
        if response is None:
            item.urlhash = None
            return

        html = response.content
        try:
            tree = lxml.etree.HTML(json.loads(html)['data']['article'])
            item.title = self.extract_title(tree)
            item.publishedtime = self.extract_publishedtime(tree)
            item.content = self.extract_content(tree)
        except Exception as e:
            item.urlhash = None



# 该类提取新浪微博, 判断url是短微博/长微博/话题, 并采取相应措施：http://weibo.com
class SinaWeiboExtract(object):

    def __init__(self):
        pass


    def parse_response(self, response, item):
        url = response.url

        if re.match("http://weibo.com/[0-9]+/.*type=comment.*", url):  # 短微博
            se = SinaWeiboShortExtract()
            se.parse_response(response, item)

        elif re.match("http://weibo.com/p/.+mod=recommand_article.*", url):  # 长微博
            se = SinaWeiboArticleExtract()
            se.parse_response(response, item)

        elif re.match("http://weibo.com/p/.+from=huati_thread.*", url):  # 话题
            item.urlhash = None

        else:
            item.urlhash = None




if __name__ == '__main__':
    item = Item()

    # url = "http://weibo.com/1389537561/BgPtMatcA?mod=weibotime&type=comment"
    url = "http://weibo.com/p/1001593739605047367339?from=singleweibo&mod=recommand_article"
    # url = "http://weibo.com/p/100808d93f8a84e207ec12b9514f1f97a051cb?k=%E4%BA%91%E5%8D%97%E9%B2%81%E7%94%B8%E5%8E%BF6.5%E7%BA%A7%E5%9C%B0%E9%9C%87&from=huati_thread"

    response = requests.get(url)
    response.url = url
    item.url = url

    s = SinaWeiboExtract()
    s.parse_response(response, item)

    print item.url
    print item.publishedtime
    print item.title
    print item.content
