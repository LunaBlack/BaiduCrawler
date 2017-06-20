#!/usr/bin/env python2
# -*- coding: utf-8 -*-


# 定义item类
class Item(object):

    def __init__(self):
        self.urlhash = None
        self.publishedtime = None
        self.source = None  # 来源网站
        self.title = None
        self.summary = None  # 摘要
        self.content = None  # 正文
        self.url = None
        self.typename = None  # 分类