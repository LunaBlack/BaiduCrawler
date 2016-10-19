#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import re
import time
import chardet
import urllib2
import threading
from Queue import Queue
import requests
import lxml
import random
import ip_pool



class TimeTransform(object):

    def __init__(self):
        pass


    @staticmethod
    def transform_coding(text):
        if not isinstance(text, unicode):
            text_encode = chardet.detect(text)['encoding']
            try:
                text = text.decode(text_encode if text_encode else 'utf8')
            except Exception as e:
                pass
        return text


    @staticmethod
    def date_to_struct(date):
        try:
            t = time.strptime(date, "%Y年%m月%d日".decode('utf8'))
            return t
        except:
            return time.localtime()


    @staticmethod
    def second_to_struct(second):
        try:
            t = time.strptime(second, "%Y年%m月%d日%H时%M分%S秒".decode('utf8'))
            return t
        except:
            return time.localtime()


    @staticmethod
    def struct_to_second(struct):
        try:
            t = time.strftime("%Y%m%d%H%M%S", struct)
            return t
        except:
            return time.strftime("%Y%m%d%H%M%S", time.localtime())


    @staticmethod
    def struct_to_date(struct):
        try:
            t = time.strftime("%Y%m%d", struct)
            return t
        except:
            return time.strftime("%Y%m%d", time.localtime())


    @staticmethod
    def struct_to_string(struct):
        try:
            t = time.strftime("%Y年%m月%d日".decode('utf8'), struct)
            return t
        except:
            return time.strftime("%Y年%m月%d日".decode('utf8'), time.localtime())


