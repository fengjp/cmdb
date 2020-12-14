#!/usr/bin/env python
# -*-coding:utf-8-*-
"""
status = '0'    正常
status = '10'   逻辑删除
status = '20'   禁用
"""

import json
import shortuuid
import base64
from websdk.jwt_token import gen_md5
from websdk.tools import check_password
from libs.base_handler import BaseHandler
from websdk.db_context import DBContext
# from models.admin import Users, UserRoles,model_to_dict as users_model_to_dict
from models.server import AssetSql, model_to_dict
from models.db import DB, model_to_dict    as   DB_model_to_dict
from websdk.consts import const
from websdk.cache_context import cache_conn
from websdk.web_logs import ins_log
from sqlalchemy import or_, and_
from sqlalchemy import func
import tornado.ioloop
import tornado.web
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os


class SqlListHandler(BaseHandler):
    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        name = data.get('name', None)  # 个案名称
        header = data.get('header', None)
        dbname_id = data.get('dbname_id', None)
        dbname = data.get('dbname', None)
        totype = data.get('totype', None)
        sqlstr = data.get('sqlstr', None)  # 优先级
        remarks = data.get('remarks', False)  # 执行人
        username = data.get('username', False)  # 执行人
        obj = data.get('obj', False)  # 项目
        department = str(data.get('department', False))[1:-1] # 部门
        storage = data.get('storage', False)  # 部门
        state = data.get('state', False)
        mode = data.get('mode', False)
        flag = data.get('flag', False)
        authorized = str(data.get('authorized', False))
        create_time = data.get('create_time', False)
        # ins_log.read_log('info', "800000000000000000000000000000000000")
        with DBContext('w', None, True) as session:
            session.add(AssetSql(
                name=name,
                header=header,
                dbname_id=dbname_id,
                dbname=dbname,
                totype=totype,
                sqlstr=sqlstr,
                remarks=remarks,
                username=username,
                obj=obj,
                authorized=authorized,
                department=department,
                storage=storage,
                mode=mode,
                state=state,
                flag=flag,
                create_time=create_time,))
            session.commit()
        self.write(dict(code=0, msg='成功', count=0, data=[]))

    def put(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        id = int(data.get('id', None))  # id号
        name = data.get('name', None)
        header = data.get('header', None)
        dbname_id = data.get('dbname_id', None)
        dbname = data.get('dbname', None)
        totype = data.get('totype', None)
        sqlstr = data.get('sqlstr', None)
        remarks = data.get('remarks', False)
        username= data.get('username', False)
        obj = data.get('obj', False)
        department = str(data.get('department', False))[1:-1]
        storage = data.get('storage', False)
        state = data.get('state', False)
        mode = data.get('mode', False)
        flag = data.get('flag', False)
        authorized = str(data.get('authorized', False))
        create_time = data.get('create_time', False)
        with DBContext('w', None, True) as session:
            session.query(AssetSql).filter(AssetSql.id == id).update({
                AssetSql.name: name,
                AssetSql.header: header,
                AssetSql.dbname_id: dbname_id,
                AssetSql.dbname: dbname,
                AssetSql.totype: totype,
                AssetSql.sqlstr: sqlstr,
                AssetSql.remarks: remarks,
                AssetSql.username: username,
                AssetSql.obj: obj,
                AssetSql.department: department,
                AssetSql.storage: storage,
                AssetSql.state: state,
                AssetSql.mode: mode,
                AssetSql.flag: flag,
                AssetSql.authorized: authorized,
                AssetSql.create_time: create_time,
            })
            session.commit()
        self.write(dict(code=0, msg='成功', count=0, data=[]))


class getSqlListHandler(BaseHandler):
    def get(self, *args, **kwargs):
        data_list = []
        superuser_flag  = 0
        tovalue = self.get_argument('value', strip=True)  # 要查询的关键字
        topage = int(self.get_argument('page', strip=1))  # 开始页
        tolimit = int(self.get_argument('limit', strip=10))  # 要查询条数
        limit_start = (topage - 1) * tolimit

        with DBContext('r') as session:
            params = {}
            if tovalue:
                params = eval(tovalue)
            conditions = []
            if self.is_superuser:
                superuser_flag = 1
            if params.get('name', ''):
                conditions.append(AssetSql.name.like('%{}%'.format(params['name'])))
            if params.get('remarks', ''):
                conditions.append(AssetSql.remarks.like('%{}%'.format(params['remarks'])))
            if params.get('totype', ''):
                conditions.append(AssetSql.totype.like('%{}%'.format(params['totype'])))

            todata = session.query(AssetSql).filter(*conditions).order_by(AssetSql.create_time.desc()).offset(limit_start).limit(int(tolimit)).all()
            tocount = session.query(AssetSql).filter(*conditions).count()

        for msg in todata:
            case_dict = {}
            data_dict = model_to_dict(msg)
            case_dict["id"] = data_dict["id"]
            case_dict["name"] = data_dict["name"]
            case_dict["header"] = data_dict["header"]
            case_dict["dbname_id"] = data_dict["dbname_id"]
            case_dict["dbname"] = data_dict["dbname"]
            case_dict["totype"] = data_dict["totype"]
            case_dict["sqlstr"] = data_dict["sqlstr"]
            case_dict["remarks"] = data_dict["remarks"]
            case_dict["username"] = data_dict["username"]
            case_dict["obj"] = data_dict["obj"]
            case_dict["department"] = data_dict["department"]
            case_dict["storage"] = data_dict["storage"]
            case_dict["mode"] = data_dict["mode"]
            case_dict["state"] = data_dict["state"]
            case_dict["flag"] = data_dict["flag"]
            case_dict["authorized"] = data_dict["authorized"]
            case_dict["create_time"] = str(data_dict["create_time"])
            data_list.append(case_dict)

        if len(data_list) > 0:
            self.write(dict(code=0, msg='获取成功', count=tocount, data=data_list,flag=superuser_flag))
        else:
            self.write(dict(code=-1, msg='没有相关数据', count=0, data=[],flag=superuser_flag))



def getlist(date_list, lime):
    sum_list = []
    sum_flag = 0
    for d in date_list:
        for k in lime:
            if d == str(k[1]):
                g = k
                sum_flag = 1
        if sum_flag == 1:
            sum_list.append(g[0])
        else:
            sum_list.append(0)
        sum_flag = 0
    # ins_log.read_log('info', sum_list)
    return sum_list


class sqlDelete(BaseHandler):
    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        toid = int(data.get('id', None))  # id号
        with DBContext('w', None, True) as session:
            session.query(AssetSql).filter(AssetSql.id == toid).delete(synchronize_session=False)
            session.commit()
        return self.write(dict(code=0, msg='删除成功'))


class getSqlIdList(BaseHandler):
    def get(self, *args, **kwargs):
        data_list = []
        with DBContext('r') as session:
            conditions = []
            conditions.append(AssetSql.totype == "sql")
            conditions.append(AssetSql.mode == "定时")
            conditions.append(AssetSql.state == "运行")
            todata = session.query(AssetSql).filter(*conditions).order_by(AssetSql.create_time.desc()).all()
            tocount = session.query(AssetSql).filter(*conditions).count()

        for msg in todata:
            case_dict = {}
            data_dict = model_to_dict(msg)
            case_dict["id"] = data_dict["id"]
            case_dict["name"] = data_dict["name"]
            case_dict["header"] = data_dict["header"]
            case_dict["dbname_id"] = data_dict["dbname_id"]
            case_dict["dbname"] = data_dict["dbname"]
            case_dict["totype"] = data_dict["totype"]
            case_dict["sqlstr"] = data_dict["sqlstr"]
            case_dict["remarks"] = data_dict["remarks"]
            case_dict["username"] = data_dict["username"]
            case_dict["obj"] = data_dict["obj"]
            case_dict["department"] = data_dict["department"]
            case_dict["storage"] = data_dict["storage"]
            case_dict["authorized"] = data_dict["authorized"]
            case_dict["create_time"] = str(data_dict["create_time"])
            data_list.append({"id":case_dict["id"],"name":case_dict["name"]})

        if len(data_list) > 0:
            self.write(dict(code=0, msg='获取成功', count=tocount, data=data_list))
        else:
            self.write(dict(code=-1, msg='没有相关数据', count=0, data=[]))

class getSqlIdDate(BaseHandler):
    def get(self, *args, **kwargs):
        data_list = []
        value = int(self.get_argument('value', default=None, strip=True))
        with DBContext('r') as session:
            todata = session.query(AssetSql).filter(AssetSql.id == value).all()
            # tocount = session.query(AssetSql).filter().count()

        for msg in todata:
            case_dict = {}
            data_dict = model_to_dict(msg)
            case_dict["id"] = data_dict["id"]
            case_dict["name"] = data_dict["name"]
            case_dict["header"] = data_dict["header"]
            case_dict["dbname_id"] = data_dict["dbname_id"]
            case_dict["dbname"] = data_dict["dbname"]
            case_dict["totype"] = data_dict["totype"]
            case_dict["sqlstr"] = data_dict["sqlstr"]
            case_dict["remarks"] = data_dict["remarks"]
            case_dict["username"] = data_dict["username"]
            case_dict["obj"] = data_dict["obj"]
            case_dict["department"] = data_dict["department"]
            case_dict["storage"] = data_dict["storage"]
            case_dict["mode"] = data_dict["mode"]
            case_dict["state"] = data_dict["state"]
            case_dict["create_time"] = str(data_dict["create_time"])
            data_list.append(case_dict)

        if len(data_list) > 0:
            self.write(dict(code=0, msg='获取成功',  data=data_list))
        else:
            self.write(dict(code=-1, msg='没有相关数据', count=0, data=[]))

class getdepartmentlist(BaseHandler):
    def get(self, *args, **kwargs):
        objlist = []
        department_list = []
        de_list = []
        obj_list = []
        num = 0
        with DBContext('r') as session:
            todata = session.query(AssetSql).filter().all()

        for msg in todata:
            case_dict = {}
            data_dict = model_to_dict(msg)
            # case_dict["id"] = data_dict["id"]
            # case_dict["name"] = data_dict["name"]
            # case_dict["header"] = data_dict["header"]
            # case_dict["dbname_id"] = data_dict["dbname_id"]
            # case_dict["dbname"] = data_dict["dbname"]
            # case_dict["totype"] = data_dict["totype"]
            # case_dict["sqlstr"] = data_dict["sqlstr"]
            # case_dict["remarks"] = data_dict["remarks"]
            # case_dict["username"] = data_dict["username"]
            case_dict["obj"] = data_dict["obj"]
            case_dict["department"] = data_dict["department"]
            # case_dict["create_time"] = str(data_dict["create_time"])
            if case_dict["obj"] not in obj_list:
                obj_list.append(case_dict["obj"])
                objlist.append({"k":num,"v":case_dict["obj"]})
            if case_dict["department"] not in de_list:
                de_list.append(case_dict["department"])
                department_list.append({"k":num,"v":case_dict["department"]})
            num  =  num + 1

        if len(department_list) > 0:
            self.write(dict(code=0, msg='获取成功',  data=department_list,objlist=objlist))
        else:
            self.write(dict(code=-1, msg='没有相关数据', count=0, data=[],objlist=[]))


class getstoragelist(BaseHandler):
    def get(self, *args, **kwargs):
        data_list = []
        department = self.get_argument('department', strip=True)
        obj = self.get_argument('obj', strip=True)
        with DBContext('r') as session:
            conditions = []
            # conditions.append(AssetSql.department == department)
            department = "'" + department +  "'"
            conditions.append(AssetSql.department.like('%{}%'.format(department)))
            conditions.append(AssetSql.obj ==  obj)
            todata = session.query(AssetSql).filter(*conditions).all()

        for msg in todata:
            case_dict = {}
            data_dict = model_to_dict(msg)
            case_dict["id"] = data_dict["id"]
            case_dict["obj"] = data_dict["obj"]
            case_dict["name"] = data_dict["name"]
            case_dict["department"] = data_dict["department"]
            case_dict["storage"] = data_dict["storage"]
            data_list.append({"k":case_dict["id"],"v":case_dict["name"],"n":case_dict["storage"]})

        if len(data_list) > 0:
            self.write(dict(code=0, msg='获取成功',  data=data_list))
        else:
            self.write(dict(code=-1, msg='没有相关数据', count=0, data=[]))

class getimplementlist(BaseHandler):
    def get(self, *args, **kwargs):
        data_list = []
        data_list2 = []
        date = self.get_argument('date', strip=True)
        storage = self.get_argument('storage', strip=True) #存储过程id
        flag = self.get_argument('flag', strip=True)  # 1执行sql，2执行存储过程
        with DBContext('r') as session:
            conditions = []
            conditions.append(AssetSql.id == int(storage))
            todata = session.query(AssetSql).filter(*conditions).all()

        for msg in todata:
            case_dict = {}
            data_dict = model_to_dict(msg)
            case_dict["id"] = data_dict["id"]
            case_dict["name"] = data_dict["name"]
            case_dict["header"] = data_dict["header"]
            case_dict["dbname_id"] = data_dict["dbname_id"]
            case_dict["dbname"] = data_dict["dbname"]
            case_dict["sqlstr"] = data_dict["sqlstr"]
            case_dict["totype"] = data_dict["totype"]
            case_dict["obj"] = data_dict["obj"]
            case_dict["department"] = data_dict["department"]
            case_dict["storage"] = data_dict["storage"]
            case_dict["create_time"] = str(data_dict["create_time"])
            data_list.append(case_dict)

        if len(data_list) > 0:

            with DBContext('r') as session:
                conditions = []
                conditions.append(DB.id == int(data_list[0]["dbname_id"]))
                DB_data = session.query(DB).filter(*conditions).all()

            for msg in DB_data:
                case_dict = {}
                data_dict = DB_model_to_dict(msg)
                case_dict["id"] = data_dict["id"]
                case_dict["db_instance"] = data_dict["db_instance"] #库名
                case_dict["db_host"] = data_dict["db_host"]
                case_dict["db_port"] = data_dict["db_port"]
                case_dict["db_user"] = data_dict["db_user"]
                case_dict["db_pwd"] = data_dict["db_pwd"]
                case_dict["db_type"] = data_dict["db_type"]  #oracle/mysql

                data_list2.append(case_dict)
            # ins_log.read_log('info', "800000000000000000000000000000000000")
            # ins_log.read_log('info', data_list2)
            # ins_log.read_log('info', "800000000000000000000000000000000000")
            #连接oracle
            #执行存储过程
            #返回数据
            title_list = data_list[0]["header"].split('|')
            columns_list = []
            num = 0
            key_list = []
            for  h in title_list:
                tempstr = 'number'+str(num)
                columns_list.append({ "title": h, "key": tempstr, "editable": "true" })
                key_list.append(tempstr)
                num +=1

            data_list3 =[{"number0":1,"number1":5,"number2":8,"number3":10}]
            ins_log.read_log('info', "800000000000000000000000000000000000")
            ins_log.read_log('info', title_list)
            ins_log.read_log('info', columns_list)
            ins_log.read_log('info', key_list)
            ins_log.read_log('info', flag)
            ins_log.read_log('info', "800000000000000000000000000000000000")
            self.write(dict(code=0, msg='获取成功',  data=data_list3,columnslist = columns_list,titlelist=title_list,keylist= key_list))
        else:
            self.write(dict(code=-1, msg='没有相关存储过程数据',data=[],columns_listb=[],titlelist=[],keylist=[]))


class getobjlist(BaseHandler):
    def get(self, *args, **kwargs):
        data_list = []
        data_list2 = []
        temp_list = []
        temp_list2 = []
        department = self.get_argument('department', strip=True)
        with DBContext('r') as session:
            conditions = []
            department = "'" + department +  "'"
            conditions.append(AssetSql.department.like('%{}%'.format(department)))
            todata = session.query(AssetSql).filter(*conditions).all()

        for msg in todata:
            case_dict = {}
            data_dict = model_to_dict(msg)
            case_dict["id"] = data_dict["id"]
            case_dict["obj"] = data_dict["obj"]
            case_dict["name"] = data_dict["name"]
            case_dict["department"] = data_dict["department"]
            case_dict["storage"] = data_dict["storage"]
            case_dict["flag"] = data_dict["flag"]
            case_dict["authorized"] = data_dict["authorized"]
            if  case_dict["obj"] not  in  temp_list:
                temp_list.append(case_dict["obj"])
                data_list.append({"v":case_dict["obj"],"t":case_dict["flag"]})
            data_list2.append(case_dict)

        for  i in temp_list:
            temp_list2.append({"name":i,"date":[]})
        for  j in    temp_list2:
             for   d in  data_list2:
                if    str(j["name"])   == str(d["obj"]):
                    j["date"].append({"k":d["id"],"v":d["name"],"t":d["flag"],"s":d["storage"]})

        if len(data_list) > 0:
            self.write(dict(code=0, msg='获取成功',  data=data_list,storagelist=temp_list2))
        else:
            self.write(dict(code=-1, msg='没有相关数据', count=0, data=[]))



assetSql_urls = [
    (r"/v1/sql/add/", SqlListHandler),
    (r"/v1/sql/list/", getSqlListHandler),
    (r"/v1/sql/Idlist/", getSqlIdList),
    (r"/v1/sql/IdDate/", getSqlIdDate),
    (r"/v1/sql/delete/", sqlDelete),
    (r"/v1/sql/departmentlist/", getdepartmentlist),
    (r"/v1/sql/storagelist/", getstoragelist),
    (r"/v1/sql/objlist/", getobjlist),
    (r"/v1/sql/implement/", getimplementlist),
]

if __name__ == "__main__":
    pass
