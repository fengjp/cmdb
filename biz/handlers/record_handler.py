#!/usr/bin/env python
# -*-coding:utf-8-*-


import json
import shortuuid
import base64
from websdk.jwt_token import gen_md5
from websdk.tools import check_password
from libs.base_handler import BaseHandler
from websdk.db_context import DBContext
from models.server import Record,  model_to_dict
from websdk.consts import const
from websdk.cache_context import cache_conn
from websdk.tools import convert
from websdk.web_logs import ins_log
import os
import pandas as pd


class RecordHandler(BaseHandler):
    def get(self, *args, **kwargs):
        data_list = []
        superuser_flag = 0
        if self.is_superuser:
            superuser_flag = 1
        key = self.get_argument('key', default=None, strip=True)
        value = self.get_argument('value', default=None, strip=True)
        page_size = self.get_argument('page', default=1, strip=True)
        limit = self.get_argument('limit', default=30, strip=True)
        limit_start = (int(page_size) - 1) * int(limit)
        user_list = []
        with DBContext('r') as session:
            conditions = []
            # if key == "name":
            #     conditions.append(Record.name.like('%{}%'.format(value)))
            # if key == "mode":
            #     conditions.append(Record.mode.like('%{}%'.format(value)))

            todata = session.query(Record).filter(*conditions).order_by(Record.create_time.desc()).offset(limit_start).limit(int(limit)).all()
            tocount = session.query(Record).filter(*conditions).count()

        for msg in todata:
            temp_dict = {}
            data_dict = model_to_dict(msg)
            temp_dict["id"] = data_dict["id"]
            temp_dict["recordname"] = data_dict["recordname"]
            temp_dict["recordlist"] = data_dict["recordlist"]
            temp_dict["zhname"] = data_dict["zhname"]
            temp_dict["username"] = data_dict["username"]
            temp_dict["tablename"] = data_dict["tablename"]
            temp_dict["number"] = data_dict["number"]
            data_list.append(temp_dict)

        if len(data_list) > 0:
            self.write(dict(code=0, msg='获取成功', count=tocount, data=data_list,flag = superuser_flag))
        else:
            self.write(dict(code=-1, msg='没有相关数据', count=0, data=[]))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        recordname = str(data.get('recordname', None))
        zhname = str(data.get('zhname', None))
        recordlist = str(data.get('recordlist', None))
        username = str(data.get('username', None))
        tablename = str(data.get('tablename', None))
        number = int(data.get('number', None))

        with DBContext('w', None, True) as session:
            session.add(Record(
                recordname=recordname,
                recordlist=recordlist,
                tablename=tablename,
                number=number,
                zhname=zhname,
                username=username,
            ))
            session.commit()

        self.write(dict(code=0, msg='成功', count=0, data=[]))

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        id = data.get('id', None)
        if not id:
            return self.write(dict(code=-1, msg='ID不能为空'))

        with DBContext('w', None, True) as session:
            session.query(Record).filter(Record.id == id).delete(synchronize_session=False)
        self.write(dict(code=0, msg='删除成功'))

    def put(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        id = data.get('id', None)
        recordname = str(data.get('recordname', None))
        zhname = str(data.get('zhname', None))
        recordlist = str(data.get('recordlist', None))
        username = str(data.get('username', None))
        tablename = str(data.get('tablename', None))
        number = int(data.get('number', None))

        try:
            with DBContext('w', None, True) as session:
                session.query(Record).filter(Record.id == id).update({
                    Record.recordname: recordname,
                    Record.recordlist: recordlist,
                    Record.zhname:zhname,
                    Record.username: username,
                    Record.tablename: tablename,
                    Record.number: number,
                })
                session.commit()
        except Exception as e:
            return self.write(dict(code=-2, msg='修改失败，请检查数据是否合法或者重复'))
        self.write(dict(code=0, msg='编辑成功'))


class Record_getId(BaseHandler):
    def get(self, *args, **kwargs):
        data_list = []
        with DBContext('r') as session:
            todata = session.query(Record).filter().order_by(Record.create_time.desc()).all()

        for msg in todata:
            temp_dict = {}
            data_dict = model_to_dict(msg)
            temp_dict["id"] = data_dict["id"]
            temp_dict["recordname"] = data_dict["recordname"]
            temp_dict["recordlist"] = data_dict["recordlist"]
            temp_dict["zhname"] = data_dict["zhname"]
            temp_dict["username"] = data_dict["username"]
            temp_dict["tablename"] = str(data_dict["tablename"])
            temp_dict["number"] = str(data_dict["number"])
            data_list.append(temp_dict)


        if len(data_list) > 0  > 0 :
            self.write(dict(code=0, msg='获取成功',  data=data_list,))
        else:
            self.write(dict(code=-1, msg='没有相关数据', count=0, data=[]))

class Record_getdata(BaseHandler):
    def get(self, *args, **kwargs):
        data_list = []
        username =  str(self.get_argument('username', default=None))#用戶名
        tablename = str(self.get_argument('tablename', default=None))#數據表名
        with DBContext('r') as session:
            conditions = []
            conditions.append(Record.username == username)
            conditions.append(Record.tablename == tablename)
            todata = session.query(Record).filter(*conditions).order_by(Record.number.desc()).all()
            # todata = session.query(Record).filter(*conditions).all()

        for msg in todata:
            temp_dict = {}
            data_dict = model_to_dict(msg)
            temp_dict["id"] = data_dict["id"]
            temp_dict["recordname"] = data_dict["recordname"]
            temp_dict["recordlist"] = data_dict["recordlist"]
            temp_dict["zhname"] = data_dict["zhname"]
            temp_dict["username"] = data_dict["username"]
            temp_dict["tablename"] = str(data_dict["tablename"])
            temp_dict["number"] = str(data_dict["number"])
            data_list.append(temp_dict)


        if len(data_list) > 0:
            self.write(dict(code=0, msg='获取成功',  data=data_list,))
        else:
            self.write(dict(code=-1, msg='没有相关数据', count=0, data=[]))

record_urls = [
    (r"/v1/record/recordlist/", RecordHandler),
    (r"/v1/record/record_getid/", Record_getId),
    (r"/v1/record/record_getdata/", Record_getdata),
]

if __name__ == "__main__":
    pass
