#!/usr/bin/env python2
# encoding: utf-8

# 该文件用于提取网页的正文部分，针对通用型网页

import re
import time
import lxml
import random
import requests
from utils import Utils
import lxml.html.soupparser as soupparser
from utils import USER_AGENTS



# 某些特定网站的页面内容提取方法：新浪微博、腾讯微博、百度贴吧、地震坛(论坛)
class SpecialExtractContent(object):

    def __init__(self):
        pass


    @classmethod
    def sina_weibo_content(cls, url):
        url = url.replace('weibo.com', 'weibo.cn')
        times = 3

        while times:
            times -= 1
            time.sleep(random.randint(1, 3))

            try:
                header = {'User-Agent': USER_AGENTS[random.randint(0, len(USER_AGENTS) - 1)]}
                req = requests.get(url, headers=header, timeout=4)

                if req.status_code == 200:
                    html = req.content
                    tree = lxml.etree.HTML(html)
                    content_path = "//div[@id='M_']//span[@class='ctt']/a/text() | //div[@id='M_']//span[@class='ctt']/text()"
                    content = tree.xpath(content_path)
                    if not content:
                        continue

                    content = ''.join(content)
                    content = Utils.transform_coding(content)
                    if content.startswith(':'.decode('utf8')):
                        content = content[1:]

                    time_path = "//div[@id='M_']//span[@class='ct']/text()"
                    t = tree.xpath(time_path)[0].strip()
                    t = time.strptime(t, "%Y-%m-%d %H:%M:%S")
                    return content, t

            except Exception as e:
                return '', None
        return '', None


    @classmethod
    def qq_weibo_content(cls, req):
        try:
            html = req.content
            tree = lxml.etree.HTML(html)
            content_path = "//div[@id='orginCnt']//div[@id='msginfo']/a/text() | //div[@id='orginCnt']//div[@id='msginfo']/text() | \
                            //div[@id='orginCnt']//div[@id='msginfo']/em/a/text() | //div[@id='orginCnt']//div[@id='msginfo']/em/text()"
            content = tree.xpath(content_path)

            content = ''.join(content)
            content = Utils.transform_coding(content)

            time_path = "//div[@id='orginCnt']//div[@class='pubInfo c_tx5']//a[@class='time']/text()"
            t = tree.xpath(time_path)[0].strip()
            t = time.strptime(t, "%Y年%m月%d日 %H:%M".decode('utf8'))
            return content, t

        except Exception as e:
            return '', None


    @classmethod
    def baidu_tieba_content(cls, req):
        try:
            html = req.content
            path = "//h1[@title]/text() | //h3[@title]/text() | \
                    //div[@class='p_postlist']//div[@class='d_post_content j_d_post_content '][1]/a/text() | \
                    //div[@class='p_postlist']//div[@class='d_post_content j_d_post_content '][1]/text() | \
                    //div[@class='p_postlist']//div[@class='d_post_content j_d_post_content  clearfix'][1]/a/text() | \
                    //div[@class='p_postlist']//div[@class='d_post_content j_d_post_content  clearfix'][1]/text()"

            tree = lxml.etree.HTML(html)
            content = tree.xpath(path)

            content = ''.join(content)
            content = Utils.transform_coding(content)
            content = '\n'.join(content.split(' '*12)).strip()
            return content

        except Exception as e:
            return ''


    @classmethod
    def dizhentan_content(cls, req):
        try:
            html = req.content
            path = "//h1/text() | \
                    //div[@class='postmessage firstpost']//div[@class='t_msgfontfix']//td[@class='t_msgfont']//text() | \
                    //div[@class='t_msgfontfix']//td[@class='t_msgfont']/text()"

            tree = lxml.etree.HTML(html)
            content = tree.xpath(path)

            content = '\n'.join([i.strip() for i in content])
            content = Utils.transform_coding(content)
            return content

        except Exception as e:
            return ''



# 通用型页面内容提取方法
class ExtractContent(object):

    def __init__(self):
        pass


    def remove_js_css(self, content):
        """ remove the the javascript and the stylesheet and the comment content (<script>....</script> and <style>....</style> <!-- xxx -->) """
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


    def remove_empty_line(self, content):
        """remove multi space """
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


    def get_main_block(self, req):
        req.encoding = Utils.get_req_encoding(req)

        try:
            tree = soupparser.fromstring(req.text)

            for t in ['main', 'view_text', 'main_content', 'WBA_content', 'ep-content-main', 'text clear', 'wh590 left', 'detailmain_lcon', 'detail_main_right_con', 'detialrcon']:
                path = "//body//div[@class='{}']".format(t)
                content = tree.xpath(path)
                if content:
                    return ''.join([lxml.etree.tostring(i, encoding='utf8', method='html') for i in content])

            for t in ['main_content']:
                path = "//body//div[@id='{}']".format(t)
                content = tree.xpath(path)
                if content:
                    return ''.join([lxml.etree.tostring(i, encoding='utf8', method='html') for i in content])

            if req.url.startswith('http://eq.ah.gov.cn/'):
                path = "//body//table//table//table//table//tr[11]"
                content = tree.xpath(path)
                if content:
                    return ''.join([lxml.etree.tostring(i, encoding='utf8', method='html') for i in content])

        except:
            return req.text

        return req.text


    def extract_content(self, req, url):
        if url.startswith('http://weibo.com'):
            return SpecialExtractContent.sina_weibo_content(url)

        if url.startswith('http://t.qq.com'):
            return SpecialExtractContent.qq_weibo_content(req)

        if url.startswith('http://tieba.baidu.com'):
            return SpecialExtractContent.baidu_tieba_content(req)

        if url.startswith('http://www.dizhentan.com'):
            return SpecialExtractContent.dizhentan_content(req)

        try:
            content = self.get_main_block(req)
            content = self.remove_empty_line(self.remove_js_css(content))
            left, right, x, y = self.method_1(content)

            content = '\n'.join(content.split('\n')[left:right])
            content = Utils.transform_coding(content)

            all_p = re.findall(r'''<p.*?>(.*?)</p>''', content, re.I|re.M|re.S)
            if not all_p or list(set(all_p)) == ['']:
                r = re.compile(r'<.*?>', re.I|re.M|re.S)
                s = r.sub(' ', content)
            else:
                r = [lxml.etree.HTML('<p>'+i+'</p>').xpath('//p')[0].xpath('string(.)') for i in all_p]
                s = '\n'.join(r)
            return s

        except:
            return ''




if __name__ == '__main__':
    url = 'http://t.qq.com/p/t/433823069681890'  # 'http://www.dizhentan.com/thread-145837-1-1.html'  # 'http://news.qq.com/a/20140805/002722.htm'
    req = requests.get(url)

    e = ExtractContent()
    content = e.extract_content(req, url)
    print content
