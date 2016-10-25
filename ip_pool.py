# # -*- coding:utf-8 -*-
# import sys
# import requests
# import time
# from lxml import etree
# reload(sys)
# sys.setdefaultencoding('utf-8')
#
#
# # Get all ip in a specified page
# def get_proxies_from_site(current_page):
#     """
#     Parameter
#     --------
#     current_page: int, the current page's number.
#     Return
#     ------
#     ip_list: list, a list with all 20*page ip with their corresponding ports.
#     """
#     url = 'http://www.66ip.cn/areaindex_1/'+str(current_page)+'.html'  # The ip resources url
#     url_xpath = '/html/body/div[last()]//table//tr[position()>1]/td[1]/text()'
#     port_xpath = '/html/body/div[last()]//table//tr[position()>1]/td[2]/text()'
#     results = requests.get(url)
#     tree = etree.HTML(results.text)
#     url_results = tree.xpath(url_xpath)    # Get ip
#     port_results = tree.xpath(port_xpath)  # Get port
#     urls = [line.strip() for line in url_results]
#     ports = [line.strip() for line in port_results]
#
#     ip_list = []
#     if len(urls) != len(ports):
#         print "No! It's crazy!"
#     else:
#         for i in range(len(urls)):
#             # Match each ip with it's port
#             full_ip = urls[i]+":"+ports[i]
#             print full_ip
#             ip_list.append(full_ip)
#     return ip_list
#
#
# #  Get all ip in 0~page pages website
# def get_all_ip(page):
#     ip_list = []
#     for i in range(page):
#         cur_ip_list = get_proxies_from_site(i+1)
#         for item in cur_ip_list:
#             ip_list.append(item)
#     for item in ip_list:
#         print item
#     return ip_list
#
#
# # Use http://lwons.com/wx to test if the server is available.
# def get_valid_proxies(proxies, timeout):
#     # You may change the url by yourself if it didn't work.
#     url = 'http://lwons.com/wx'
#     results = []
#     for p in proxies:
#         proxy = {'http': 'http://'+p}
#         succeed = False
#         try:
#             start = time.time()
#             r = requests.get(url, proxies=proxy, timeout=timeout)
#             end = time.time()
#             if r.text == 'default':
#                 succeed = True
#         except Exception as e:
#             print 'error:', p
#             succeed = False
#         if succeed:
#             print 'succeed: '+p+'\t'+str(end-start)
#             results.append(p)
#         time.sleep(1)  # Avoid frequent crawling
#     results = list(set(results))
#     return results
#
#
# def get_the_best(round, proxies, timeout, sleeptime):
#     """
#     ========================================================
#     With a strategy of N round test to find secure and stable
#     ip, during each round it will sleep a period of time to
#     avoid the 'famous 15 minutes".
#     ========================================================
#     Parameters
#     ----------
#     round: int, a number to decide how many round the test will hold.
#     proxies: list, the ip list to be detected.
#     timeout:  float, for each ip, decide the longest time we assume it's disconnected.
#     sleeptime: float, how many seconds it sleep between two round test.
#     """
#     for i in range(round):
#         print '\n'
#         print ">>>>>>>Round\t"+str(i+1)+"<<<<<<<<<<"
#         proxies = get_valid_proxies(proxies, timeout)
#         if i != round-1:
#             time.sleep(sleeptime)
#     return proxies
#
#
# def main():
#     ip_list = get_all_ip(2)
#     proxies = get_the_best(3, ip_list, 1.5, 60)  # The suggested parameters
#     print "\n\n\n"
#     print ">>>>>>>>>>>>>>>>>>>The Final Ip<<<<<<<<<<<<<<<<<<<<<<"
#     for item in proxies:
#         print item
#
#
# if __name__ == '__main__':
#     main()
#
#
#
# -*- coding: utf-8 -*-

import urllib2
import random

ip_list=['119.6.136.122','114.106.77.14']
#使用一组ip调用random函数来随机使用其中一个ip
url = "http://www.ip181.com/"
proxy_support = urllib2.ProxyHandler({'http':random.choice(ip_list)})
#参数是一个字典{'类型':'代理ip:端口号'}
opener = urllib2.build_opener(proxy_support)
#定制opener
opener.add_handler=[('User-Agent','Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36')]
#add_handler给加上伪装
urllib2.install_opener(opener)
response = urllib2.urlopen(url)

print response.read().decode('gbk')