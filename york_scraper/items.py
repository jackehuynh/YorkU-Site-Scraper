# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class YorkSubjectItem(scrapy.Item):
    faculty = scrapy.Field()
    subject = scrapy.Field()
    name = scrapy.Field()
    expanded_name = scrapy.Field() # Full name of abbreviated faculty

# Just has the basic info of a course (name, faculty, subject, etc.)
class YorkCourseItem(scrapy.Item):
    faculty = scrapy.Field()
    subject = scrapy.Field()
    code = scrapy.Field()
    credit = scrapy.Field()
    name = scrapy.Field()
    url = scrapy.Field()

class YorkCourseInfoItem(scrapy.Item):
    # TODO: Add field for prerequisite
    faculty = scrapy.Field()
    subject = scrapy.Field()
    course_number = scrapy.Field()
    name = scrapy.Field()
    description = scrapy.Field()
    credit = scrapy.Field()
    offerings = scrapy.Field()
    url = scrapy.Field()
    loi = scrapy.Field() # Language of instruction