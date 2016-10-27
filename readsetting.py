# -*- coding: utf-8 -*-


import sys, os
import time
import datetime
import json
from time_transform import TimeTransform
from utils import Utils


class ReadSetting: #读取用户设置的信息,包括检索词

    def __init__(self): #初始化,读取包含用户设置信息的文件
        if getattr(sys, 'frozen', False):
            dir_ = os.path.dirname(sys.executable)
        else:
            dir_ = os.path.dirname(os.path.realpath(__file__))

        with open(os.path.join(dir_, "setting.txt"), 'r') as f:
            self.text = f.readlines()


    def read_args(self, conn, db, webpages_table):
        self.read_keywords()
        self.read_exist_urls(conn, db, webpages_table)
        self.read_classfy_dict()


    def read_keywords(self): #读取检索的关键词
        allwords = []

        for n, i in enumerate(self.text):
            if i.strip():
                text = i.strip()
                try:
                    text = text.decode('utf8')
                except:
                    try:
                        text = text.decode('utf8')
                    except:
                        pass
            else:
                continue

            text = text.split(';')

            times = text[0]
            starttime, endtime = times.split(' ')
            self.starttime = TimeTransform.date_to_struct(Utils.transform_coding(starttime))
            self.endtime = TimeTransform.datetime_to_struct((TimeTransform.date_to_datetime(Utils.transform_coding(endtime)) + datetime.timedelta(days=1)))

            if len(text) > 1:
                words = list(set(text[1].split()))
                if ' ' in words:
                    words.remove(' ')
                if '' in words:
                    words.remove('')
                allwords.extend(words)
                break
            else:
                allwords = ['地震'.decode('utf8')]
                break

        self.allwords = allwords


    def read_exist_urls(self, conn, db, webpages_table):
        cur = conn.cursor()
        cur.execute('use {db}'.format(db=db))
        cur.execute('select url from {table}'.format(table=webpages_table))
        urls = cur.fetchall()
        self.exist_urls = [i[0] for i in urls]


    def read_classfy_dict(self):
        if getattr(sys, 'frozen', False):
            dir_ = os.path.dirname(sys.executable)
        else:
            dir_ = os.path.dirname(os.path.realpath(__file__))

        with open(os.path.join(dir_, "vocabulary.json"), 'r') as f:
            self.classfy_dict = json.load(f)




if __name__ == '__main__':
    rs = ReadSetting()
