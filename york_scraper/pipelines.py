# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

'''
TODO: 
1) Extract the course type for easier insertion into DB
'''
import psycopg2
import json
import pytz
from datetime import datetime

# Current timestamp
dt = datetime.now().replace(microsecond = 0)
timezone = pytz.timezone('US/Eastern')
dt = timezone.localize(dt).strftime("%m/%d/%Y - %H:%M:%S")

class Database(object):
    

    def get_conn(self):
        self.connection = psycopg2.connect(
            host = self.host,
            user = self.user,
            password = self.password,
            dbname = self.dbname
        )
        self.connection.autocommit = True
        return self.connection

class YorkSubjectPipeline(object):
    def create_tables(self):
        query = """create table if not exists faculty (
            code varchar(8) not null,
            name text not null,
            primary key (code),
            unique (name)
        );"""
        self.cur.execute(query)

        query = """create table if not exists subject (
            subject varchar(8) not null,
            name text not null,
            primary key (subject),
            unique (name)
        );"""
        self.cur.execute(query)

    def open_spider(self, spider):
        self.connection = Database().get_conn()
        self.cur = self.connection.cursor()
        self.create_tables()

    def process_item(self, item, spider):
        query = """insert into faculty (code, name)
            values (%s, %s) on conflict (code) do update set
            name = excluded.name"""
        self.cur.execute(query, (item['faculty'], item['expanded_name']))
        
        query = """insert into subject (subject, name)
            values (%s, %s) on conflict (subject) do update set
            name = excluded.name"""
        self.cur.execute(query, (item['subject'], item['name']))
        return item

    def close_spider(self, spider):
        self.cur.close()
        self.connection.close()

class YorkCoursePipeline(object):
    def create_tables(self):
        query = """ ;"""
        self.cur.execute(query)
    
    def open_spider(self, spider):
        self.connection = Database().get_conn()
        self.cur = self.connection.cursor()
        self.create_tables()

    def process_item(self, item, spider):
        query = """"""
        self.cur.execute(query)
        return item
    
    def close_spider(self, spider):
        self.cur.close()
        self.connection.close()

class YorkCourseInfoPipeline(object):
    def create_tables(self):
        query = """CREATE TABLE if not exists courses (
            faculty varchar(8) not null REFERENCES faculty (code),
            subject varchar(8) not null REFERENCES subject (subject),
            course_number varchar(8) not null,
            name text not null,
            description text,
            credit text not null,
            loi text,
            offerings jsonb,
            url text not null,
            last_updated text
        );"""
        self.cur.execute(query)

    def open_spider(self, spider):
        self.connection = Database().get_conn()
        self.cur = self.connection.cursor()
        self.create_tables()

    def process_item(self, item, spider):
        query = """insert into courses (
            faculty, subject, course_number, name, description, credit, loi, offerings, url, last_updated
        ) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) on conflict do nothing"""
        self.cur.execute(query, (item['faculty'], item['subject'], item['course_number'], item['name'], 
        item['description'], item['credit'], item['loi'], json.dumps(item['offerings']), item['url'], dt))
        return item

    def close_spider(self,spider):
        self.cur.close()
        self.connection.close()