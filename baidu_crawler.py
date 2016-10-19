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

from time_transform import TimeTransform
from extract_item import Item, ExtractItem
from utils import USER_AGENTS, Utils



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
                    tree = lxml.etree.HTML(req.text)
                    res = tree.xpath(path)
                    if len(res) != 0:
                        return req
            except:
                pass

            times -= 1
            time.sleep(5)
        return req


    def read_nextpage(self, html, param):
        n = 1
        path = "//div[@id='page']/a/text()"
        res = lxml.etree.HTML(html).xpath(path)
        while '下一页>' in res:
            n += 1
            try:
                param[param.keys()[0]]['pn'] = (n - 1) * 10
                req = self.get_req(param.values()[0])
                html = req.text
                res = lxml.etree.HTML(html).xpath(path)
                self.out_queue.put({param.keys()[0]: html})
            except:
                pass


    def run(self):
        while not self.queue.empty():
            p = self.queue.get()
            try:
                req = self.get_req(p.values()[0])
                res = req.text
                self.read_nextpage(res, p)
                self.out_queue.put({p.keys()[0]: res})
                self.queue.task_done()
            except:
                pass



class ExtractHtml(threading.Thread):

    def __init__(self, queue, starttime, endtime, allwords, user_agents):
        threading.Thread.__init__(self)
        self.queue = queue
        self.user_agents = user_agents
        self.extractItem = ExtractItem(starttime, endtime, allwords, classfy_dict, user_agents, conn, webpages_table, log_table)


    def get_item(self, html, name):
        path = "//div[@id='content_left']//div[@class='result c-container ']"
        tree = lxml.etree.HTML(html)
        results = tree.xpath(path)
        for i in results:
            item = self.extractItem.extract_item(i, name)


    def run(self):
        while not self.queue.empty():
            i = self.queue.get()
            name = i.keys()[0]
            html = i[name]
            self.get_item(html, name)



def define_urls(allwords, start_urls):
    params = Queue()
    for name, url in start_urls.items():
        params.put({name: {'q2': ' '.join(allwords).encode('gbk'),
                           'q6': urllib2.urlparse.urlparse(url).hostname}})
    return params


allwords = ['地震'.decode('utf8'), '鲁甸'.decode('utf8'), '6.5级'.decode('utf8')]
start_urls = {'腾讯新闻':'http://news.qq.com', '百度新闻':'http://news.baidu.com'}
queue = define_urls(allwords, start_urls)
out_queue = Queue()
t = ThreadCrawl(queue, out_queue, USER_AGENTS)
t.setDaemon(True)
t.start()
t.join()

# def html_parser(html, n):
#     path = "//div[@id='content_left']//div[@class='c-abstract']/text()"  # Xpath of abstract in BaiDu search results
#     tree = lxml.etree.HTML(html)
#     results = tree.xpath(path)
#     text = [line.strip() for line in results]
#     text_str = ''
#     if len(text) == 0:
#         print "No!", n
#     else:
#         for i in text:
#             i = i.strip()
#             text_str += i
#     return text_str



e = ExtractHtml(out_queue, '2014年8月1日', '2016年9月1日', USER_AGENTS)
e.setDaemon(True)
e.start()
e.join()


# n = 1
# while not out_queue.empty():
#     i = out_queue.get()
#     with open('%d.html'%n, 'w') as f:
#         f.write(i.values()[0])
#     n += 1
#     print i.keys()[0], html_parser(i.values()[0], n)
#     print '===' * 30







# class BaiduSearch(object):
#
#     def __init__(self):
#         pass
#
#
#     def download_html(self, keywords, proxy):
#         key = {'wd': keywords}
#         headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko'}
#         web_content = requests.get("http://www.baidu.com/s?", params=key, headers=headers, proxies=proxy, timeout=4)
#         content = web_content.text
#         return content
#
#
#     def html_parser(self, html):
#         path = "//div[@id='content_left']//div[@class='c-abstract']/text()"  # Xpath of abstract in BaiDu search results
#         tree = lxml.etree.HTML(html)
#         results = tree.xpath(path)
#         text = [line.strip() for line in results]
#         text_str = ''
#         if len(text) == 0:
#             print "No!"
#         else:
#             for i in text:
#                 i = i.strip()
#                 text_str += i
#         return text_str
#
#
#     def extract_all_text(self, keyword_dict, keyword_text):
#         """
#         ========================================================
#         Extract all text of elements in company dict
#         There are 3 strategies:
#             1. Every time appears "download timeout", I will choose another proxy.
#             2. Every 200 times after I crawl, change a proxy.
#             3. Every 2000,0 times after I crawl, Re-construct an ip_pool.
#
#         ========================================================
#         Parameters
#         ---------
#         keyword_dict: the keyword name dict.
#         keyword_text: file that save all text.
#
#         Return
#         ------
#         """
#
#         cn = open(keyword_dict, 'r')
#         print ">>>>>read success<<<"
#         with open(keyword_text, 'w') as ct:
#             flag = 0  # Change ip
#             switch = 0  # Change the proxies list
#             useful_proxies = []
#             new_ip = ''
#             for line in cn:
#                 if switch % 20000 == 0:
#                     switch = 1
#                     ip_list = ip_pool.get_all_ip(1)
#                     useful_proxies = ip_pool.get_the_best(1, ip_list, 1.5, 20)
#                 switch += 1
#                 try:
#                     if flag % 200 == 0 and len(useful_proxies) != 0:
#                         flag = 1
#                         rd = random.randint(0, len(useful_proxies)-1)
#                         new_ip = useful_proxies[rd]
#                         print new_ip
#                     flag += 1
#                     proxy = {'http': 'http://'+new_ip}
#                     content = download_html(line, proxy)
#                     raw_text = html_parser(content)
#                     raw_text = raw_text.replace('\n', ' ')
#                     print raw_text
#                     ct.write(line.strip()+'\t'+raw_text+'\n')
#                 except Exception, e:
#                     rd = random.randint(0, len(useful_proxies)-1)
#                     new_ip = useful_proxies[rd]
#                     print 'download error: ', e
#         ct.close()
#         cn.close()
#
#
# def main():
#     keyword_dict = 'data/samples.txt'
#     keyword_text = 'data/results.txt'
#     extract_all_text(keyword_dict, keyword_text)
#
# if __name__ == '__main__':
#     main()

