#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import re
import time

from utils.utils import Utils
from utils.time_transform import TimeTransform



# 根据百度的搜索结果页面, 解析百度给出的、item的title等信息
class ParseItem(object):

    def __init__(self, source):
        self.source = source  # 所属网站


    # 转换发布时间的格式
    def trans_time(self, t):
        if '日'.decode('utf8') in t:
            t = t[: t.index('日'.decode('utf8'))+1]
            t = TimeTransform.date_to_struct(t)
            return t

        if '前'.decode('utf8') in t:
            if '天'.decode('utf8') in t:
                delta_d = int(t[: t.index('天'.decode('utf8'))])
                t = time.gmtime(time.time() - delta_d*24*60*60)
                return t
            elif '小时'.decode('utf8') in t:
                delta_H = int(t[: t.index('小时'.decode('utf8'))])
                t = time.gmtime(time.time() - delta_H*60*60)
                return t
            elif '分钟'.decode('utf8') in t:
                delta_M = int(t[: t.index('分钟'.decode('utf8'))])
                t = time.gmtime(time.time() - delta_M*60)
                return t
            elif '秒'.decode('utf8') in t:
                delta_S = int(t[: t.index('秒'.decode('utf8'))])
                t = time.gmtime(time.time() - delta_S)
                return t

        return time.localtime()


    # 解析发布时间publishedtime
    def parse_publishedtime(self, element):
        res = element.xpath(".//div[@class='bbs f13']/text()")  # 搜索百度贴吧

        if res:
            res = res[0]
            res = res[res.index('发帖时间'.decode('utf8')) + 5:]
        else:
            res = element.xpath(".//div[@class='c-abstract']//span[@class=' newTimeFactor_before_abs m']/text()")
            if res:
                res = res[0]
            else:
                return None

        res = res.split()[0]
        res = TimeTransform.struct_to_string(TimeTransform.date_to_struct(res))
        return res


    # 提取标题title
    def parse_title(self, element):
        try:
            title = eval(element.xpath(".//div[@class='c-tools']//@data-tools")[0])['title']
            title = title.split('_')[0].split('-')[0]
            title = Utils.transform_coding(title)
            return title
        except:
            return None


    # 提取摘要summary
    def parse_summary(self, element):
        try:
            summary = re.sub(element.xpath(".//div[@class='c-abstract']//span//text()")[0], '',
                             ''.join(element.xpath(".//div[@class='c-abstract']//text()")), 1)
            summary = Utils.transform_coding(summary)
            return summary

        except:
            try:
                summary = ''.join(element.xpath(".//div[@class='c-abstract']//text()"))
                summary = Utils.transform_coding(summary)
                return summary
            except:
                return None


    # 提取百度给出的url（非真实url）
    def parse_tmpurl(self, item):
        tmp_url = eval(item.xpath(".//div[@class='c-tools']//@data-tools")[0])['url']
        return tmp_url


    def parse_item(self, item, element):
        item.source = Utils.transform_coding(self.source)
        item.url = self.parse_tmpurl(element)
        item.title = self.parse_title(element)
        item.summary = self.parse_summary(element)
        item.publishedtime = self.parse_publishedtime(element)
