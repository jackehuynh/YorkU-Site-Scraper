fa = 'faculty'
sj = 'subject'
cn = 'course number'
cr = 'credit amount'
ay = 'academic year'
ss = 'study session'

link = 'https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq?fa='+ fa + '&sj=' + sj + '&cn=' + cn + '&cr=' + cr + '&ay=' + ay + '&ss=' + ss

import scrapy
from scrapy.selector import Selector

class coursescraperSpider(scrapy.Spider):
    name = "york_scraper"
    user_agent = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'
    
    start_urls = [
        'https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq1?faculty=LE&subject=EECS&academicyear=2019&studysession=FW',
        'https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq1?faculty=GS&subject=EECS&academicyear=2019&studysession=fw',
        'https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq1?faculty=AP&subject=ADMS&academicyear=2019&studysession=fw',
        ]
    def parse(self, response):

        # prints course code and credits in an array, ex: AP/ADMS 1500 3.00
        course_list = response.css('td[width="16%"]::text').extract()
        course_names = response.css('td[width="24%"]::text').extract()

        for rows in course_list:
            yield {
                'course code' : rows
            }

        for row in course_names:
            yield {
                'course name' : row
            }
