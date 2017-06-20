#!/usr/bin/env python2
# encoding: utf-8

# 该文件用于提取网页的正文部分，针对通用型网页

import re
import time
import lxml
import random
from utils.utils import Utils
import lxml.html.soupparser as soupparser


# 通用型页面内容提取方法
class ExtractContent(object):

    def __init__(self):
        pass


    # 去除javascript、stylesheet、注释（<script>....</script> and <style>....</style> <!-- xxx -->)
    def remove_js_css(self, content):
        r = re.compile(r'''<script.*?</script>''', re.I|re.M|re.S)
        s = r.sub('', content)
        r = re.compile(r'''<style.*?</style>''', re.I|re.M|re.S)
        s = r.sub('', s)
        r = re.compile(r'''<!--.*?-->''', re.I|re.M|re.S)
        s = r.sub('', s)
        r = re.compile(r'''<meta.*?>''', re.I|re.M|re.S)
        s = r.sub('', s)
        r = re.compile(r'''<ins.*?</ins>''', re.I|re.M|re.S)
        s = r.sub('', s)
        return s


    # 去除多空行
    def remove_empty_line(self, content):
        r = re.compile(r'''^\s+$''', re.M|re.S)
        s = r.sub('', content)
        r = re.compile(r'''\n+''', re.M|re.S)
        s = r.sub('\n', s)
        return s


    def remove_any_tag(self, s):
        s = re.sub(r'''<[^>]+>''', '', s)
        return s.strip()


    def remove_any_tag_but_a(self, s):
        text = re.findall(r'''<a[^r][^>]*>(.*?)</a>''', s, re.I|re.M|re.S)
        text_b = self.remove_any_tag(s)
        return len(''.join(text)), len(text_b)


    def remove_image(self, s, n=5):
        image = 'a' * n
        r = re.compile(r'''<img.*?>''', re.I|re.M|re.S)
        s = r.sub(image, s)
        return s


    def remove_video(self, s, n=10):
        video = 'a' * n
        r = re.compile(r'''<embed.*?>''', re.I|re.M|re.S)
        s = r.sub(video, s)
        return s


    def sum_max(self, values):
        cur_max = values[0]
        glo_max = -999999
        left, right = 0, 0
        for index, value in enumerate(values):
            cur_max += value
            if (cur_max > glo_max):
                glo_max = cur_max
                right = index
            elif (cur_max < 0):
                cur_max = 0

        for i in range(right, -1, -1):
            glo_max -= values[i]
            if abs(glo_max) < 0.00001:
                left = i
                break

        return left, right+1


    # 根据密度提取正文
    def method_1(self, content, k=1, delta=8):
        tmp = content.split('\n')
        group_value = []

        for i in range(0, len(tmp), k):
            group = '\n'.join(tmp[i:i+k])
            group = self.remove_image(group)
            group = self.remove_video(group)
            text_a, text_b = self.remove_any_tag_but_a(group)
            temp = (text_b - text_a) - delta
            group_value.append(temp)

        left, right = self.sum_max(group_value)
        return left, right, len('\n'.join(tmp[:left])), len('\n'.join(tmp[:right]))


    # 根据常见的main模块的xpath, 预先提取出大致正文
    def get_main_block(self, response):
        response.encoding = Utils.get_response_encoding(response)

        try:
            tree = soupparser.fromstring(response.text)

            for t in ['main', 'main_content']:
                path = "//body//div[@class='{}']".format(t)
                content = tree.xpath(path)
                if content:
                    return ''.join([lxml.etree.tostring(i, encoding='utf8', method='html') for i in content])

            for t in ['main_content']:
                path = "//body//div[@id='{}']".format(t)
                content = tree.xpath(path)
                if content:
                    return ''.join([lxml.etree.tostring(i, encoding='utf8', method='html') for i in content])

        except:
            return response.text

        return response.text


    # 重新整理段落格式
    def rearrage_paragraph(self, content):
        all_p = re.findall(r'''<p.*?>(.*?)</p>''', content, re.I | re.M | re.S)
        if not all_p or list(set(all_p)) == ['']:
            r = re.compile(r'<.*?>', re.I | re.M | re.S)
            s = r.sub(' ', content)
        else:
            r = [lxml.etree.HTML('<p>' + i + '</p>').xpath('//p')[0].xpath('string(.)') for i in all_p]
            s = '\n'.join(r)
        return s.strip()


    # 替换一些html的特殊字符
    def substring(self, text):
        if text:
            text = re.sub('&nbsp;', ' ', text)
            text = re.sub('&gt;', '>', text)
            text = re.sub('&lt;', '<', text)
        return text


    # 本类主函数, 通用型网页正文提取
    def extract_content(self, response):
        try:
            content = self.get_main_block(response)
            content = self.remove_empty_line(self.remove_js_css(content))
            left, right, x, y = self.method_1(content)

            content = '\n'.join(content.split('\n')[left:right])
            content = Utils.transform_coding(content)
            content = self.rearrage_paragraph(content)
            content = self.substring(content)
            return content

        except:
            return ''



# 通用的、提取item信息
class CommonExtract(object):

    def __init__(self):
        pass


    def parse_response(self, response, item):
        ec = ExtractContent()
        content = ec.extract_content(response)
        item.content = content.strip('\n')


