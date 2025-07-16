#!/usr/bin/env python
# encoding: utf-8

import taobao
import filePreRegular
# import dataAnalysis as DA
import configparser
import time
import random
import os

config_path = os.path.join(os.path.dirname(__file__), 'Infor.conf')
cp = configparser.RawConfigParser()
cp.read(config_path, encoding='utf-8')

#1
print('数据爬取开始')
print('-'*20)
for i in range(0,int(cp.get('taobao','pageNumber'))):
    filename = cp.get('taobao','name')+str(i)
    result = taobao.crawlerTaobao(i+1)
    if "令牌过期" in result or "FAIL_SYS_TOKEN_EXOIRED" in result:
        # print("令牌过期，跳过写入Input/xtool0.txt")
        continue  # 或直接break
    else:
        filePreRegular.fileInput(result, filename)
    list = filePreRegular.fileProcess(filename)
    filePreRegular.fileOutput(list,filename)
    # print("已爬取第{}页评论".format(i))
    time.sleep(random.randint(20,30))

# # 取消注释，生成Excel报表
# print('数据获取成功，开始生成报表')
# print('-'*20)
# print('准备生成Excel...')
# filePreRegular.CreatExcelFile(cp.get('taobao','name'))
# print('Excel生成完毕，检查文件是否存在')
# print('-'*20)

# # 取消注释，生成图表
# print('正在生成图表...')
# DA.commentByDay()
# DA.sentiment()
# DA.perDayCommentSy()
# print("图表生成成功！，请在Image文件夹下查看")
