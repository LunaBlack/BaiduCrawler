#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os, sys
import re
import time
import chardet
import urllib2
import threading
from Queue import Queue
import requests
import lxml
import random
import pymysql

from time_transform import TimeTransform
from extract_item import Item, ExtractItem
from utils import USER_AGENTS, Utils
from readsetting import ReadSetting



class ThreadCrawl(threading.Thread):

    def __init__(self, queue, out_queue, user_agents):
        threading.Thread.__init__(self)
        self.queue = queue
        self.out_queue = out_queue
        self.user_agents = user_agents


    def get_req(self, param):
        times = 5
        while times:
            try:
                header = {'User-Agent': self.user_agents[random.randint(0, len(self.user_agents) - 1)]}
                req = requests.get("http://www.baidu.com/s?", params=param, headers=header, timeout=4)
                if req.status_code == 200:
                    path = "//div[@id='content_left']//div[@class='c-abstract']/text()"  # Xpath of abstract in BaiDu search results
                    tree = lxml.etree.HTML(req.content)
                    res = tree.xpath(path)
                    if len(res) != 0:
                        return req
            except:
                pass

            times -= 1
            time.sleep(1)
        return req


    def read_nextpage(self, html, param):
        n = 1
        path = "//div[@id='page']/a/text()"
        res = lxml.etree.HTML(html).xpath(path)
        while '下一页>'.decode('utf8') in res:
            n += 1
            try:
                param[param.keys()[0]]['pn'] = (n - 1) * 10
                req = self.get_req(param.values()[0])
                html = req.content
                res = lxml.etree.HTML(html).xpath(path)
                self.out_queue.put({param.keys()[0]: html})
            except:
                pass


    def run(self):
        while not self.queue.empty():
            p = self.queue.get()
            try:
                req = self.get_req(p.values()[0])
                res = req.content
                self.read_nextpage(res, p)
                self.out_queue.put({p.keys()[0]: res})
                self.queue.task_done()
            except:
                pass



class ExtractHtml(threading.Thread):

    def __init__(self, queue, starttime, endtime, allwords, classfy_dict, user_agents, conn, webpages_table, log_table):
        threading.Thread.__init__(self)
        self.queue = queue
        self.user_agents = user_agents
        self.extractItem = ExtractItem(starttime, endtime, allwords, classfy_dict, user_agents, conn, webpages_table, log_table)


    def get_item(self, html, name):
        path = "//div[@id='content_left']//div[@class='result c-container ']"
        tree = lxml.etree.HTML(html)
        results = tree.xpath(path)
        for i in results:
            self.extractItem.extract_item(i, name)


    def run(self):
        while not self.queue.empty():
            i = self.queue.get()
            name = i.keys()[0]
            html = i[name]
            self.get_item(html, name)



class Spider(object):

    def __init__(self):
        pass


    def read_mysql_setting(self):
        if getattr(sys, 'frozen', False):
            dir_ = os.path.dirname(sys.executable)
        else:
            dir_ = os.path.dirname(os.path.realpath(__file__))

        mysql_file = os.path.join(dir_, "mysql_setting.txt")
        with open(mysql_file, 'r') as f:
            text = f.readlines()

        for n, i in enumerate(text):
            if i.startswith("host="):
                self.host = i.strip().split('=')[1]
            elif i.startswith("port="):
                self.port = int(i.strip().split('=')[1])
            elif i.startswith("user="):
                self.user = i.strip().split('=')[1]
            elif i.startswith("password="):
                self.password = i.strip().split('=')[1]
            elif i.startswith("database="):
                self.database = i.strip().split('=')[1]
            elif i.startswith("webpages_table="):
                self.webpages_table = i.strip().split('=')[1]
            elif i.startswith("urls_table="):
                self.urls_table = i.strip().split('=')[1]
            elif i.startswith("log_table="):
                self.log_table = i.strip().split('=')[1]


    def update_database(self):
        conn_flag = 0  # 标记是否成功连接数据库
        number = 0  # 标记尝试连接数据库的次数, 上限为10次

        while 1:
            try:
                self.conn = pymysql.connect(host=self.host, port=self.port, user=self.user, passwd=self.password)
                cur = self.conn.cursor()
                conn_flag = 1
            except Exception as e:
                pass
            if conn_flag:
                break
            elif number == 10:
                return False
            else:
                number += 1
                time.sleep(3)

        try:
            # 创建数据库
            cur.execute('CREATE DATABASE IF NOT EXISTS %s '
                        'DEFAULT CHARSET utf8 COLLATE utf8_general_ci' % self.database)
            cur.execute('USE %s' % self.database)

            # 创建网页表
            sql = '''CREATE TABLE IF NOT EXISTS %s (
            id INT(11) NOT NULL AUTO_INCREMENT,
            publishedtime VARCHAR(30) DEFAULT NULL,
            typename VARCHAR(255) DEFAULT NULL,
            source VARCHAR(255) DEFAULT NULL,
            title VARCHAR(255) DEFAULT NULL,
            summary LONGTEXT,
            content LONGTEXT,
            url VARCHAR(255) DEFAULT NULL,
            crawledtime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id))''' % self.webpages_table
            cur.execute(sql)
            self.conn.commit()

        except Exception, e:
            return False

        return True


    def read_starturls(self):
        cur = self.conn.cursor()
        cur.execute('SET NAMES UTF8')
        cur.execute('USE %s' % self.database)
        cur.execute('SELECT url, notes FROM {table}'.format(table=self.urls_table))
        res = cur.fetchall()
        self.start_urls = {i[0]: i[1] for i in res}


    def run(self):
        rs = ReadSetting()
        rs.read_args(self.conn, self.database, self.webpages_table)
        self.read_starturls()



        # self.start_urls = {}
        # self.start_urls['http://dizhentan.com/'] = '地震坛'



        for url, name in self.start_urls.items():
            queue = Queue()
            out_queue = Queue()
            queue.put({name: {'q2': ' '.join(rs.allwords).encode('gbk'),
                              'q6': urllib2.urlparse.urlparse(url).hostname}})

            thread_baidu = ThreadCrawl(queue, out_queue, USER_AGENTS)
            thread_baidu.setDaemon(True)
            thread_baidu.start()
            thread_baidu.join()

            thread_extract = ExtractHtml(out_queue, rs.starttime, rs.endtime, rs.allwords, rs.classfy_dict, USER_AGENTS, self.conn, self.webpages_table, self.log_table)
            thread_extract.setDaemon(True)
            thread_extract.start()
            thread_extract.join()

        self.conn.close()



if __name__ == '__main__':
    testspider = Spider()
    testspider.read_mysql_setting()
    if testspider.update_database():
        testspider.run()
    else:
        sys.exit(-1)
