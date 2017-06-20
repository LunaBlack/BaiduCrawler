#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import hashlib
import random
import re
import time
import requests

from extract.common import CommonExtract
from extract.special import ChinaExtract, ChinaCnExtract, CeaExtract, CencExtract, CsiExtract, CnrExtract, \
    DizhentanExtract, GovExtract, HuanqiuExtract, IfengExtract, EqiglExtract, CeaigpExtract, PeopleExtract, QqExtract, \
    SinaExtract, SinaWeiboExtract, SohuExtract, SouhcnExtract, TencentWeiboExtract, TiebaExtract, WangyiExtract, XinhuaExtract



# 解析出真实url, 请求页面, 提取item相应字段信息
class ExtractItem(object):

    def __init__(self, hostname, user_agents, writedb, allwords):
        self.user_agents = user_agents
        self.try_times = 3
        self.time_out = 4

        self.hostname = hostname
        self.ec = self.judge_extract_methods()

        self.writedb = writedb
        self.allwords = allwords


    # 判断采用哪个类来提取信息
    def judge_extract_methods(self):
        if self.hostname.endswith('china.com.cn'):
            ec = ChinaCnExtract()
        elif self.hostname.endswith('cea.gov.cn'):
            ec = CeaExtract()
        elif self.hostname.endswith('cenc.ac.cn'):
            ec = CencExtract()
        elif self.hostname.endswith('csi.ac.cn'):
            ec = CsiExtract()
        elif self.hostname.endswith('china.com'):
            ec = ChinaExtract()
        elif self.hostname.endswith('cnr.cn'):
            ec = CnrExtract()
        elif self.hostname.endswith('dizhentan.com'):
            ec = DizhentanExtract()
        elif self.hostname.endswith('gov.cn'):
            ec = GovExtract()
        elif self.hostname.endswith('huanqiu.com'):
            ec = HuanqiuExtract()
        elif self.hostname.endswith('ifeng.com'):
            ec = IfengExtract()
        elif self.hostname.endswith('eq-igl.ac.cn'):
            ec = EqiglExtract()
        elif self.hostname.endswith('cea-igp.ac.cn'):
            ec = CeaigpExtract()
        elif self.hostname.endswith('people.com.cn'):
            ec = PeopleExtract()
        elif self.hostname.endswith('qq.com'):
            ec = QqExtract()
        elif self.hostname.endswith('weibo.com'):
            ec = SinaWeiboExtract()
        elif self.hostname.endswith('sina.com.cn'):
            ec = SinaExtract()
        elif self.hostname.endswith('sohu.com'):
            ec = SohuExtract()
        elif self.hostname.endswith('southcn.com'):
            ec = SouhcnExtract()
        elif self.hostname.endswith('t.qq.com'):
            ec = TencentWeiboExtract()
        elif self.hostname.endswith('tieba.baidu.com'):
            ec = TiebaExtract()
        elif self.hostname.endswith('163.com'):
            ec = WangyiExtract()
        elif self.hostname.endswith('xinhuanet.com'):
            ec = XinhuaExtract()
        else:
            ec = CommonExtract()
        return ec


    # 根据百度给出的url, 获取真实url
    def get_realurl(self, item):
        for _ in range(self.try_times):
            try:
                header = {'User-Agent': self.user_agents[random.randint(0, len(self.user_agents) - 1)]}
                response = requests.get(item.url, headers=header, allow_redirects=False)

                if response.status_code == 200:
                    urlMatch = re.search(r'URL=\'(.*?)\'', response.content.encode('utf-8'), re.S)
                    url = urlMatch.group(1)
                    return url

                elif response.status_code == 302:
                    url = response.headers.get('location')
                    return url

            except:
                pass
            time.sleep(random.randint(1, 3))

        return None


    # 根据真实url, 发起请求, 获取response
    def request_realurl(self, item):
        for _ in range(self.try_times):
            try:
                header = {'User-Agent': self.user_agents[random.randint(0, len(self.user_agents) - 1)]}
                response = requests.get(item.url, headers=header, timeout=self.time_out)
                if response.status_code == 200:
                    return response
            except:
                pass
            time.sleep(random.randint(1, 3))

        return None


    # 处理一些特殊字符
    def substring(self, text):
        if text:
            text = re.sub('&nbsp;', ' ', text)
            text = re.sub('&gt;', '>', text)
            text = re.sub('&lt;', '<', text)
        return text


    # 判断是否包含指定的检索词
    def judge_item(self, item):
        for w in self.allwords:
            w = w.encode('utf-8')
            if w not in item.title and w not in item.summary and w not in item.content:
                return False
        return True


    # 提取item相应字段的信息
    def extract_item(self, conn, item):
        url = self.get_realurl(item)
        if not url:  # 无法获取真实url, 丢弃
            self.writedb.write_log_table(conn, item, 'Drop item which can not get real url')
            item.urlhash = None
            return

        item.url = url
        response = self.request_realurl(item)
        if not response:  # 无法请求获得页面, 丢弃
            self.writedb.write_log_table(conn, item, 'Drop item which can not get response')
            item.urlhash = None
            return

        self.writedb.write_log_table(conn, item, 'Get item')
        item.urlhash = hashlib.md5(item.url).hexdigest()
        ec = self.ec
        ec.parse_response(response, item)
        if not item.urlhash and not isinstance(ec, CommonExtract):  # 指定方法出错则采用通用方法
            item.urlhash = hashlib.md5(item.url).hexdigest()
            ec = CommonExtract()
            ec.parse_response(response, item)

        if not item.urlhash:  # Extract item失败, 丢弃
            self.writedb.write_log_table(conn, item, 'Drop item which can not be parsed')
            return

        self.writedb.write_log_table(conn, item, 'Parsed item')
        item.title = self.substring(item.title)
        item.summary = self.substring(item.summary)
        item.content = self.substring(item.content)

        # 统一编码
        for k in item.__dict__.keys():
            try:
                item.__dict__[k] = item.__dict__[k].encode('utf8').strip()
            except Exception as e:
                pass

        if not self.judge_item(item):  # 不包含指定关键词, 丢弃
            self.writedb.write_log_table(conn, item, 'Drop item not containing keywords')
            item.urlhash = None
            return
