# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class YorkSubjectItem(scrapy.Item):
    code = scrapy.Field()
    name = scrapy.Field()
    faculty = scrapy.Field()

# Just has the basic info of a course (name, faculty, subject, etc.)
class YorkCourseItem(scrapy.Item):
    faculty = scrapy.Field()
    subject = scrapy.Field()
    code = scrapy.Field()
    credit = scrapy.Field()
    name = scrapy.Field()
    url = scrapy.Field()

class YorkCourseInfoItem(scrapy.Item):
    '''
    TODO: Add fields for prerequisites, academic year, and LOI (Language of Instructions)
    '''
    name = scrapy.Field()
    description = scrapy.Field()
    faculty = scrapy.Field()
    subject = scrapy.Field()
    credit = scrapy.Field()
    offerings = scrapy.Field()