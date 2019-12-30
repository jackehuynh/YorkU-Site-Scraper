# -*- coding: utf-8 -*-

import os.path
import csv
import scrapy
import re
from york_scraper.items import YorkCourseItem

# Gets list of course names and it's course code
class CourseScraper(scrapy.Spider):
    name = "course_codes"

    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': 'csv/courses.csv',
        'FEED_EXPORT_FIELDS': ['faculty', 'subject', 'code', 'credit', 'name', 'url']
    }

    def start_requests(self):
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'}
        file_name = self.csv_location + "subjects.csv"
        urls = []

        '''
        TODO: add try-throw block to throw an error if file does not exist
        '''

        with open(file_name, mode="r") as file:
            reader = csv.DictReader(file, delimiter=',')
            year = "2019"
            session = "FW"

            for data in reader:
                faculty = data['faculty']
                subject = data['subject_code']

                url = "https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq1?faculty=" + \
                    faculty + "&subject=" + subject + "&academicyear=" + year + "&studysession=" + session
                urls.append(url)

        for url in urls:
            yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def parse(self, response):
        # parses course code and name ex: AP/ADMS 1500 3.00
        course_codes = response.css('td[width="16%"]::text').getall()
        course_names = response.css('td[width="24%"]::text').getall()

        for (code, name) in zip(course_codes, course_names):                
            course_dict = self.parse_course_and_subject_code(code, name)
            yield course_dict

    def parse_course_and_subject_code(self, course, course_name):
        item = YorkCourseItem()

        # Cleaning up and splitting of course string
        formatted_c_text = re.sub('\s+', ' ', course).strip()
        course_arr = formatted_c_text.split(" ")
        arr = course_arr[0].split("/")
        faculty = arr[0]
        course_subject = arr[1]
        course_code = course_arr[1]
        credit_amount = course_arr[2]
        name = re.sub('\s+', ' ', course_name).strip()

        '''
        TODO: 
        1. remove extra " characters in some course's names
        2. allow for flexible way to determine academic year and study session
        '''
        
        if name.find('\"') != -1:
            name = re.sub('\"', '', name)

        academic_year = '2019'
        study_session = 'FW'
        course_url = 'https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq?fa='+ faculty + \
              '&sj='+ course_subject +'&cn='+ course_code +'&cr=' + credit_amount + '&ay=' + academic_year + '&ss=' + study_session

        item['faculty'] = faculty
        item['subject'] = course_subject
        item['code'] = course_code
        item['credit'] = credit_amount
        item['name'] = name
        item['url'] = course_url

        return item