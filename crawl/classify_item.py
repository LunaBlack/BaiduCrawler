#!/usr/bin/env python2
# -*- coding: utf-8 -*-


# 根据title、content等信息对item分类
class ClassifyItem(object):

    def __init__(self, classfy_dict):
        self.classfy_dict = classfy_dict


    def classfy_item(self, item):
        typename = []
        text = item.title + item.summary + item.content

        for each in self.classfy_dict.keys():
            for word in self.classfy_dict[each]:
                if word.encode('utf-8') in text:
                    typename.append(each)
                    break

        if typename:
            item.typename = ','.join(typename).encode('utf-8')
        else:
            item.typename = ''
