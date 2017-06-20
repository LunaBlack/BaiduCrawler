#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import re
import time
import lxml
import random
import requests
from utils.utils import Utils, USER_AGENTS
import lxml.html.soupparser as soupparser

from crawl.item import Item
from utils.time_transform import TimeTransform



# 该类提取腾讯网的相关信息：http://www.qq.com
class QqExtract(object):

    def __init__(self):
        self.url_xpath = "/html/head/link[@rel='alternate']/@href"
        self.title_xpath = "//h1/text()"
        self.publishedtime_xpath = "//span[@class='time']/text()"
        self.content_xpath = "//div[@class='content fontsmall']//p//text() "

        self.user_agents = USER_AGENTS
        self.try_times = 3
        self.time_out = 4


    # 将页面转换为便于提取信息的形式
    def re_request(self, tree):
        url = tree.xpath(self.url_xpath)[0].strip()

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
        t = time.strptime(t, "%Y-%m-%d %H:%M:%S")
        t = TimeTransform.struct_to_string(t)
        return t


    def extract_content(self, tree):
        content = tree.xpath(self.content_xpath)
        content = '\n'.join(content)

        r = re.compile(r'''\n+''', re.M | re.S)
        content = r.sub('\n', content)

        content = Utils.transform_coding(content.strip('\n'))
        return content


    def parse_response(self, response, item):
        html = response.content
        tree = lxml.etree.HTML(html)
        response = self.re_request(tree)
        if response is None:
            item.urlhash = None
            return

        html = response.content
        tree = lxml.etree.HTML(html)
        try:
            item.title = self.extract_title(tree)
            item.publishedtime = self.extract_publishedtime(tree)
            item.content = self.extract_content(tree)
        except Exception as e:
            print e
            item.urlhash = None



if __name__ == '__main__':
    item = Item()
    url = 'http://news.qq.com/a/20140807/020463.htm'
    response = requests.get(url)

    e = QqExtract()
    e.parse_response(response, item)

    print item.title
    print item.publishedtime
    print item.content