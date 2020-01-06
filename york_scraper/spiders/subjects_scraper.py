import scrapy
import csv
import json
from york_scraper.items import YorkSubjectItem

# grabs list of subjects from York's subject page
class SubjectScraper(scrapy.Spider):
    name = "subjects"
    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': 'csv/subjects.csv',
        'FEED_EXPORT_FIELDS': ['faculty', 'subject', 'name', 'expanded_name', 'url'],
        'ITEM_PIPELINES': {
            'york_scraper.pipelines.YorkSubjectPipeline' : 200
        }
    }

    with open ('data/faculty.json', 'r') as f:
        faculty_dict = json.load(f)

    def start_requests(self):
        start_url = ["https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm"]

        # obtain url to subjects page
        yield scrapy.Request(url=start_url[0], callback=self.set_subject_url)

    def set_subject_url(self, response):
        u = "https://w2prod.sis.yorku.ca"

        # response selector should output /App/WebObjects/cdm.woa/.. 
        # it's the first result of the ul tag with class=bodytext
        url = u + response.css("ul.bodytext").css("a::attr(href)").get()
        yield scrapy.Request(url=url, callback=self.get_subjects)

    def get_subjects(self, response):
        '''
        TODO: 
        1) When Summer 2020 courses are released on the site, switch to selenium to handle
        scraping of course subjects due to use of AJAX on this page. In addition, can possibly
        stop scraping for 2019-2020 Fall/Winter courses at this point.

        2) Have session name as a dictionary field?
        '''
        # list of session names (ie. Fall/Winter 2019-2020 or Summer 2020)
        session_list = response.css('select[name="sessionPopUp"]').css("option::text").getall()
        
        # list of subjects and its corresponding faculties (ie. ACTG - Accounting - (SB, ED))
        subject_list = response.css('select[name="subjectPopUp"]').css("option::text").getall()

        year = '2019'
        session = 'FW'

        for subjects in subject_list:
            subject_arr = subjects.split("-", 1)
            subject_arr_2 = subject_arr[1].split('- (')
            subject_code = subject_arr[0].strip()
            subject_name = subject_arr_2[0].strip()
            
            faculty = subject_arr_2[1].replace(")","").replace(" ","").split(",")
               
            for i in range(len(faculty)):
                item = YorkSubjectItem()
                item['faculty'] = faculty[i]
                item['subject'] = subject_code
                item['name'] = subject_name
                item['expanded_name'] = self.faculty_dict[faculty[i]]
                item['url'] = "https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq1?faculty=" + \
                    faculty[i] + "&subject=" + subject_code + "&academicyear=" + year + "&studysession=" + session
                yield item