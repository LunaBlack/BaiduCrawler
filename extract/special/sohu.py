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



# 该类提取搜狐网的相关信息：http://www.sohu.com
class SohuExtract(object):

    def __init__(self):
        self.title_xpath = "//h1//text()"
        self.publishedtime_xpath = "//span[@class='time']/text() | //div[@class='time']/text()"
        self.content_xpath = "//div[@itemprop='articleBody']//p//text() | //div[@itemprop='articleBody']/text() | //div[@class='text clear']/text() | //article[@class='article']//p//text() "


    def extract_title(self, tree):
        title = tree.xpath(self.title_xpath)[0].strip()
        title = Utils.transform_coding(title.strip())
        return title


    def extract_publishedtime(self, tree):
        t = tree.xpath(self.publishedtime_xpath)[0].strip().split()[0]

        try:
            t = time.strptime(t, "%Y-%m-%d")
        except:
            try:
                t = time.strptime(t, "%Y年%m月%d日%H%M".decode('utf8'))
            except:
                pass

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

        try:
            item.title = self.extract_title(tree)
            item.publishedtime = self.extract_publishedtime(tree)
            item.content = self.extract_content(tree)
        except Exception as e:
            item.urlhash = None



if __name__ == '__main__':
    item = Item()
    url = 'http://roll.sohu.com/20140804/n403090818.shtml'
    response = requests.get(url)

    e = SohuExtract()
    e.parse_response(response, item)

    print item.title
    print item.publishedtime
    print item.content