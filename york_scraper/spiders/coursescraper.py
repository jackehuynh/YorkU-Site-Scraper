# -*- coding: utf-8 -*-

import os.path
import csv
import scrapy
import re

# Gets list of course names and it's course code
class CourseScraper(scrapy.Spider):
    csv_location = "csv/"
    name = "course_codes"

    def start_requests(self):
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'}
        file_name = self.csv_location + "subjects.csv"
        urls = []

        with open(file_name, mode="r") as file:
            reader = csv.DictReader(file, delimiter=',')
            year = "2019"
            session = "FW"

            for data in reader:
                faculty = data['faculty']
                subject = data['subject_code']

                url = "https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq1?faculty=" + \
                    faculty + "&subject=" + subject + "&academicyear=" + \
                    year + "&studysession=" + session
                urls.append(url)

        for url in urls:
            yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def parse(self, response):
        # default mode set to file is to write
        file_mode = "w"
        file_name = self.csv_location + "courses.csv"

        # check if file exists, append, else create file and write to it
        if os.path.isfile(file_name):
            file_mode = "a"
        else:
            file_mode = "w"

        # parses course code and name ex: AP/ADMS 1500 3.00
        course_codes = response.css('td[width="16%"]::text').getall()
        course_names = response.css('td[width="24%"]::text').getall()

        with open(file_name, mode=file_mode, encoding="utf-8", newline='') as file:
            header_fields = ['faculty','subject','code','credit','name']
            writer = csv.DictWriter(file,fieldnames=header_fields)

            # write header only once (when it's the first time writing to file)
            if file_mode is 'w':
                writer.writeheader()

            for (code, name) in zip(course_codes, course_names):                
                course_dict = self.parse_course_and_subject_code(code, name)
                writer.writerow(course_dict)

    def parse_course_and_subject_code(self, course, course_name):
        
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
        TODO: remove extra " characters in some course's names
        '''
        if name.find('\"') != -1:
            name = re.sub('\"', '', name)

        course_dict = {'faculty': faculty,
                       'subject': course_subject,
                       'code': course_code,
                       'credit': credit_amount,
                       'name': name}

        return course_dict
