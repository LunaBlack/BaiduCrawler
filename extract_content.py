#!/usr/bin/env python2
# encoding: utf-8

# 该文件用于提取网页的正文部分，针对通用型网页

import re
import lxml
from utils import Utils



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


    def remove_image(self, s, n=50):
        image = 'a' * n
        r = re.compile(r'''<img.*?>''', re.I|re.M|re.S)
        s = r.sub(image, s)
        return s


    def remove_video(self, s, n=100):
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


    def method_1(self, content, k=1):
        tmp = content.split('\n')
        group_value = []

        for i in range(0, len(tmp), k):
            group = '\n'.join(tmp[i:i+k])
            group = self.remove_image(group)
            group = self.remove_video(group)
            text_a, text_b = self.remove_any_tag_but_a(group)
            temp = (text_b - text_a) - 20
            group_value.append(temp)

        left, right = self.sum_max(group_value)
        return left, right, len('\n'.join(tmp[:left])), len('\n'.join(tmp[:right]))


    def get_main_div(self, html):
        try:
            path = "//body//div[@class='main']"
            tree = lxml.etree.HTML(html)
            content = tree.xpath(path)
            if content:
                return ''.join([lxml.etree.tostring(i, encoding='utf8', method='html') for i in content])
            else:
                return html
        except:
            return html



    def extract_content(self, content):
        try:
            content = self.get_main_div(content)
            content = self.remove_empty_line(self.remove_js_css(content))
            left, right, x, y = self.method_1(content)

            content = '\n'.join(content.split('\n')[left:right])
            content = Utils.transform_coding(content)
            r = re.compile(r'<.*?>', re.I|re.M|re.S)
            s = r.sub(' ', content)
            return s

        except:
            return ''


if __name__ == '__main__':
    f = open('1.html', 'r')
    text = f.read()

    e = ExtractContent()
    content = e.extract_content(text)
    print content
    f.close()