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



# 该类提取百度贴吧的相关信息：http://tieba.baidu.com
class TiebaExtract(object):

    def __init__(self):
        self.title_xpath = "//h1[@title]/text() | //h3[@title]/text()"
        self.content_xpath = "//div[@class='p_postlist']//div[@class='d_post_content j_d_post_content '][1]/a/text() | \
                              //div[@class='p_postlist']//div[@class='d_post_content j_d_post_content '][1]/text() | \
                              //div[@class='p_postlist']//div[@class='d_post_content j_d_post_content  clearfix'][1]/a/text() | \
                              //div[@class='p_postlist']//div[@class='d_post_content j_d_post_content  clearfix'][1]/text()"

    def extract_title(self, tree):
        title = tree.xpath(self.title_xpath)[0].strip()
        title = Utils.transform_coding(title.strip())
        return title


    def extract_content(self, tree):
        content = tree.xpath(self.content_xpath)
        content = '\n'.join([i.strip() for i in content])

        r = re.compile(r'''\n+''', re.M | re.S)
        content = r.sub('\n', content)

        content = Utils.transform_coding(content.strip('\n'))
        return content


    def parse_response(self, response, item):
        html = response.text
        tree = lxml.etree.HTML(html)

        try:
            item.title = self.extract_title(tree)
            item.content = self.extract_content(tree)
        except Exception as e:
            item.urlhash = None



if __name__ == '__main__':
    item = Item()
    url = 'http://tieba.baidu.com/p/3206341463'
    response = requests.get(url)

    e = TiebaExtract()
    e.parse_response(response, item)

    print item.title
    print item.content
