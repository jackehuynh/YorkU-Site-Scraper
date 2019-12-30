import scrapy
import csv
from w3lib.html import remove_tags
from york_scraper.items import YorkCourseInfoItem, YorkCourseItem

# Scrape all course information from York's Course Website
class CourseInfoScraper(scrapy.Spider):
    name = "course_info"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:48.0) Gecko/20100101 Firefox/48.0'
    }
    custom_settings = {
        'FEED_EXPORTER': 'JsonLinesItemExporter',
        'FEED_FORMAT': 'jsonlines',
        'FEED_URI': 'data/info.json',
        'ITEM_PIPELINES': {
            'york_scraper.pipelines.CheckDuplicatePipeline': 200,
            'york_scraper.pipelines.YorkCourseInfoPipeline': 300
        }
    }
    u = "https://w2prod.sis.yorku.ca"

    # Keys to construct the dictionaries
    course_info_keys = ["type", "meet_info", "cat", "instructor", "notes"]
    nested_keys = ["term", "section", "course_info"]

    def start_requests(self):
        file_name = "csv/courses.csv"
        course_list = []

        '''
        TODO: 
        1) add try-throw block to throw an error if file does not exist
        2) make it customizable for other terms not just FW
        3) log errors to a custom file so if a course fails to be scraped, it can start up
           a separate (essentially an exact version of this one but for single link(s) only) crawler
           to try to rescrape it. Do this for coursescraper.py too.
        '''
        
        with open(file_name, mode="r") as file:
            reader = csv.DictReader(file, delimiter=',')

            # Populate course list to pass it's data to parse method
            for data in reader:
                course_item = YorkCourseItem()
                course_item['faculty'] = data['faculty']
                course_item['subject'] = data['subject']
                course_item['code'] = data['code']
                course_item['credit'] = data['credit']
                course_item['name'] = data['name']
                course_item['url'] = data['url']
                course_list.append(course_item)
        
        for course in course_list:
            yield scrapy.Request(
                url = course['url'], 
                headers = self.headers, 
                callback = self.set_course_url, 
                dont_filter = True,
                meta = {'course_dict': course}
            )
        #t = 'https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm.woa/wa/crsq?fa=GS&sj=HUMA&cn=6000B&cr=3.00&ay=2019&ss=FW'
        #yield scrapy.Request(url=t, headers=self.headers, callback=self.set_course_url, dont_filter = True)

    def set_course_url(self, response):
        # TODO: implement xpath for summer courses once it's available

        # Some course websites have duplicates for some reason IE: FA/FILM 2230 and GL/BIOL 2300
        # As a result the first link directs to a cancelled class whereas the subsequent links are the reinstated class.
        url = self.u + response.xpath('//a[contains(text(), "Fall")]/@href').getall()[-1]

        # Sends request to the 'Timetable' link on the course's page
        yield scrapy.Request(
            url = url, 
            headers = self.headers, 
            callback = self.parse, 
            dont_filter = True,
            meta = {'course_dict': response.meta['course_dict']}
        )

    def parse(self, response):
        course = YorkCourseInfoItem()
        
        course_dict = response.meta['course_dict']
        course['faculty'] = course_dict['faculty']
        course['subject'] = course_dict['subject']
        course['course_number'] = course_dict['code']
        course['credit'] = course_dict['credit']
        course['name'] = course_dict['name']

        # HTML element that contains section of description, title, and times
        table_body = response.css("table[cellpadding='10']")

        # extract all text within <p> tags in the outer table body containing all the inner tables with the course info
        course_description = table_body.xpath('//b[contains(text(), "Course Description")]/../following-sibling::p[1]').get()
        course['description'] = remove_tags(course_description).replace('\r','').replace('\n','').replace('\t','')

        # Language of Instructions (language that's used in teaching the course)
        course['loi'] = remove_tags(table_body.xpath('//b[contains(text(), "Language of Instruction:")]/../following-sibling::p[1]').get())

        # extracts html element (red bar) containing term and section
        t_s = table_body.css("td[width='50%']")
        terms = [string.strip('Term').strip() for string in t_s.css("b::text").getall()]
        sections = [string.strip() for string in t_s.css("font::text").getall()]

        # grabs the outer table element holding ALL the course offerings
        body = response.css("table[border='2']")

        # List of all the different sections being offered for this particular course
        course_offerings = []

        # loop through main course tables
        for i in range(len(body)):
            # dictionary for course info
            nested_dict = dict.fromkeys(self.nested_keys)
            nested_dict['term'] = terms[i]
            nested_dict['section'] = sections[i]
        
            # Holds course_info_dict which consist of Type, Days, Start Time, Duration, Cat #, instructor, notes
            course_info = []

            course_type_list = body[i].css("td[width='10%']::text").getall()
            
            # parse the course times row
            times = body[i].css("td[width='35%']")

            # first row contains the headers of the table (Days, Start Time, Duration, Location)
            times.pop(0)

            # loop through each row of the course table
            for (time, course_type) in zip(times, course_type_list):

                course_info_dict = dict.fromkeys(self.course_info_keys)

                # holds dictionary of days, start_time, duration, and location
                meet_info_list = []

                # parse the 'Day', 'Start Time', 'Duration', 'Location' row
                for time_info in time.css("tr"):
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
                        location = remove_tags(location)
                        #location = location.replace('<td width="45%" valign="TOP">', '').replace('<br>', '').replace('</td>', '').replace('\xa0', '')
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
                cat_list = [string.replace('\xa0', '').replace('  ', '').strip() for string in cat_list]

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
                notes_list = notes_list.replace('\r', '').replace('\n', '').split('<br>')
                #notes_list = remove_tags(notes, keep=('br',)).replace('<br>\xa0', '').split('<br>')
                
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
        course['url'] = course_dict['url']
        yield course