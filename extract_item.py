#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import re
import time
import chardet
import requests
import lxml
import random
import pymysql
import ip_pool

from time_transform import TimeTransform
from extract_content import ExtractContent
from utils import USER_AGENTS, Utils



class Item(object):

    def __init__(self):
        self.publishedtime = None
        self.source = None
        self.title = None
        self.summary = None
        self.content = None
        self.url = None
        self.typename = None



class ClassifyItem(object):

    def __init__(self, classfy_dict):
        self.classfy_dict = classfy_dict


    def classfy_item(self, item):
        typename = []
        text = item.title + item.content

        for each in self.classfy_dict.keys():
            for word in self.classfy_dict[each]:
                if word in text:
                    typename.append(each)
                    break

        if typename:
            item.typename = ','.join(typename)
        else:
            item.typename = ''



class ExtractItem(object):

    def __init__(self, starttime, endtime, allwords, classfy_dict,
                 user_agents, conn, webpages_table, log_table):

        self.starttime = starttime
        self.endtime = endtime
        self.allwords = allwords
        self.user_agents = user_agents

        self.conn = conn
        self.webpages_table = webpages_table
        self.log_table = log_table

        self.extractContent = ExtractContent()
        self.classfyItem = ClassifyItem(classfy_dict)


    def log_item(self, item, info):
        try:
            cur = self.conn.cursor()
            sql = '''INSERT INTO `%s` VALUES (null, '%s', '%s', null)''' % (self.log_table,
                                                                            info,
                                                                            item.url)

            cur.execute(sql)
            self.conn.commit()

        except Exception as e:
            pass


    def save_item(self, item):
        try:
            cur = self.conn.cursor()
            sql = '''INSERT INTO `%s` VALUES (null, '%s', '%s', '%s', '%s', '%s', '%s', '%s', null)''' % (self.webpages_table,
                                                                                                          item.publishedtime,
                                                                                                          item.typename,
                                                                                                          item.source,
                                                                                                          item.title,
                                                                                                          item.summary,
                                                                                                          item.content,
                                                                                                          item.url)
            cur.execute(sql)
            self.conn.commit()

            with open(('html/%s'%item.title).split()[0], 'w') as f:
                f.write(item.url + '\n' + item.content)

        except Exception as e:
            pass


    def parse_time(self, t):
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


    def get_realurl(self, tmp_url):
        times = 5
        while times:
            try:
                header = {'User-Agent': self.user_agents[random.randint(0, len(self.user_agents) - 1)]}
                tmp_page = requests.get(tmp_url, headers=header, allow_redirects=False)

                if tmp_page.status_code == 200:
                    urlMatch = re.search(r'URL=\'(.*?)\'', tmp_page.content.encode('utf-8'), re.S)
                    return urlMatch.group(1)
                elif tmp_page.status_code == 302:
                    return tmp_page.headers.get('location')

            except:
                pass

            times -= 1
            time.sleep(1)
        return None


    def get_html_request(self, url):
        times = 5
        while times:
            try:
                header = {'User-Agent': self.user_agents[random.randint(0, len(self.user_agents) - 1)]}
                req = requests.get(url, headers=header, timeout=4)
                if req.status_code == 200:
                    return req
            except:
                pass

            times -= 1
            time.sleep(1)
        return None


    def substring(self, text):
        if text:
            text = re.sub('&nbsp;', ' ', text)
            text = re.sub('&gt;', '>', text)
            text = re.sub('&lt;', '<', text)
        return text


    def judge_item(self, item):
        for w in self.allwords:
            if w not in item.title and w not in item.summary and w not in item.content:
                return False
        return True


    def get_publishedtime(self, element):
        res = element.xpath(".//div[@class='bbs f13']/text()")
        if res:
            res = res[0]
            res = res[res.index('发帖时间'.decode('utf8'))+5:]
        else:
            res = element.xpath(".//div[@class='c-abstract']//span[@class=' newTimeFactor_before_abs m']/text()")
            if res:
                res = res[0]
            else:
                return None

        res = self.parse_time(res.strip())
        if res < self.starttime or res >= self.endtime:
            return False
        return res



    def extract_item(self, element, source):
        item = Item()
        item.source = Utils.transform_coding(source)

        # 提取发布时间publishedtime
        publishedtime = self.get_publishedtime(element)
        if publishedtime is None:
            item.publishedtime = None
        elif publishedtime is False:
            return None
        else:
            item.publishedtime = TimeTransform.struct_to_string(publishedtime)

        # 提取标题title（百度给出的标题）
        try:
            title = eval(element.xpath(".//div[@class='c-tools']//@data-tools")[0])['title']
            title = title.split('_')[0].split('-')[0]
            item.title = Utils.transform_coding(title)
        except:
            return None

        # 提取摘要summary（百度给出的摘要）
        try:
            summary = re.sub(element.xpath(".//div[@class='c-abstract']//span//text()")[0], '', ''.join(element.xpath(".//div[@class='c-abstract']//text()")), 1)
            item.summary = Utils.transform_coding(summary)
        except:
            try:
                summary = ''.join(element.xpath(".//div[@class='c-abstract']//text()"))
                item.summary = Utils.transform_coding(summary)
            except:
                return None

        # 提取真实url
        tmp_url = eval(element.xpath(".//div[@class='c-tools']//@data-tools")[0])['url']
        url = self.get_realurl(tmp_url)
        if not url:
            return None
        if not url.startswith('http://weibo.com') and not url.startswith('http://t.qq.com') and not item.publishedtime:
            return None
        item.url = url
        self.log_item(item, 'Get item')

        # 提取内容content（从原始网页提取）, 针对微博重新提取发布时间publishedtime
        req = self.get_html_request(url)
        if not req:
            item.content = ''
        else:
            content = self.extractContent.extract_content(req, item.url)
            if not isinstance(content, list) and not isinstance(content, tuple):
                content = self.substring(content)
                item.content = content
            else:
                content, t = content
                if item.publishedtime:
                    content = self.substring(content)
                    item.content = content
                elif not t:
                    return None
                elif t >= self.starttime and t < self.endtime:
                    item.publishedtime = TimeTransform.struct_to_string(t)
                    content = self.substring(content)
                    item.content = content
                else:
                    return None

        # 再次判断是否包含指定的检索词
        if not self.judge_item(item):
            self.log_item(item, 'Drop item not containing keywords')
            return None

        # 计算分类typename
        self.classfyItem.classfy_item(item)
        self.log_item(item, 'Classify item')

        # 统一编码
        for k in item.__dict__.keys():
            try:
                item.__dict__[k] = item.__dict__[k].encode('utf8').strip()
            except:
                pass

        self.save_item(item)
        self.log_item(item, 'Save item')
        return item