#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import re
import time
import lxml
import random
import requests
from utils.utils import Utils
import lxml.html.soupparser as soupparser

from utils.time_transform import TimeTransform



# 该类提取腾讯微博相关信息：http://t.qq.com/
class TencentWeiboExtract(object):

    def __init__(self):
        self.publishedtime_xpath = "//div[@id='orginCnt']//div[@class='pubInfo c_tx5']//a[@class='time']/text()"
        self.content_xpath = "//div[@id='orginCnt']//div[@id='msginfo']/a/text() | //div[@id='orginCnt']//div[@id='msginfo']/text() | \
                            //div[@id='orginCnt']//div[@id='msginfo']/em/a/text() | //div[@id='orginCnt']//div[@id='msginfo']/em/text()"


    def extract_publishedtime(self, tree):
        t = tree.xpath(self.publishedtime_xpath)[0].strip()
        t = time.strptime(t, "%Y年%m月%d日 %H:%M".decode('utf8'))
        t = TimeTransform.struct_to_string(t)
        return t


    def extract_content(self, tree):
        content = tree.xpath(self.content_xpath)
        content = ''.join(content)
        content = Utils.transform_coding(content.strip('\n'))
        return content


    def parse_response(self, response, item):
        if re.match("http://t.qq.com/p/t/[0-9]+", item.url):  # 短微博
            html = response.content
            tree = lxml.etree.HTML(html)
            try:
                item.publishedtime = self.extract_publishedtime(tree)
                item.content = self.extract_content(tree)
            except Exception as e:
                item.urlhash = None

        else:  # 其它, 如用户首页
            item.urlhash = None
