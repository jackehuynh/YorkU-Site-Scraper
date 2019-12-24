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

    # Use these keys to construct the dictionary
    course_info_keys = ["type", "meet_info", "cat", "instructor", "notes"]
    #meet_info will be a nested dictionary containing days, start_time, duration, and location

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

        for url in urls:
            yield scrapy.Request(url=url, headers=self.headers, callback=self.set_course_url, dont_filter = True)

    def set_course_url(self, response):
        url = self.u + response.xpath('//a[contains(text(), "Fall")]/@href').get()

        # Sends request to the 'Timetable' link on the course's page
        yield scrapy.Request(url=url, headers=self.headers, callback=self.parse, dont_filter = True)

    def parse(self, response):
        file_name = self.csv_location + "course_info.csv"

        # HTML element that contains section of course info (description, title, times)
        table_body = response.css("table[cellpadding='10']")

        # extract all text within <p> tags in the outer table body containing all the inner tables with the course info
        p_text = table_body.css('p::text').getall()
        course_description = p_text[-3]

        # extracts html element (red bar) containing term and section
        t_s = table_body.css("td[width='50%']")
        terms = [string.strip() for string in t_s.css("b::text").getall()]
        sections = [string.strip() for string in t_s.css("font::text").getall()]

        # xpath version of above
        #test = response.xpath('//table[@border="2"]//tr')

        # currently testing
        #test = response.xpath('//table[@border="2"]').xpath('//td[@width="20%" and @valign="TOP"]')

        # grabs the entire table holding the courses
        body = response.css("table[border='2']")

        course_offering_list = []
       
        # loop through main course tables
        for i in range(0, len(body)):
            # dictionary for course info
            course_info_dict = dict.fromkeys(self.course_info_keys)

            # catalogue number
            #cat = body[i].css("td[width='20%']").getall()[-2]
            #cat_list = re.sub('<td width=\"20%\" valign=\"TOP\">', '', cat).strip('<br></td>').strip().split('<br>')
            #cat_list = [string.replace('\xa0', '').strip() for string in cat_list] # parsed version, ready to be put into JSON object

            course_type_list = body[i].css("td[width='10%']::text").getall()
            
            # parse the course times row
            times = body[i].css("td[width='35%']")
            times.pop(0)    # first row contains the headers of the table (Days, Start Time, Duration, Location)

            # holds dictionary of days, start_time, duration, and location
            meet_info_list = []

            # loop through each row of the course table
            for (time, course_type) in zip(times, course_type_list):
                #time_info = time.css("td::text").getall()
                time_info_list = time.css("tr")

                # this is for when one row has multiple classes on different days/times/locations ie. M/W/F 1:30-2:30 @ LAS A/B/C
                for n in range(0, len(time_info_list)):
                    #for info in time_info_list:
                    #dict_key = 'info_' + str(i)     # info_0, info_1, etc.

                    time_info = time_info_list[n].css("td::text").getall()
                    time_info = [string.replace('\xa0','').strip() for string in time_info]
                    day = time_info[0]
                    start_time = time_info[1]
                    duration = time_info[2]
                    location = time_info[-1].strip()
                    #location = time_info_list[n].css("td[width='45%']::text").get()
                    #location = location.replace('\xa0', '').strip()

                    # create new dictionary key for meet_info
                    time_info_dict = {
                        'day': day,
                        'start_time': start_time,
                        'duration': duration,
                        'location': location
                    }

                    meet_info_list.append(time_info_dict)
                
                course_info_dict['meet_info'] = meet_info_list
                course_info_dict['type'] = course_type

                # cat element is right after time_info element
                cat_element = time.xpath('following-sibling::td[@width="20%" and @valign="TOP"]')
                cat_list = time.xpath('string(following-sibling::td[@width="20%" and @valign="TOP"])').getall()
                cat_list = [string.replace('\xa0', '').strip() for string in cat_list]
                #cat_list = cat_list.strip('<br></td>').split('<br>')

                #Version 2 of cat parse, if a course is cross-listed and has two cat's this puts them into a list instead of a single element
                #cat_list = time.xpath('following-sibling::td[@width="20%" and @valign="TOP"][1]') # get first sibling only
                #cat_list = cat_list.css("td::text").getall()
                #cat_list = [string.replace('\xa0', '').strip() for string in cat_list]

                if cat_list.count('') > 0:
                    # When the Cat # column has nothing in it
                    cat_list = ['N/A']

                course_info_dict['cat'] = cat_list

                # instructor element is right beside cat_element
                instructor_element = cat_element[0].xpath('following-sibling::td[@valign="TOP" and @width="15%"]')
                instructor_list = instructor_element.css('td ::text').getall()
                instructors = [string.replace('\xa0',' ') for string in instructor_list]

                if instructors[0] == ' ':
                    instructors = []

                course_info_dict['instructor'] = instructors

                # Notes/Additional Fees beside instructor element
                notes_element = time.xpath('following-sibling::td[@width="20%" and @valign="TOP"][2]')
                notes = notes_element.css("td").get()
                notes_list = notes.replace('<td valign="TOP" width="20%">', '').replace('<br>\xa0</td>', '').replace('\xa0</td>', '').split('<br>')

                if notes_list[0] == '\xa0</td>' or notes_list[0] == '':
                    # For courses where there isn't a note or extra information, have to appropriately assign value to it
                    notes_list = []

                course_info_dict ['notes'] = notes_list

            # finally add this to course_offering_list
            course_offering_list.append(course_info_dict)
            #yield (course_info_dict)
        
        yield (course_offering_list[0])


        '''
        # example used is EECS 1019
        cat = body[i].css("td[width='20%']").getall()[-2] # need to clean up
        cat_id = re.sub('<td width=\"20%\" valign=\"TOP\">', '', cat).strip() # 'Y21A01 (LE EECS) <br>E10C01 (SC MATH) <br></td>
        cat_id = cat_id.strip('<br></td>').strip() # 'Y21A01 (LE EECS) <br>E10C01 (SC MATH)'
        cat_id = cat_id.split('<br>') # ['Y21A01 (LE EECS) ', 'E10C01 (SC MATH)']
        parsed_cat = [string.replace('\xa0','').strip() for string in cat_id] # ['Y21A01 (LE EECS)', 'E10C01 (SC MATH)']

        instructors = body[i].css("td[width='15%']").css("a::text").getall() # ['Andranik\xa0Mirzaian']
        times = body[i].css("td[width='35%']") # ['time_slots']
        time_slots = times[1].css("tr") # ['day1', 'day2']
        day_1 = time_slots[0].css("td::text").getall() # M 17:30 90 LAS\xa0C 
        day_2 = time_slots[1].css("td::text").getall() # R 17:30 90 LAS\xa0C

        course_type = body[i].css("td[width='10%']::text").get()

        # removing the '\xa0' string from the parsed text
        parsed_instructors = [string.replace('\xa0',' ') for string in instructors] # ['Andranik Mirazaian']

        # TODO: probably turn these list comprehensions into functions 
        parsed_day = [string.replace('\xa0', '').strip() for string in day_1] # ['M', '17:30', '90', 'LAS C']
        parsed_section = [string.replace('\xa0', '').strip() for string in sections] # ['Section A', 'Section B', 'Section C', etc]
        '''
        
        '''
        TODO: add info_dict to scrapy's item feature
        '''

        '''
        # for loop
        nested_dict = {'term': term,
                       'section': section,
                       'info' : [times_list]
                       'times': {
                            'course_type': course_type,
                            'day': day,
                            'start': start,
                            'duration': duration,
                            'location': location,
                            'cat': [cat_list],
                            'instructors': [inst_list],
                            'notes': notes
                       }
                     }

        inst_list.append('inst1')

        nested_dict['instructors'] = nested_inst
        '''

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

        '''
        info_dict = {
                     'Type': lect,
                     'Time': nested_dict,
                     'cat': cat_list,
                     'instructor': inst_list,
                     'notes': notes_list
                     }
        '''
        # returns array of days and the location corresponding to those days
        #day = body[i].css("td[width='15%']::text").getall()
        #loc = body[i].css("td[width='45%']::text").getall() # ['LAS C', 'LAS C']