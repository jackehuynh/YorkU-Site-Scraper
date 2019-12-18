# -*- coding: utf-8 -*-

import os.path
import csv
import scrapy
import re

fa = 'faculty'  # LE
sj = 'subject'  # EECS
cn = 'course number'  # 2011
cr = 'credit amount'  # 3.00
ay = 'academic year'  # 2019
ss = 'study session'  # FW

link = 'https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq?fa=' + \
    fa + '&sj=' + sj + '&cn=' + cn + '&cr=' + cr + '&ay=' + ay + '&ss=' + ss
# 'https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq?fa=LE&sj=EECS&cn=1019&cr=3.00&ay=2019&ss=FW

# Gets list of course names and it's course code
class CourseScraper(scrapy.Spider):
    csv_location = "csv/"
    name = "course_codes"

    def start_requests(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'}
        file_name = self.csv_location + "subjects.csv"
        urls = []

        with open(file_name, mode="r") as file:
            reader = csv.reader(file, delimiter=',')
            year = "2019"
            session = "FW"

            for data in reader:
                faculty = data[2]
                subject = data[0]
                url = "https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq1?faculty=" + \
                    faculty + "&subject=" + subject + "&academicyear=" + \
                    year + "&studysession=" + session
                urls.append(url)

        for url in urls:
            yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def parse(self, response):
        # default mode to set to file is to write
        file_mode = "w"
        file_name = self.csv_location + "courseinfo.csv"

        # check if file exists, append, else create and set buffer to write
        if os.path.isfile(file_name):
            file_mode = "a"
        else:
            file_mode = "w"

        # parses course code and name ex: AP/ADMS 1500 3.00
        course_codes = response.css('td[width="16%"]::text').getall()
        course_names = response.css('td[width="24%"]::text').getall()
        #course_site = response.css('td[width="30%"]').css('a::attr(href)').getall()

        with open(file_name, mode=file_mode, encoding="utf-8", newline='') as file:
            writer = csv.writer(file)

            for (code, name) in zip(course_codes, course_names):
                
                course_dict = self.parse_course_and_subject_code(code)
                #writer.writerow([code, name])
                writer.writerow([course_dict['faculty'],
                                 course_dict['subject'],
                                 course_dict['code'],
                                 course_dict['credit'], name])

    def parse_course_and_subject_code(self, course):
        bar = re.sub('\s+', ' ', course).strip()
        course_arr = bar.split(" ")

        arr = course_arr[0].split("/")
        faculty = arr[0]
        course_subject = arr[1]
        course_code = course_arr[1]
        credit_amount = course_arr[2]

        course_dict = {'faculty': faculty,
                       'subject': course_subject,
                       'code': course_code,
                       'credit': credit_amount}

        return course_dict
