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

        # Sends request to the 'Timetable' link on the course's page
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        file_name = self.csv_location + "course_info.csv"

        # HTML element that contains section of course info (description, title, times)
        table_body = response.css("table[cellpadding='10']")

        # extract all text within <p> tags in the outer table body containing all the inner tables with the course info
        p_text = table_body.css('p::text').getall()
        course_description = p_text[-3]

        #course_info_body = table_body.css("table[width='100%']").get()

        # extracts html element (red bar) containing term and section
        t_s = table_body.css("td[width='50%']")
        terms = [string.strip() for string in t_s.css("b::text").getall()]
        sections = [string.strip() for string in t_s.css("font::text").getall()]

        # extracts the table below the term/section containing times, location, cat #, etc.
        info_tables = table_body.css("table[border='2']").css("td[valign='TOP']::text")

        # xpath version of above
        test = response.xpath('//table[@border="2"]//tr')

        # currently testing
        test = response.xpath('//table[@border="2"]').xpath('//td[@width="20%" and @valign="TOP"]')

        # grabs the entire table holding the courses
        body = response.css("table[border='2']")

        course_info_list = []

        # loop through main course tables
        for i in range(0, len(body)):
            
            # catalogue number
            cat = body[i].css("td[width='20%']").getall()[-2]
            cat_list = re.sub('<td width=\"20%\" valign=\"TOP\">', '', cat).strip('<br></td>').strip().split('<br>')
            cat_list = [string.replace('\xa0', '').strip() for string in cat_list] # parsed version, ready to be put into JSON object

            course_type_list = body[i].css("td[width='10%']::text").getall()

            # parse instructor list
            instructors = body[i].css("td[width='15%']").css("a::text").getall()
            parsed_instructors = [string.replace('\xa0',' ') for string in instructors]

            # parse times
            times = body[i].css("td[width='35%']")
            times.pop(0)    # first element contains the headers of the table (Type, Days, Start Time, etc.)

            # loop through each row of the course table
            for (time, c_type) in zip(times, course_type_list):
                #time_info = time.css("td::text").getall()
                time_info_list = time.css("tr").css

                # this is for when one row has multiple classes on different days/times/locations ie. M/W/F 1:30-2:30 @ LAS A/B/C
                for info in time_info_list:
                    time_info = info.css("td::text").getall()
                    time_info = [string.replace('\xa0','').strip() for string in info]
                    day = time_info[0]
                    start_time = time_info[1]
                    duration = time_info[2]
                    location = time_info[3]
                   
                course_type = c_type

                # cat element is right after time_info element
                cat_element = time.xpath('following-sibling::td[@width="20%" and @valign="TOP"]')
                cat_list = time.xpath('string(following-sibling::td[@width="20%" and @valign="TOP"])').getall()
                cat_list = [string.replace('\xa0', '').strip() for string in cat_list]

                if cat_list.count('') > 0:
                    # When the Cat # column has nothing in it
                    cat_list = ['N/A']

               
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
        TODO: add info_dict to scrapy's item feature
        '''

        '''
        inst_list = []
        # for loop
        nested_dict = {'term': term,
                       'section': section,
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
                  'academic_year' : year
                  'Pre-requisites': yes or no, if yes have a list of the courses of the pre-req # more of a TO-DO instead of an immediate need
                  'info': ['nested_dict', 'nested_dict', etc.]
                  }
        '''

        '''
        info_dict = {
                     'Type': lect,
                     'Time': nested_dict,
                     'cat': cat_list,
                     'instructor': nested_inst,
                     'notes': note 
                     }
        '''
        # returns array of days and the location corresponding to those days
        #day = body[i].css("td[width='15%']::text").getall()
        #loc = body[i].css("td[width='45%']::text").getall() # ['LAS C', 'LAS C']