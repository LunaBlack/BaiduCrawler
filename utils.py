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


USER_AGENTS = ['Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20130406 Firefox/23.0',
               'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0',
               'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533+(KHTML, like Gecko) Element Browser 5.0',
               'IBM WebExplorer /v0.94', 'Galaxy/1.0 [en] (Mac OS X 10.5.6; U; en)',
               'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
               'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14',
               'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1468.0 Safari/537.36',
               'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; TheWorld)']



class Utils(object):

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