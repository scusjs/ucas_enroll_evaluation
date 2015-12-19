#!/usr/bin/env python
# -* - coding: UTF-8 -* -
##
# @file evaluate.py
# @brief 
# @author scusjs@foxmail.com
# @version 0.1.00
# @date 2015-12-19

import requests
import ConfigParser
from bs4 import BeautifulSoup
import sys, os
import re

class UCASEvaluate:
    def __init__(self):
        cf= ConfigParser.RawConfigParser()
        cf.read('config')
        self.username=cf.get('info', 'username')
        self.password=cf.get('info', 'password')
        self.loginUrl="http://sep.ucas.ac.cn/slogin"
        self.loginPage="http://sep.ucas.ac.cn"
        self.courseSelectionPage="http://sep.ucas.ac.cn/portal/site/226/821"
        self.studentCourseSelectionSystem="http://jwjz.ucas.ac.cn/Student/"
        self.studentCourseIndentify="http://jwjz.ucas.ac.cn/Student/Portal.aspx?Identity="
        self.studentCourseTop="http://jwjz.ucas.ac.cn/Student/DeskTopModules/TopHead.aspx"
        self.studentCourseEvaluateUrl="http://jwjz.ucas.ac.cn/Student/DeskTopModules/"
        self.headers = {
                'Host': 'sep.ucas.ac.cn',
                'Connection': 'keep-alive',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36',
                'Accept-Encoding': 'gzip, deflate, sdch',
                'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',

            }
        self.s = requests.Session()
        loginPage = self.s.get(self.loginPage, headers=self.headers)
        self.cookies = loginPage.cookies

    def login(self):
        postdata = {
            'userName' : self.username,
            'pwd' : self.password,
            'sb'       : 'sb'
        }
        response = self.s.post(self.loginUrl, data=postdata, headers=self.headers)
        if self.s.cookies.get_dict().has_key('sepuser'):
            return True
        return False

    def getCourse(self):
        response = self.s.get(self.courseSelectionPage, headers=self.headers)
        soup = BeautifulSoup(response.text)
        #print(response.text.encode('utf8'))
        coursePage = self.studentCourseIndentify + soup.noscript.contents[0].strip().split('Identity=')[1][:-2]
        response = self.s.get(coursePage)
        response = self.s.get(self.studentCourseTop)
        soup = BeautifulSoup(response.text)
        listLi = (str)(soup.select('div[class="Menubox"]')[0]).split('SwichClass(this,"MainFrame",')
        evaluateCouse = self.studentCourseEvaluateUrl + listLi[3].split('"')[1]
        response = self.s.get(evaluateCouse)
        soup = BeautifulSoup(response.text)
        courseListResource = soup.body.table.tbody.find_all('tr')[3:-2]
        courseDict = {}
        if len(courseListResource) == 0:
            self.courseDict =  courseDict
        for course in courseListResource:
            tdList = course.find_all('td')
            if tdList[-1].a is None:
                continue
            courseUrl  = tdList[-1].a['href']
            courseName = tdList[1].a.string.strip()
            evaluateFlag = tdList[-1].a.string.encode('utf-8')
            if evaluateFlag == '评估':
                courseDict[courseName] = courseUrl
        self.courseDict =  courseDict

    def evaluateCourse(self):
        if len(self.courseDict) == 0:
            print('there is no course need to be evaluated')
            return
        for course in self.courseDict:
            print('start evaluate ' + course + '...')
            evaluateUrl = self.studentCourseEvaluateUrl + 'Evaluate/' + self.courseDict[course]
            self.__evaluate(evaluateUrl)

    def __evaluate(self, evaluateUrl):
        postData = {}
        response = self.s.get(evaluateUrl)
        soup = BeautifulSoup(response.text)
        formResource = soup.body.form
        formList = formResource.contents

        for inputResource in formResource.contents:
            if (str)(inputResource).strip() != '':
                if inputResource.name == 'input':
                    postData[inputResource['name']] = inputResource['value']
                elif inputResource.name == 'table':
                    subTable = inputResource.contents[1].contents[2].td.table.find_all(attrs={'class': 'GbText'})
                    for eachTable in subTable:
                        for eachInput in eachTable.find_all('input'):
                            label = eachInput.next_sibling.string.encode('utf-8')
                            if label == '优' or label.find('优') != -1:
                                postData[eachInput['name']] = eachInput['value']
                    #subText = inputResource.contents[1].contents[4]
                    postData['rbtnList'] = 5
                postData['tbMerit'] = "本课程老师非常优秀，讲的知识也非常有用。"
                postData['tbSuggest'] = ''
                postData['tbFlaw'] = ''
                postData['btnSave'] = "保存我的评论"
        response = self.s.post(evaluateUrl, data = postData)
        if (response.text.encode('utf-8').find("<script>alert('恭喜您，提交对该课程的评论成功……')</script>") != -1):
            print('evaluate success...')
        else:
            #print(response.text)
            print('evaluate error!')








if __name__=="__main__":
    ucasEvaluate = UCASEvaluate()
    if not ucasEvaluate.login():
        print('login error, please check your username and password')
        exit()
    print('login success')
    ucasEvaluate.getCourse()
    if len(ucasEvaluate.courseDict) == 0:
        print('there is no course need to be evaluated')
        exit()
    print((str)(len(ucasEvaluate.courseDict)) + ' courses need to be evaluated...')
    ucasEvaluate.evaluateCourse()


