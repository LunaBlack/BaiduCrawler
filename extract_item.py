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

        self.starttime = TimeTransform.date_to_struct(Utils.transform_coding(starttime))
        self.endtime = TimeTransform.date_to_struct(Utils.transform_coding(endtime))
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

            with open('html/%s'%item.title, 'w') as f:
                f.write(item.url + '\n' + item.content)

        except Exception as e:
            pass


    def parse_time(self, t):
        if '日' in t:
            t = t[: t.index('日')+1]
            t = TimeTransform.date_to_struct(t)
            return t

        if '前' in t:
            if '天' in t:
                delta_d = int(t[: t.index('天')])
                t = time.gmtime(time.time() - delta_d*24*60*60)
                return t
            elif '小时' in t:
                delta_H = int(t[: t.index('小时')])
                t = time.gmtime(time.time() - delta_H*60*60)
                return t
            elif '分钟' in t:
                delta_M = int(t[: t.index('分钟')])
                t = time.gmtime(time.time() - delta_M*60)
                return t
            elif '秒' in t:
                delta_S = int(t[: t.index('秒')])
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
            if w not in item.title and w not in item.content:
                return False
        return True


    def extract_item(self, element, source):
        publishedtime = element.xpath(".//div[@class='c-abstract']//span[@class=' newTimeFactor_before_abs m']//text()")
        if not publishedtime:
            return None

        publishedtime = self.parse_time(publishedtime[0].strip())
        if publishedtime < self.starttime or publishedtime > self.endtime:
            return None

        item = Item()
        item.publishedtime = TimeTransform.struct_to_string(publishedtime)
        item.source = Utils.transform_coding(source)

        try:
            title = eval(element.xpath(".//div[@class='c-tools']//@data-tools")[0])['title']
            title = title.split('_')[0]
            item.title = Utils.transform_coding(title)
        except:
            return None

        try:
            summary = re.sub(element.xpath(".//div[@class='c-abstract']//span//text()")[0], '', ''.join(element.xpath(".//div[@class='c-abstract']//text()")), 1)
            item.summary = Utils.transform_coding(summary)
        except:
            try:
                summary = ''.join(element.xpath(".//div[@class='c-abstract']//text()"))
                item.summary = Utils.transform_coding(summary)
            except:
                return None

        tmp_url = eval(element.xpath(".//div[@class='c-tools']//@data-tools")[0])['url']
        url = self.get_realurl(tmp_url)
        if not url:
            return None
        item.url = url
        self.log_item(item, 'Get item')

        req = self.get_html_request(url)
        if req:
            content = self.extractContent.extract_content(req)
            content = self.substring(content)
            item.content = content
        else:
            item.content = ''

        if not self.judge_item(item):
            self.log_item(item, 'Drop item not containing keywords')
            return None

        self.classfyItem.classfy_item(item)
        self.log_item(item, 'Classify item')

        for k in item.__dict__.keys():
            try:
                item.__dict__[k] = item.__dict__[k].encode('utf8')
            except:
                pass

        self.save_item(item)
        self.log_item(item, 'Save item')
        return item