#!/usr/bin/env python
# -*-coding:utf-8-*-


import json
import shortuuid
import base64
from websdk.jwt_token import gen_md5
from websdk.tools import check_password
from libs.base_handler import BaseHandler
from websdk.db_context import DBContext
from models.server import Storage,  model_to_dict
from websdk.consts import const
from websdk.cache_context import cache_conn
from websdk.tools import convert
from websdk.web_logs import ins_log
import os
import pandas as pd


class StorageHandler(BaseHandler):
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
            if key == "name":
                conditions.append(Storage.name.like('%{}%'.format(value)))
            if key == "mode":
                conditions.append(Storage.mode.like('%{}%'.format(value)))

            todata = session.query(Storage).filter(*conditions).order_by(Storage.create_time.desc()).offset(limit_start).limit(int(limit)).all()
            tocount = session.query(Storage).filter(*conditions).count()

        for msg in todata:
            temp_dict = {}
            data_dict = model_to_dict(msg)
            temp_dict["id"] = data_dict["id"]
            temp_dict["name"] = data_dict["name"]
            temp_dict["mode"] = data_dict["mode"]
            temp_dict["dictvalue"] = data_dict["dictvalue"]
            temp_dict["authorized"] = data_dict["authorized"]
            temp_dict["remarks"] = data_dict["remarks"]
            temp_dict["username"] = str(data_dict["username"])
            temp_dict["consume"] = str(data_dict["consume"])
            temp_dict["create_time"] = str(data_dict["create_time"])
            data_list.append(temp_dict)

        if len(data_list) > 0:
            self.write(dict(code=0, msg='获取成功', count=tocount, data=data_list,flag = superuser_flag))
        else:
            self.write(dict(code=-1, msg='没有相关数据', count=0, data=[]))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        name = data.get('name', None)  #存储过程名
        mode = data.get('mode', None)   #执行方式
        dictvalue = str(data.get('dictvalue', None))  #参数列表
        authorized = str(data.get('authorized', None))  #授权用户列表
        remarks = str(data.get('remarks', None))   #详细描述
        username = str(self.get_current_nickname()) #创建人


        with DBContext('w', None, True) as session:
            session.add(Storage(
                name=name,
                mode=mode,
                dictvalue=dictvalue,
                authorized=authorized,
                remarks=remarks,
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
            session.query(Storage).filter(Storage.id == id).delete(synchronize_session=False)
        self.write(dict(code=0, msg='删除成功'))

    def put(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        id = data.get('id', None)
        name = data.get('name', None)  # 存储过程名
        mode = data.get('mode', None)  # 执行方式
        dictvalue = str(data.get('dictvalue', None))  # 参数列表
        authorized = str(data.get('authorized', None))  # 授权用户列表
        remarks = str(data.get('remarks', None))  # 详细描述
        # username = str(self.get_current_nickname())  # 创建人

        try:
            with DBContext('w', None, True) as session:
                session.query(Storage).filter(Storage.id == id).update({
                    Storage.id: id,
                    Storage.name: name,
                    Storage.mode: mode,
                    Storage.dictvalue: dictvalue,
                    Storage.authorized: authorized,
                    Storage.remarks: remarks,
                })
                session.commit()
        except Exception as e:
            return self.write(dict(code=-2, msg='修改失败，请检查数据是否合法或者重复'))
        self.write(dict(code=0, msg='编辑成功'))


class Storage_getId(BaseHandler):
    def get(self, *args, **kwargs):
        data_list = []
        data_list2 = []
        with DBContext('r') as session:
            todata = session.query(Storage).filter().order_by(Storage.create_time.desc()).all()

        for msg in todata:
            temp_dict = {}
            data_dict = model_to_dict(msg)
            temp_dict["id"] = data_dict["id"]
            temp_dict["name"] = data_dict["name"]
            temp_dict["mode"] = data_dict["mode"]
            temp_dict["consume"] = data_dict["consume"]
            temp_dict["dictvalue"] = str(data_dict["dictvalue"])
            # temp_dict["authorized"] = str(data_dict["authorized"])
            ins_log.read_log('info', "800000000000000000000000000000000000")
            ins_log.read_log('info', data_dict["mode"])
            ins_log.read_log('info', "800000000000000000000000000000000000")
            if data_dict["mode"] == "定时":
               data_list.append(temp_dict)
            if data_dict["mode"] == "触发":
               data_list2.append(temp_dict)

        if len(data_list) > 0  or len(data_list2) > 0 :
            self.write(dict(code=0, msg='获取成功',  data=data_list,data2=data_list2))
        else:
            self.write(dict(code=-1, msg='没有相关数据', count=0, data=[]))

class Storage_Iddata(BaseHandler):
    def get(self, *args, **kwargs):
        data_list = []
        data_list2 = []
        name = self.get_argument('name', default=None, strip=True)
        with DBContext('r') as session:
            todata = session.query(Storage).filter(Storage.name == name).all()

        for msg in todata:
            temp_dict = {}
            data_dict = model_to_dict(msg)
            temp_dict["id"] = data_dict["id"]
            temp_dict["name"] = data_dict["name"]
            temp_dict["mode"] = data_dict["mode"]
            temp_dict["consume"] = data_dict["consume"]
            temp_dict["dictvalue"] = str(data_dict["dictvalue"])
            temp_dict["authorized"] = str(data_dict["authorized"])
            data_list.append(temp_dict)

        if len(data_list) > 0  or len(data_list2) > 0 :
            self.write(dict(code=0, msg='获取成功!',  data=data_list))
        else:
            self.write(dict(code=-1, msg='没有相关数据', count=0, data=[]))



storage_urls = [
    (r"/v1/storage/storagelist/", StorageHandler),
    (r"/v1/storage/storage_getid/", Storage_getId),
    (r"/v1/storage/storage_iddata/", Storage_Iddata),
]

if __name__ == "__main__":
    pass
