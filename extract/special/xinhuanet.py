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



# 该类提取新华网（时政版）的相关信息：http://www.xinhuanet.com/politics/
class XinhuaPoliticsExtract(object):

    def __init__(self):
        self.title_xpath = "//div[@id='center']//h1/text()"
        self.publishedtime_xpath = "//div[@id='center']//div[@class='info']/span[@id='pubtime']/text()"
        self.content_xpath = "//div[@id='center']//div[@id='content']//text()"


    def extract_title(self, tree):
        title = tree.xpath(self.title_xpath)[0].strip()
        return title


    def extract_publishedtime(self, tree):
        t = tree.xpath(self.publishedtime_xpath)[0].strip()
        t = time.strptime(t, "%Y年%m月%d日 %H:%M:%S".decode('utf8'))
        t = TimeTransform.struct_to_string(t)
        return t


    def extract_content(self, tree):
        content = tree.xpath(self.content_xpath)
        content = ''.join(content)

        content = content.replace(' ', '\n')
        r = re.compile(r'''\n+''', re.M | re.S)
        content = r.sub('\n', content)

        content = Utils.transform_coding(content.strip('\n'))
        return content


    def extract_summary(self, content):
        p_list = content.split('\n')
        p_list = [i for i in p_list if i.strip()]
        summary = p_list[0]
        return summary


    def parse_response(self, response, item):
        html = response.content
        tree = lxml.etree.HTML(html)

        try:
            item.title = self.extract_title(tree)
            item.publishedtime = self.extract_publishedtime(tree)
            item.content = self.extract_content(tree)

            summary = self.extract_summary(item.content)
            if summary:
                item.summary = summary

        except Exception as e:
            item.urlhash = None



# 该类提取新华网（图片版）的相关信息：http://www.xinhuanet.com/photo/
class XinhuaPhotoExtract(object):

    def __init__(self):
        self.title_xpath = "//span[@id='title']/text()"
        self.publishedtime_xpath = "//span[@id='pubtime']/text()"
        self.content_xpath = "//span[@id='content']//text()"


    def extract_title(self, tree):
        title = tree.xpath(self.title_xpath)[0].strip()
        title = Utils.transform_coding(title.strip())
        return title


    def extract_publishedtime(self, tree):
        t = tree.xpath(self.publishedtime_xpath)[0].strip()
        t = time.strptime(t, "%Y年%m月%d日 %H:%M:%S".decode('utf8'))
        t = TimeTransform.struct_to_string(t)
        return t


    def extract_content(self, tree):
        content = tree.xpath(self.content_xpath)
        content = ''.join(content)

        content = content.replace(' ', '\n')
        r = re.compile(r'''\n+''', re.M | re.S)
        content = r.sub('\n', content)

        content = Utils.transform_coding(content.strip())
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



# 该类提取新华网, 判断url是图片版/时政版, 并采取相应措施
class XinhuaExtract(object):

    def __init__(self):
        pass


    def parse_response(self, response, item):
        url = response.url

        if re.match("http://news.xinhuanet.com/photo/.*", url):  # 图片版
            xe = XinhuaPhotoExtract()
            xe.parse_response(response, item)

        elif re.match("http://news.xinhuanet.com/politics/.*", url):  # 时政版
            xe = XinhuaPoliticsExtract()
            xe.parse_response(response, item)

        else:
            item.urlhash = None





if __name__ == '__main__':
    item = Item()
    # url = 'http://news.xinhuanet.com/politics/2014-08/07/c_1111984461.htm'
    url = 'http://news.xinhuanet.com/photo/2014-08/03/c_126827156_2.htm'
    response = requests.get(url)

    e = XinhuaExtract()
    e.parse_response(response, item)

    print item.title
    print item.publishedtime
    print item.content