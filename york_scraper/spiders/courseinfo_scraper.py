fa = 'faculty'  # LE
sj = 'subject'  # EECS
cn = 'course number'  # 2011
cr = 'credit amount'  # 3.00
ay = 'academic year'  # 2019
ss = 'study session'  # FW

# 'https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq?fa=LE&sj=EECS&cn=1019&cr=3.00&ay=2019&ss=FW

import scrapy
import csv
import re

class CourseInfoScraper(scrapy.Spider):
    csv_location = "csv/"
    name = "course_info"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'
    }
    
    u = "https://w2prod.sis.yorku.ca"

    # Keys to construct the dictionaries
    course_info_keys = ["type", "meet_info", "cat", "instructor", "notes"]
    course_keys = ["name", "description", "offerings"]
    nested_keys = ["term", "section", "course_info"]

    '''
    faculty_list = []
    subject_list = []      
    course_numbers = []
    credits = []
    '''

    def start_requests(self):
        file_name = self.csv_location + "courses.csv"
        urls = []

        '''
        TODO: 
        1) add try-throw block to throw an error if file does not exist
        2) make it customizable for other terms not just FW
        '''
        
        with open(file_name, mode="r") as file:
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
                '''
                self.subject_list.append(subject)
                self.course_numbers.append(course_number)
                self.credits.append(credit)
                '''
        #t = 'https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq?fa=GS&sj=HUMA&cn=6000B&cr=3.00&ay=2019&ss=FW'
        #s = 'https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq?fa=AP&sj=WRIT&cn=2003&cr=6.00&ay=2019&ss=FW'
        #yield scrapy.Request(url=t, headers=self.headers, callback=self.set_course_url, dont_filter = True)

        for url in urls:
           yield scrapy.Request(url=url, headers=self.headers, callback=self.set_course_url, dont_filter = True)

    def set_course_url(self, response):
        url = self.u + response.xpath('//a[contains(text(), "Fall")]/@href').get()

        # Sends request to the 'Timetable' link on the course's page
        yield scrapy.Request(url=url, headers=self.headers, callback=self.parse, dont_filter = True)

    def parse(self, response):
        course = dict.fromkeys(self.course_keys)

        '''
        TODO:
        1. Separate pre-requisites into a separate dictionary key
        2. Extract language of instructions
        '''

        # HTML element that contains section of description, title, and times
        table_body = response.css("table[cellpadding='10']")

        # extract all text within <p> tags in the outer table body containing all the inner tables with the course info
        #p_text = table_body.css('p::text').getall()
        course_description = table_body.xpath('//b[contains(text(), "Course Description")]/../following-sibling::p[1]').get()
        course['description'] = course_description.replace('<p>','').replace('</p>','').replace('\r','').replace('\t','').replace('\n','').replace('\\','')

        # extracts html element (red bar) containing term and section
        t_s = table_body.css("td[width='50%']")
        terms = [string.strip() for string in t_s.css("b::text").getall()]
        sections = [string.strip() for string in t_s.css("font::text").getall()]

        # grabs the outer table holding the courses
        body = response.css("table[border='2']")

        # course['offerings'] contains the course_offering_list
        course_offerings = []

        # loop through main course tables
        for i in range(len(body)):
            # dictionary for course info
            nested_dict = dict.fromkeys(self.nested_keys)
            nested_dict['term'] = terms[i]
            nested_dict['section'] = sections[i]
        
            # nested_dict['course_info'] contains the course_info (list)
            course_info = []

            course_type_list = body[i].css("td[width='10%']::text").getall()
            
            # parse the course times row
            times = body[i].css("td[width='35%']")
            times.pop(0)    # first row contains the headers of the table (Days, Start Time, Duration, Location)

            # loop through each row of the course table
            for (time, course_type) in zip(times, course_type_list):

                course_info_dict = dict.fromkeys(self.course_info_keys)

                # holds dictionary of days, start_time, duration, and location
                meet_info_list = []

                time_info_list = time.css("tr")

                # parse the 'Day', 'Start Time', 'Duration', 'Location' row
                for n in range(len(time_info_list)):
                    time_info = time_info_list[n]
                    day = time_info.css("td:nth-child(1)::text").get()
                    start_time = time_info.css("td:nth-child(2)::text").get()
                    duration = time_info.css("td:nth-child(3)::text").get()
                    location = time_info.css("td[width='45%']").get()

                    # Has to check if the text exist in the page, otherwise have to return empty string instead of 'None'                   
                    if day is None:
                        day = ''
                    if start_time is None:
                        start_time = ''
                    if duration is None:
                        duration = ''
                    if location is None:
                        location = ''
                    else:
                        location = location.replace('<td width="45%" valign="TOP">', '').replace('<br>', '').replace('</td>', '').replace('\xa0', '')
                        location = ' '.join(location.split())

                    time_info_dict = {
                        'day': day,
                        'start_time': start_time,
                        'duration': duration,
                        'location': location
                    }
                    meet_info_list.append(time_info_dict)
            
                # cat element is right after time_info element
                cat_element = time.xpath('following-sibling::td[@width="20%" and @valign="TOP"]')
                cat_list = time.xpath('string(following-sibling::td[@width="20%" and @valign="TOP"])').getall()
                cat_list = [string.replace('\xa0', '').strip() for string in cat_list]

                #Version 2 of cat parse, if a course is cross-listed and has two cat's this puts them into a list instead of a single element
                #cat_list = time.xpath('following-sibling::td[@width="20%" and @valign="TOP"][1]') # get first sibling only
                #cat_list = cat_list.css("td::text").getall()
                #cat_list = [string.replace('\xa0', '').strip() for string in cat_list]

                if cat_list.count('') > 0:
                    # When the Cat # column has nothing in it
                    cat_list = []

                # instructor element is right beside cat_element
                instructor_element = cat_element[0].xpath('following-sibling::td[@valign="TOP" and @width="15%"]')
                instructor_list = instructor_element.css('td ::text').getall()
                instructors = [string.replace('\xa0',' ') for string in instructor_list]

                if instructors[0] == ' ' or instructors[0] == '  ':
                    instructors = []

                # Notes/Additional Fees beside instructor element
                notes_element = time.xpath('following-sibling::td[@width="20%" and @valign="TOP"][2]')
                notes = notes_element.css("td").get()
                notes_list = notes.replace('<td valign="TOP" width="20%">', '').replace('<br>\xa0</td>', '').replace('\xa0', '').replace('</td>', '')
                notes_list = notes_list.replace('\r\n', '').split('<br>')

                if notes_list[0] == '\xa0</td>' or notes_list[0] == '':
                    # For courses where there isn't a note or extra information, it's appropriate to keep this empty
                    notes_list = []
                
                course_info_dict['type'] = course_type
                course_info_dict['meet_info'] = meet_info_list
                course_info_dict['cat'] = cat_list
                course_info_dict['instructor'] = instructors
                course_info_dict['notes'] = notes_list                
                course_info.append(course_info_dict)

            nested_dict['course_info'] = course_info
            course_offerings.append(nested_dict)
            
        course['offerings'] = course_offerings
        yield course

        '''
        Example of how the rest api's structure is going to look like
        course = {'course_name': name,
                  'description': desc,
                  'faculty': faculty,
                  'subject': subject,
                  'credit': credit,
                  TODO: academic_year and pre-requisites later
                  # 'academic_year' : year
                  # 'Pre-requisites': yes or no, if yes have a list of the courses of the pre-req # more of a TO-DO instead of an immediate need
                  'offerings': ['nested_dict', 'nested_dict', etc.]
                  }
        '''