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
        #'https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq1?faculty=LE&subject=EECS&academicyear=2019&studysession=FW',
        #'https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq1?faculty=GS&subject=EECS&academicyear=2019&studysession=fw',
        #'https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq1?faculty=AP&subject=ADMS&academicyear=2019&studysession=fw',
        ]
    def parse(self, response):
        # Courses Main site put these in a separate crawler
        url = "https://w2prod.sis.yorku.ca"

        # prints course code and credits in an array, ex: AP/ADMS 1500 3.00
        course_list = response.css('td[width="16%"]::text').extract()
        course_names = response.css('td[width="24%"]::text').extract()
        course_site = response.css('td[width="30%"]').css('a::attr(href)').extract() 
        # gets links to 'subject' course on page before selecting term and courses
        #s1 = response.css("ul.bodytext").css("a::attr(href)").extract()
        #subject_link = s1[0]

        #url = url + subject_link

        print(url)
        for (code,name,site) in zip(course_list, course_names, course_site):
            yield {
                #'course code' : rows
                'name' : code + " " + name + " link: " + url + site
            }

        '''
        for row in course_names:
            yield {
                'course name' : row
            }
        '''
