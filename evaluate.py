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
import re
import sys
reload(sys)
sys.setdefaultencoding('utf8')

class UCASEvaluate:
    def __init__(self):
        self.__readCoursesId()
        self.enrollCount = {}
        cf= ConfigParser.RawConfigParser()
        cf.read('config')
        self.username=cf.get('info', 'username')
        self.password=cf.get('info', 'password')
        self.loginUrl="http://sep.ucas.ac.cn/slogin"
        self.enroll = cf.getboolean('action', 'enroll')
        self.evaluate = cf.getboolean('action', 'evaluate')
        self.loginPage="http://sep.ucas.ac.cn"
        self.courseSelectionPage="http://sep.ucas.ac.cn/portal/site/226/821"
        self.studentCourseSelectionSystem="http://jwjz.ucas.ac.cn/Student/"
        self.studentCourseIndentify="http://jwjz.ucas.ac.cn/Student/Portal.aspx?Identity="
        self.studentCourseTop="http://jwjz.ucas.ac.cn/Student/DeskTopModules/TopHead.aspx"
        self.studentCourseEvaluateUrl="http://jwjz.ucas.ac.cn/Student/DeskTopModules/"
        self.selectCourseUrl = "http://jwjz.ucas.ac.cn/Student/DesktopModules/Course/SelectCourse.aspx"
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
        self.courseId = open("courseid", "r").read().splitlines();

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
    
    def __readCoursesId(self):
        coursesFile = open('./courseid', 'r')
        self.coursesId = {}
        for line in coursesFile.readlines():
            line = line.strip().split(':')
            courseId = line[0]
            isDegree = False
            if len(line) == 2 and line[1] == "on":
                isDegree = True
            self.coursesId[courseId] = isDegree

    def enrollCourses(self):
        response = self.s.get(self.courseSelectionPage, headers=self.headers)
        soup = BeautifulSoup(response.text)
        #print(response.text.encode('utf8'))
        try:
            indentity = str(soup.noscript).split('Identity=')[1].split('"'[0])[0]
            coursePage = self.studentCourseIndentify + indentity
            response = self.s.get(coursePage)
            response = self.s.get(self.studentCourseTop)
            soup = BeautifulSoup(response.text)
            listLi = (str)(soup.select('div[class="Menubox"]')[0]).split('SwichClass(this,"MainFrame",')
            enrollCouseUrl = self.studentCourseEvaluateUrl + listLi[1].split('"')[1]
            response = self.s.get(enrollCouseUrl)
            soup = BeautifulSoup(response.text)
            urlSession = (str)(soup.body.form['action']).strip().split('=')[1]
            coursesId = self.coursesId.copy()
            
            while len(coursesId) > 0:
                for eachCourse in coursesId.keys():
                    if eachCourse in response.text:
                        print("course " + eachCourse + " is in your coursetable")
                        del coursesId[eachCourse]
                        continue
                    if self.enrollCount.has_key(eachCourse):
                        self.enrollCount[eachCourse] += 1
                    else:
                        self.enrollCount[eachCourse] = 1
                    result = self.__enrollCourse(urlSession, eachCourse, coursesId[eachCourse], self.enrollCount[eachCourse])
                    if result:
                        del coursesId[eachCourse]
        except Exception as e:
            print("system error")
            print e
            #self.enrollCourses()
            pass
        except KeyboardInterrupt:
            print("Bye")
    
        
        
        


    def __enrollCourse(self, urlSession, courseId, isDegree, count):
        
        selectCourseUrl = self.selectCourseUrl + "?CourseTypeString=" + courseId[:2] + "&s=" + urlSession
        response = self.s.get(selectCourseUrl)
        soup = BeautifulSoup(response.text)
        
        postData = {}
        postData['__VIEWSTATE'] = soup.find(attrs={"name": "__VIEWSTATE"})['value']
        postData['__VIEWSTATEGENERATOR'] = soup.find(attrs={"name": "__VIEWSTATEGENERATOR"})['value']
        postData['__EVENTVALIDATION'] = soup.find(attrs={"name": "__EVENTVALIDATION"})['value']
        
        dataTable = soup.body.form.table.contents[1].find_all('tr')
        courseName = "存放当前需要选择的课程"
        for course in dataTable:
            if courseId in course.text:
                codeLink = course.find(id=re.compile('_CodeLink'))
                if courseId != codeLink.string:
                    continue
                courseCheckBoxName = course.find(id=re.compile('_ItemCheckBox'))['name']
                degreeCheckBoxName = course.find(id=re.compile('_DegreeCheckBox'))['name']
                courseName = course.find(id=re.compile('_NameLink')).string
                
                postData[courseCheckBoxName] = "on"
                if isDegree:
                    postData[degreeCheckBoxName] = "on"
                print("select " + courseName + "..." + str(count) + " times")
    
        if len(postData) == 3:
            print "no such course"
            return True
        postData['SureBtn'] = "确定提交选课"
        
        
        response = self.s.post(selectCourseUrl, data = postData)
        soup = BeautifulSoup(response.text)
        
        if soup.head.find('script') == None:
            if courseName in response.text:
                print("choose success")
                return True
            print("course full")
            return False
        print soup.head.find('script').string.split('"')[1]
        return False

    def getCourse(self):
        response = self.s.get(self.courseSelectionPage, headers=self.headers)
        soup = BeautifulSoup(response.text)
        #print(response.text.encode('utf8'))
        indentity = str(soup.noscript).split('Identity=')[1].split('"'[0])[0]
        coursePage = self.studentCourseIndentify + indentity
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
    if ucasEvaluate.enroll:
        print('Enrolling course...\n')
        ucasEvaluate.enrollCourses()
    if ucasEvaluate.evaluate:
        print('Evaluating course...\n')
        ucasEvaluate.getCourse()
        if len(ucasEvaluate.courseDict) == 0:
            print('there is no course need to be evaluated')
            exit()
        print((str)(len(ucasEvaluate.courseDict)) + ' courses need to be evaluated...')
        ucasEvaluate.evaluateCourse()


