# with open("comment03.txt",'w',encoding='utf-8') as f:
#     print(f.write("hello"))
import re
import xlwt
import os
from snownlp import SnowNLP
import json

def fileInput(file, name):
    try:
        input_dir = os.path.join('Input')
        os.makedirs(input_dir, exist_ok=True)
        input_path = os.path.join(input_dir, name + '.txt')
        with open(input_path, 'w', encoding='utf-8') as f:
            f.write(file)
        return 1
    except Exception as e:
        print('原始数据写入出现问题:', e)
        return 0

def fileProcess(filename):
    input_path = os.path.join('Input', filename + '.txt')
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # 处理 mtopjsonp 回调格式
        json_str = content[content.find('(')+1:content.rfind(')')]
        data = json.loads(json_str)
        comments = []
        dates = []
        # 提取评论内容和日期
        if 'data' in data and 'rateList' in data['data']:
            for item in data['data']['rateList']:
                feedback = item.get('feedback', '').strip()
                date = item.get('feedbackDate', '').strip()
                if feedback:  # 只要有内容的评论
                    comments.append(feedback)
                    dates.append(date)
        return [comments, dates]

def fileOutput(list, name):
    if list is None or len(list) < 2:
        return 0
    try:
        comment_dir = os.path.join('Output', 'comment')
        date_dir = os.path.join('Output', 'date')
        os.makedirs(comment_dir, exist_ok=True)
        os.makedirs(date_dir, exist_ok=True)
        comment_path = os.path.join(comment_dir, name + '.txt')
        date_path = os.path.join(date_dir, name + '.txt')
        with open(comment_path, 'w', encoding='utf-8') as f1:
            for comment in list[0]:
                f1.write(comment + '\n')
        with open(date_path, 'w', encoding='utf-8') as f2:
            for date in list[1]:
                f2.write(date + '\n')
        return 1
    except Exception as e:
        print('清洗后写入出现问题:', e)
        return 0

def CreatExcelFile(filename):
    workBook = xlwt.Workbook()
    workSheet = workBook.add_sheet('dataAnalysis')

    comment_dir = os.path.join('Output', 'comment')
    date_dir = os.path.join('Output', 'date')
    commentDirs = os.listdir(comment_dir)
    dateDirs = os.listdir(date_dir)
    count = 0
    for name in commentDirs:
        comment_path = os.path.join(comment_dir, name)
        date_path = os.path.join(date_dir, name)
        with open(comment_path, 'r', encoding='utf-8') as f1:
            with open(date_path, 'r', encoding='utf-8') as f2:
                Date = f2.readlines()
                for line in f1.readlines():
                    count += 1
                    line = line.strip()
                    try:
                        date = Date[(count - 1) % 20].strip()
                    except:
                        print("发生角标越界，已忽略")

                    # 情感分析
                    try:
                        s = SnowNLP(line)
                        sy = s.sentiments
                    except:
                        print("分词为空，已忽略")
                    # 导入excel中
                    workSheet.write(count, 1, line)
                    workSheet.write(count, 0, date)
                    workSheet.write(count, 2, sy)
    workBook.save(filename + '.xls')







