#!/usr/bin/env python
# coding:utf-8
'''创建Sqlite数据库'''
import time
import os
import os.path as osp
import sqlite3
import random
import re

def mkdir(dir_name):
    if not osp.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
    return


def create_database_table(database_path, database, table_name):
    mkdir(database_path)
    database_connect = sqlite3.connect(osp.join(database_path, database))
    print("open database:%s successfully" % database)
    database_cur = database_connect.cursor()
    try:
        database_cur.execute(
            "create table %s(num INTEGER PRIMARY KEY, target TEXT, name TEXT, timer TEXT);" % table_name)
    except:
        print("table:%s has existed" % table_name)
    return database_cur, database_connect


def insert_database_table(database_cur, database_connect, table_name, values):
    database_cur.execute("INSERT INTO %s VALUES(?,?,?,?);" % \
                         table_name, (None, values[0], values[1], values[2]))
    database_connect.commit()


if __name__ == "__main__":
    database_path = './database'
    database = 'demo.sqlite3'
    table_name = 'time_count'

    database_cur, database_connect = create_database_table(database_path, database, table_name)
    count = 0
    fruit = ['apple', 'banana', 'bayberry', 'cherry']
    while True:
        target = fruit[random.randint(0, 3)]
        id_name = str(count).zfill(10)[:10]
        now_time = time.strftime('%Y-%m-%d  %H:%M:%S', time.localtime())

        values = (target, id_name, now_time)
        insert_database_table(database_cur, database_connect, table_name, values)

        count += 1
        # time.sleep(0.5)