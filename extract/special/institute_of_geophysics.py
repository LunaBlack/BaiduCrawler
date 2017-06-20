#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import re
import time
import lxml
import random
import requests
from utils.utils import Utils
import lxml.html.soupparser as soupparser

from crawl.item import Item
from utils.time_transform import TimeTransform



# 该类提取中国地震局地球物理研究所的相关信息：http://http://www.cea-igp.ac.cn/
class CeaigpExtract(object):

    def __init__(self):
        self.detail_xpath = "//div[@class='main']/div[@class='sub_right']/div[@class='detail']//text()"


    def extract_title(self, detail):
        title = detail[0].strip()
        title = Utils.transform_coding(title.strip())
        return title


    def extract_content(self, detail):
        content = ''.join(detail[1:])
        r = re.compile(r'''\n+''', re.M | re.S)
        content = r.sub('\n', content)

        content = Utils.transform_coding(content.strip('\n+'))
        return content


    def parse_response(self, response, item):
        html = response.content
        tree = lxml.etree.HTML(html)

        try:
            detail = tree.xpath(self.detail_xpath)
            detail = [i for i in detail if i.strip()]

            item.title = self.extract_title(detail)
            item.content = self.extract_content(detail)

        except Exception as e:
            item.urlhash = None



if __name__ == '__main__':
    item = Item()
    url = 'http://www.cea-igp.ac.cn/cxdt/273313.html'
    response = requests.get(url)

    e = CeaigpExtract()
    e.parse_response(response, item)

    print item.title
    print item.content