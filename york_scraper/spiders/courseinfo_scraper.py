import scrapy
import os
import json
from w3lib.html import remove_tags
from scrapy.selector import Selector
from york_scraper.items import YorkCourseInfoItem, YorkCourseItem
from york_scraper.spiders.courses_scraper import CourseScraper
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from datetime import datetime

# Scrape all course information from York's Course Website using Selenium & Scrapy selectors
class CourseInfoScraper(scrapy.Spider):
    # Keys to construct the dictionaries
    name = "course_info_scrape"
    course_info_keys = ["type", "meet_info", "cat", "instructor", "notes"]
    nested_keys = ["term", "section", "course_info"]

    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        # suppress console(22) prompt when running headless
        chrome_options.add_argument("--log-level=3")
        self.driver = webdriver.Chrome(executable_path='chromedriver.exe', chrome_options=chrome_options)
        self.driver.implicitly_wait(1)

    def access_subject_page(self):
        url = 'https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm'
        self.driver.get(url)
        self.driver.find_element_by_link_text('Subject').click()

    def parse(self):
        start_time = datetime.now()
        self.access_subject_page()

        # Grab subject option elements
        subject_table = self.driver.find_element_by_xpath("//select[@name='subjectPopUp']")
        options = subject_table.find_elements_by_tag_name("option")

        # TODO: include option for summer session
        # session_table = self.driver.find_element_by_xpath("//select[@name='sessionPopUp]")

        # Select each subject
        for i in range(len(options)):
            subject_options = Select(self.driver.find_element_by_name('subjectPopUp'))
            subject_options.select_by_index(i)
            self.driver.find_element_by_name('3.10.7.5').click()
            self.set_course_url()
            # Go back to subject page
            self.access_subject_page()
            print('elapsed time: ' + str(datetime.now() - start_time))

        self.driver.close()
        print('Total execution time: ' + str(datetime.now() - start_time))

    def set_course_url(self):
        scrapy_selector = Selector(text = self.driver.page_source)

        w2_url = 'https://w2prod.sis.yorku.ca'

        # Grab all course schedule links
        urls = scrapy_selector.xpath('//a[contains(text(), "Course Schedule")]/@href').getall()

        # ex. SB/ACTG 2010 3.00
        course_codes = scrapy_selector.css('td[width="16%"]::text').getall()

        # ex. Introduction To Financial Accounting I
        course_names = scrapy_selector.css('td[width="24%"]::text').getall()
        cs = CourseScraper()

        # Sends request to the 'Timetable' link on the course's page
        for i in range(len(urls)):
            # have to call the selector again since it doesn't exist once call returns from extract_course_info function
            url_list = urls
            url = w2_url+url_list[i]
            course_dict = cs.parse_course_and_subject_code(course_codes[i], course_names[i])
            self.driver.get(url)
            self.extract_course_info(course_dict)

    def extract_course_info(self, course_dict):
        #course = YorkCourseInfoItem()
        course_keys = ['faculty', 'subject', 'course_number', 'credit', 'name', 'description', 'loi', 'offerings', 'url']
        course = dict.fromkeys(course_keys)
        course['faculty'] = course_dict['faculty']
        course['subject'] = course_dict['subject']
        course['course_number'] = course_dict['code']
        course['credit'] = course_dict['credit']
        course['name'] = course_dict['name']

        file_name = 'data/data.json'

        scrapy_selector = Selector(text = self.driver.page_source)

        # HTML element that contains section of description, title, and times
        table_body = scrapy_selector.css("table[cellpadding='10']")

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
        body = scrapy_selector.css("table[border='2']")

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
                cat_list = time.xpath('string(following-sibling::td[@width="20%" and @valign="TOP"])').get()
                cat_list = cat_list.replace('\xa0', '').replace('  ', '').strip()

                '''
                if cat_list.count('') > 0:
                    # When the Cat # column has nothing in it
                    cat_list = []
                '''
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
        print('Parsing: ' + course_dict['faculty'] + '/' + course_dict['subject'] + ' ' + course_dict['code'] + ' ' + 
        course_dict['credit'] + ' ' + course_dict['name'])

        if os.path.exists(file_name):
            filemode = 'a'
        else:
            filemode = 'w'

        # Write to json file
        with open(file_name, filemode, encoding='utf-8') as f:
            json.dump(course, f, ensure_ascii=False, indent = 4, separators = (',', ': '))

c = CourseInfoScraper()
c.parse()