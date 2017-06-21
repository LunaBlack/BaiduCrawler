#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import random
import threading
import time
from Queue import Queue

import pymysql
import lxml
import requests
from multiprocessing.dummy import Pool

from utils.utils import MyThread
from item import Item
from parse_item import ParseItem
from extract_item import ExtractItem
from classify_item import ClassifyItem
from write_database import WriteDatabase



# 针对每个网站构建一个爬虫, 作为单独的线程
class ThreadCrawler(object):

    def __init__(self, webname, hostname, allwords, starttime, endtime, classify_dict, webpages_table, log_table,
                 user_agents, host, port, user, password, database):
        self.webname = webname
        self.hostname = hostname
        self.allwords = allwords
        self.starttime = starttime
        self.endtime = endtime
        self.classify_dict = classify_dict
        self.baidu_rn = 50  # 百度搜索参数, 每页多少条结果

        self.webpages_table = webpages_table
        self.log_table = log_table
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database

        self.user_agents = user_agents
        self.num_thread = 100  # 线程数

        self.items_list = []
        self.writedb = WriteDatabase(log_table, webpages_table)
        self.parse = ParseItem(webname)
        self.extract = ExtractItem(hostname, user_agents, self.writedb, allwords)
        self.classify = ClassifyItem(classify_dict)


    def get_items(self):
        baidu_crawler = BaiduCrawler(self.user_agents, self.baidu_rn)
        param = {'q2': ' '.join(self.allwords).encode('gbk'),
                 'q6': self.hostname,
                 'gpc': 'stf={starttime},{endtime}|stftype=2'.format(starttime=int(time.mktime(self.starttime)),
                                                                     endtime=int(time.mktime(self.endtime))),
                 'rn': self.baidu_rn
                 }

        try:
            response = baidu_crawler.get_response(param)
            html = response.content
            baidu_crawler.read_nextpage(html, param)
        except:
            pass

        for item in baidu_crawler.items:
            self.items_list.append(item)


    def process_items(self, element):
        try:
            conn = pymysql.connect(host=self.host, port=self.port, user=self.user, passwd=self.password)
            cur = conn.cursor()
            cur.execute('SET NAMES UTF8')
            cur.execute('USE {database}'.format(database=self.database))

            if element is None:
                return

            item = Item()
            self.parse.parse_item(item, element)
            self.writedb.write_log_table(conn, item, 'Searched item')

            self.extract.extract_item(conn, item)
            if item.urlhash:
                self.classify.classfy_item(item)
                self.writedb.write_log_table(conn, item, 'Classified item')
                self.writedb.write_webpages_table(conn, item)
                self.writedb.write_log_table(conn, item, 'Save item')
                # self.print_item(item)

            conn.close()

        except Exception as e:
            pass


    def print_item(self, item):
        for k in item.__dict__.keys():
            print k, item.__dict__[k]
        print '---' * 30


    def run(self):
        self.get_items()
        pool = Pool(self.num_thread)
        pool.map(self.process_items, self.items_list)
        pool.close()
        pool.join()



# 针对每个网站构建百度爬虫, 通过百度高级搜索来进行爬取, 收集爬取到的items
class BaiduCrawler(object):

    def __init__(self, user_agents, baidu_rn):
        self.user_agents = user_agents
        self.baidu_rn = baidu_rn
        self.try_times = 3
        self.time_out = 4

        self.page_xpath = "//div[@id='page']/a/text()"
        self.item_xpath = "//div[@id='content_left']//div[@class='result c-container ']"
        self.items = []


    # 根据关键词、网站、时间范围等构建检索式, 发起请求并返回
    def get_response(self, param):
        for _ in range(self.try_times):
            try:
                header = {'User-Agent': self.user_agents[random.randint(0, len(self.user_agents) - 1)]}
                response = requests.get("http://www.baidu.com/s?", params=param, headers=header, timeout=self.time_out)

                if response.status_code == 200:
                    tree = lxml.etree.HTML(response.content)
                    items = tree.xpath(self.item_xpath)
                    if len(items) != 0:  # 搜索结果大于0
                        self.items.extend(items)
                        return response

            except:
                pass
            time.sleep(random.randint(1, 3))

        return None


    # 读取下一页
    def read_nextpage(self, html, param):
        n = 1
        res = lxml.etree.HTML(html).xpath(self.page_xpath)

        while '下一页>'.decode('utf8') in res:
            n += 1
            try:
                param['pn'] = (n - 1) * self.baidu_rn
                req = self.get_response(param)
                html = req.content
                res = lxml.etree.HTML(html).xpath(self.page_xpath)
            except:
                pass
