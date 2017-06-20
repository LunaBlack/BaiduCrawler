#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import pymysql


# 写数据库表格
class WriteDatabase(object):

    def __init__(self, log_table, webpages_table):
        self.log_table = log_table
        self.webpages_table = webpages_table


    # 记录log信息
    def write_log_table(self, conn, item, info):
        try:
            cur = conn.cursor()
            sql = '''INSERT INTO `%s` VALUES (null, '%s', '%s', null)''' % (self.log_table,
                                                                            info,
                                                                            item.url)

            cur.execute(sql)
            conn.commit()

        except Exception as e:
            pass


    # 记录爬取到的页面
    def write_webpages_table(self, conn, item):
        try:
            cur = conn.cursor()
            sql = '''INSERT INTO `%s` VALUES (null, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', null)''' % (self.webpages_table,
                                                                                                                item.urlhash,
                                                                                                                item.publishedtime,
                                                                                                                item.typename,
                                                                                                                item.source,
                                                                                                                item.title,
                                                                                                                item.summary,
                                                                                                                item.content,
                                                                                                                item.url)
            cur.execute(sql)
            conn.commit()

        except pymysql.err.IntegrityError as e:
            self.write_log_table(conn, item, 'Drop duplicated item')

        except Exception as e:
            print e