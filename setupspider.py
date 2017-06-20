#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# 本程序用于启动爬虫


import os
import sys
import time
import urllib2
from Queue import Queue
from multiprocessing.dummy import Pool

import pymysql

from readsetting import ReadSetting
from crawl.crawler import ThreadCrawler
from utils.utils import USER_AGENTS, MyThread


# 读取数据库参数, 连接数据库, 启动爬虫
class Spider(object):

    def __init__(self):
        # self.num_crawler = 3  # 最多同时爬取的站点数
        self.user_agents = USER_AGENTS


    # 从文件 mysql_setting.txt 中读取数据库的各项参数
    def read_mysql_setting(self):
        if getattr(sys, 'frozen', False):
            dir_ = os.path.dirname(sys.executable)
        else:
            dir_ = os.path.dirname(os.path.realpath(__file__))

        mysql_file = os.path.join(dir_, "setting/mysql_setting.txt")
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


    # 连接到mysql, 尝试创建数据库, 创建保存抓取网页的表格
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
                return False  # 数据库连接失败
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
            urlhash CHAR(32) UNIQUE,
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


    # 读取初始urls（即需要爬取的站点）
    def read_starturls(self):
        cur = self.conn.cursor()
        cur.execute('SET NAMES UTF8')
        cur.execute('USE %s' % self.database)
        cur.execute('SELECT url, notes FROM {table}'.format(table=self.urls_table))
        res = cur.fetchall()
        self.start_urls = {i[0]: i[1] for i in res}


    # 清空相关表格
    def clean_tables(self):
        cur = self.conn.cursor()
        cur.execute('USE %s' % self.database)
        cur.execute('DELETE FROM {table}'.format(table=self.log_table))
        cur.execute('DELETE FROM {table}'.format(table=self.webpages_table))
        self.conn.commit()


    # # 针对每个起始url（即需要爬取的站点）构建一个爬虫
    # def create_crawler(self, host_name):
    #     webname, hostname = host_name
    #     crawler = ThreadCrawler(webname, hostname, self.allwords, self.starttime, self.endtime, self.classify_dict,
    #                             self.webpages_table, self.log_table, self.user_agents,
    #                             self.host, self.port, self.user, self.password, self.database)
    #     crawler.run()
    #
    #
    # # 启动爬虫
    # def run(self):
    #     self.clean_tables()  # 清空表格, 准备记录本次数据
    #
    #     rs = ReadSetting()
    #     rs.read_args()
    #     self.read_starturls()
    #     self.allwords = rs.allwords
    #     self.starttime = rs.starttime
    #     self.endtime = rs.endtime
    #     self.classify_dict = rs.classfy_dict
    #
    #     hostname_list = []
    #     for url, webname in self.start_urls.items():
    #         hostname = urllib2.urlparse.urlparse(url).hostname
    #         if hostname.startswith('www.'):
    #             hostname = hostname[4:]
    #         hostname_list.append([webname, hostname])
    #
    #     pool = Pool(self.num_crawler)
    #     pool.map(self.create_crawler, hostname_list)
    #     pool.close()
    #     pool.join()
    #
    #     self.conn.close()


    # 针对每个起始url（即需要爬取的站点）构建一个爬虫
    def create_crawler(self, webname, hostname):
        crawler = ThreadCrawler(webname, hostname, self.allwords, self.starttime, self.endtime, self.classify_dict,
                                self.webpages_table, self.log_table, self.user_agents,
                                self.host, self.port, self.user, self.password, self.database)
        crawler.run()

    # 启动爬虫
    def run(self):
        self.clean_tables()  # 清空表格, 准备记录本次数据

        rs = ReadSetting()
        rs.read_args()
        self.read_starturls()
        self.allwords = rs.allwords
        self.starttime = rs.starttime
        self.endtime = rs.endtime
        self.classify_dict = rs.classfy_dict

        hostname_list = []
        for url, webname in self.start_urls.items():
            hostname = urllib2.urlparse.urlparse(url).hostname
            if hostname.startswith('www.'):
                hostname = hostname[4:]
            hostname_list.append([webname, hostname])

        for webname, hostname in hostname_list:
            self.create_crawler(webname, hostname)

        self.conn.close()




if __name__ == '__main__':
    testspider = Spider()
    testspider.read_mysql_setting()
    if testspider.update_database():
        testspider.run()
    else:
        sys.exit(-1)