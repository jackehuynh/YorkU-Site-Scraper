import scrapy
import csv

# grabs list of subjects from York's subject page
class SubjectScraper(scrapy.Spider):
    name = "subject"

    def start_requests(self):
        start_url = ["https://w2prod.sis.yorku.ca/Apps/WebObjects/cdm"]

        # obtain url to subjects page
        yield scrapy.Request(url=start_url[0], callback=self.set_subject_url)

    def set_subject_url(self, response):
        u = "https://w2prod.sis.yorku.ca"

        # response selector should output /App/WebObjects/cdm.woa/.. 
        # it's the first result of the ul tag with class=bodytext
        url = u + response.css("ul.bodytext").css("a::attr(href)").get()

        # use obtained 'url' to navigate to webpage to scrape subjects and corresponding faculties
        yield scrapy.Request(url=url, callback=self.get_subjects)

    def get_subjects(self, response):
        file_name = "csv/subjects.csv"

        '''
        TODO: 
        When Summer 2020 courses are released on the site, switch to selenium to handle
        scraping of course subjects due to use of AJAX on this page. In addition, can possibly
        stop scraping for 2019-2020 Fall/Winter courses at this point.
        '''

        # list of session names (ie. Fall/Winter 2019-2020 or Summer 2020)
        session_list = response.css('select[name="sessionPopUp"]').css("option::text").getall()
        
        # list of subjects and its corresponding faculties (ie. ACTG - Accounting - (SB, ED))
        subject_list = response.css('select[name="subjectPopUp"]').css("option::text").getall()

        with open(file_name, mode="w", encoding="utf-8", newline='') as file:
            writer = csv.writer(file)

            for subjects in subject_list:
                subject_dict = subjects.split("-")
                subject_code = subject_dict[0].strip()
                subject_name = subject_dict[1].strip()
                faculty = subject_dict[2].replace("(","").replace(")","").replace(" ","").split(",")
            
                for i in range(len(faculty)):
                    writer.writerow([subject_code, subject_name, faculty[i]])
