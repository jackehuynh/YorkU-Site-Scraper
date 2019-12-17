# -*- coding: utf-8 -*-

fa = 'faculty' # LE
sj = 'subject' # EECS
cn = 'course number' # 2011
cr = 'credit amount' # 3.00
ay = 'academic year' # 2019
ss = 'study session' # FW

link = 'https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq?fa='+ fa + '&sj=' + sj + '&cn=' + cn + '&cr=' + cr + '&ay=' + ay + '&ss=' + ss
# 'https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq?fa=LE&sj=EECS&cn=1019&cr=3.00&ay=2019&ss=FW

import scrapy
import csv
import os.path

# Gets list of course names and it's course code
class coursescraperSpider(scrapy.Spider):
    csv_location = "../csv/"
    name = "course_links"

    def start_requests(self):
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'}
        file_name = self.csv_location + "subjects.csv"
        urls = []

        with open(file_name, mode="r") as file:
            reader = csv.reader(file, delimiter=',')
            year = "2019"
            session = "FW"

            for data in reader:
                faculty = data[2]
                subject = data[0]
                url = "https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq1?faculty=" + faculty + "&subject=" + subject + "&academicyear=" + year + "&studysession=" + session
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

        # Courses Main site put these in a separate crawler
        url = "https://w2prod.sis.yorku.ca"

        # prints course code and credits in an array, ex: AP/ADMS 1500 3.00
        course_list = response.css('td[width="16%"]::text').getall()
        course_names = response.css('td[width="24%"]::text').getall()
        course_site = response.css('td[width="30%"]').css('a::attr(href)').getall() 

        with open(file_name, mode=file_mode, newline='') as file:
            writer = csv.writer(file)

            for (code,name,site) in zip(course_list, course_names, course_site):
                writer.writerow([code, name, url+site])
                # course['name'] = code + " " + name
                # course['link'] = url + site
                # yield {
                #     'name' : code + " " + name + " link: " + url + site
                # }