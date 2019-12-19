fa = 'faculty'  # LE
sj = 'subject'  # EECS
cn = 'course number'  # 2011
cr = 'credit amount'  # 3.00
ay = 'academic year'  # 2019
ss = 'study session'  # FW

# 'https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq?fa=LE&sj=EECS&cn=1019&cr=3.00&ay=2019&ss=FW

import scrapy
import re

class CourseInfoScraper(scrapy.Spider):
    csv_location = "csv/"
    name = "course_info"

    def start_requests(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'
        }

        file_name = self.csv_location + "courses.csv"
        urls = []

        '''
        TODO: 
        1) add try-throw block to throw an error if file does not exist
        2) make it customizable for other terms not just FW
        '''
        
        with open(self.file_name, mode="r") as file:
            reader = csv.DictReader(file, delimiter=',')
            ay = "2019"  # academic year
            ss = "FW"    # study session

            for data in reader:
                faculty = data['faculty']
                subject = data['subject']
                credit = data['credit']
                course_number = data['code']

                url = 'https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq?fa='+ faculty + \
                      '&sj='+ subject +'&cn='+ course_number +'&cr=' + credit + '&ay=2019&ss=' + ss
                urls.append(url)

            for url in urls:
                yield scrapy.Request(url=url, headers=headers, callback=self.set_course_url)

    def set_course_url(self, response):
        u = "https://w2prod.sis.yorku.ca"
        url = u + response.xpath('//a[contains(text(), "Fall")]').css("a:attr(href)").get()
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        file_name = self.csv_location + "course_info.csv"

        # HTML element that contains section of course info (description, title, times)
        table_body = response.css("table[cellpadding='10']")

        # extract all text within <p> tags in the table body
        p_text = table_body.css('p::text').getall()

        course_description = p_text[1]

        #course_info_body = table_body.css("table[width='100%']").get()

        # extracts html element (red bar) containing term and section
        terms = table_body.css("td[width='50%']").css("b::text").getall()
        sections = table_body.css("td[width='50%']").css("font::text").getall()

        # extracts the table below the term/section containing times, location, cat #, etc.
        info_tables = table_body.css("table[border='2']").css("td[valign='TOP']::text")

        # xpath version of above
        test = response.xpath('//table[@border="2"]//tr')

        # grabs the entire table holding the courses
        body = response.css("table[border='2']")

        # returns array of days and the location corresponding to those days
        day = body[i].css("td[width='15%']::text").getall()
        loc = body[i].css("td[width='45%']::text").getall()

        # example used is EECS 1019
        cat = body[i].css("td[width='20%']").getall()[-2] # need to clean up
        cat_id = re.sub('<td width=\"20%\" valign=\"TOP\">', '', cat).strip()
        cat_id = re.sub('<br></td>', '', cat_id).strip()
        cat_id = cat_id.split('<br>') # ['Y21A01 (LE EECS)', 'E10C01 (SC MATH)']


        inst = body[i].css("td[width='15%']").css("a::text").getall() # ['Andranik Mirzaian']
        time = body[i].css("td[width='35%']").getall() # ['time_slot']
        time_slot = time[1].css("tr").getall() # ['day1', 'day2']
        day_1 = time_slot[0].css("td::text").getall() # M 17:30 90 LAS C 
        day_2 = time_slot[1].css("td::text").getall() # R 17:30 90 LAS C
        
        '''
        TODO: add info_dict to scrapy's item feature
        '''

        '''
        nested = []
        # for loop
        nested_dict = {'day': day,
                       'start': start,
                       'duration': duration,
                       'location': location}
        # nested.append(nested_dict)

        nested_inst = ['inst1, inst2, etc.']
        '''

        '''
        Example of how the rest api's structure is going to look like
        course = {'course_name': name,
                  'description': desc,
                  'subject': subject,
                  'credit': credit,
                  'Pre-requisites': yes or no, if yes have a list of the courses,
                  'info': ['info_dict']
                  }
        '''

        '''
        info_dict = {
                     'Type': lect,
                     'Time': nested_dict,
                     'cat': cat,
                     'instructor': nested_inst,
                     'notes': note 
                     }
        '''