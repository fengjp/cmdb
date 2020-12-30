#!/usr/bin/env python
# -*-coding:utf-8-*-
"""
status = '0'    正常
status = '10'   逻辑删除
status = '20'   禁用
"""
import os
import sys

_op = os.path.dirname
cwdir = _op(os.path.abspath(__file__))
project_path = _op(_op(os.path.abspath(__file__)))
app_path = _op(project_path)
sys.path.insert(0, project_path)

import json
from libs.base_handler import BaseHandler
from websdk.db_context import DBContext
from models.server import AssetSql, model_to_dict
from models.server import Storage
from models.db import DB, model_to_dict    as   DB_model_to_dict
from websdk.web_logs import ins_log
from libs.mysql_conn import MysqlBase
from libs.aes_coder import encrypt, decrypt
import cx_Oracle
import time
import copy
import traceback


def getfieldlist(dbname_id, fieldname):
    data_list = []
    data_list3 = []
    with DBContext('r') as session:
        conditions = []
        conditions.append(DB.id == int(dbname_id))
        DB_data = session.query(DB).filter(*conditions).all()

    for msg in DB_data:
        case_dict = {}
        data_dict = DB_model_to_dict(msg)
        case_dict["id"] = data_dict["id"]
        case_dict["db_instance"] = data_dict["db_instance"]  # 库名
        case_dict["db_host"] = data_dict["db_host"]
        case_dict["db_port"] = data_dict["db_port"]
        case_dict["db_user"] = data_dict["db_user"]
        case_dict["db_pwd"] = data_dict["db_pwd"]
        case_dict["db_type"] = data_dict["db_type"]  # oracle/mysql

        data_list.append(case_dict)
    # sql_temp_str = "select  *  from  all_col_comments  where  table_name =upper('xxx')"
    # column_name字段名  comments字段中文备注
    sql_temp_str = "select  column_name, comments  from  all_col_comments   where  table_name =upper('xxx') and owner=upper('nnn')"
    sql_temp_str = sql_temp_str.replace("xxx", fieldname)
    sql_temp_str = sql_temp_str.replace("nnn", data_list[0]["db_user"])
    ins_log.read_log('info', sql_temp_str)
    CUSTOM_DB_INFO = dict(
        host=data_list[0]["db_host"],
        port=data_list[0]["db_port"],
        user=data_list[0]["db_user"],
        passwd=decrypt(data_list[0]["db_pwd"]),
        db=data_list[0]["db_instance"]  # 库名
    )
    try:
        if data_list[0]["db_type"] == "mysql":
            mysql_conn = MysqlBase(**CUSTOM_DB_INFO)
            db_data = mysql_conn.query(sql_temp_str)  # 测试用不了
        if data_list[0]["db_type"] == "oracle":
            temp_str = data_list[0]["db_host"] + '/' + data_list[0]["db_instance"]
            oracle_conn = cx_Oracle.connect(data_list[0]["db_user"], decrypt(data_list[0]["db_pwd"]), temp_str)
            cur = oracle_conn.cursor()
            data_temp = cur.execute(sql_temp_str)
            for i in data_temp:
                temp_dict = {}
                temp_dict["name"] = str(i[0])
                if str(i[1]) == "None":
                    temp_dict["zh_name"] = str(i[0])
                else:
                    temp_dict["zh_name"] = str(i[1])
                data_list3.append(temp_dict)
            cur.close()
            oracle_conn.close()
    except:
        traceback.print_exc()

    return data_list3


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
        department = str(data.get('department', False))[1:-1]  # 部门
        storage = data.get('storage', False)  # 部门
        storage2 = data.get('storage2', False)  # 部门
        state = data.get('state', False)
        mode = data.get('mode', False)
        flag = data.get('flag', False)
        authorized = str(data.get('authorized', '[]'))
        fieldname = str(data.get('fieldname', False)).strip()  # 表名
        fieldlist = ""
        dictvalue = str(data.get('dictvalue', False))
        dictvalue2 = str(data.get('dictvalue2', False))
        if authorized == "None":
            authorized = "[]"
        create_time = data.get('create_time', False)
        # 获取数据表字段名和对应的中文名称（測試版）
        # if str(totype) == "存储过程":
        #    fieldlist = str(getfieldlist(dbname_id,fieldname))
        fieldlist = str([{"name": "bianhao", "zh_name": "地區编号"}, {"name": "number", "zh_name": "车牌号"},
                         {"name": "username", "zh_name": "姓名"}, {"name": "sex", "zh_name": "性别"},
                         {"name": "iphone", "zh_name": "手机号"}, {"name": "chepinpai", "zh_name": "车品牌"},
                         {"name": "type", "zh_name": "车类型"}, {"name": "zhuangzailiang", "zh_name": "车装载量"}])
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
                department=department,
                storage=storage,
                storage2=storage2,
                mode=mode,
                state=state,
                flag=flag,
                dictvalue=dictvalue,
                dictvalue2=dictvalue2,
                fieldname=fieldname,
                fieldlist=str(fieldlist),
                authorized=authorized,
                create_time=create_time, ))
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
        username = data.get('username', False)
        obj = data.get('obj', False)
        department = str(data.get('department', False))[1:-1]
        storage = data.get('storage', False)
        storage2 = data.get('storage2', False)
        state = data.get('state', '')
        mode = data.get('mode', False)
        flag = data.get('flag', False)
        authorized = str(data.get('authorized', '[]'))
        fieldname = str(data.get('fieldname', False)).strip()
        fieldlist = ""
        dictvalue = str(data.get('dictvalue', False))
        dictvalue2 = str(data.get('dictvalue2', False))
        if authorized == "None":
            authorized = "[]"
        create_time = data.get('create_time', False)
        # 获取数据表字段名和对应的中文名称
        # if str(totype) == "存储过程":
        #    fieldlist = str(getfieldlist(dbname_id,fieldname))
        fieldlist = str([{"name": "bianhao", "zh_name": "地區编号"}, {"name": "number", "zh_name": "车牌号"},
                         {"name": "username", "zh_name": "姓名"}, {"name": "sex", "zh_name": "性别"},
                         {"name": "iphone", "zh_name": "手机号"}, {"name": "chepinpai", "zh_name": "车品牌"},
                         {"name": "type", "zh_name": "车类型"}, {"name": "zhuangzailiang", "zh_name": "车装载量"}])
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
                AssetSql.storage2: storage2,
                AssetSql.state: state,
                AssetSql.mode: mode,
                AssetSql.flag: flag,
                AssetSql.dictvalue: dictvalue,
                AssetSql.dictvalue2: dictvalue2,
                AssetSql.authorized: authorized,
                AssetSql.fieldname: fieldname,
                AssetSql.fieldlist: str(fieldlist),
                AssetSql.create_time: create_time,
            })
            session.commit()
        self.write(dict(code=0, msg='成功', count=0, data=[]))


class getSqlListHandler(BaseHandler):
    def get(self, *args, **kwargs):
        data_list = []
        superuser_flag = 0
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

            todata = session.query(AssetSql).filter(*conditions).order_by(AssetSql.create_time.desc()).offset(
                limit_start).limit(int(tolimit)).all()
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
            case_dict["storage2"] = data_dict["storage2"]
            case_dict["mode"] = data_dict["mode"]
            case_dict["state"] = data_dict["state"]
            case_dict["flag"] = data_dict["flag"]
            case_dict["dictvalue"] = data_dict["dictvalue"]
            case_dict["dictvalue2"] = data_dict["dictvalue2"]
            case_dict["fieldname"] = data_dict["fieldname"]
            case_dict["authorized"] = str(data_dict["authorized"])
            case_dict["create_time"] = str(data_dict["create_time"])
            data_list.append(case_dict)

        if len(data_list) > 0:
            self.write(dict(code=0, msg='获取成功', count=tocount, data=data_list, flag=superuser_flag))
        else:
            self.write(dict(code=-1, msg='没有相关数据', count=0, data=[], flag=superuser_flag))


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
            # conditions.append(AssetSql.totype == "sql")
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
            case_dict["storage2"] = data_dict["storage2"]
            case_dict["dictvalue"] = data_dict["dictvalue"]
            case_dict["dictvalue2"] = data_dict["dictvalue2"]
            case_dict["create_time"] = str(data_dict["create_time"])
            data_list.append({"id": case_dict["id"], "name": case_dict["name"]})

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
            case_dict["storage2"] = data_dict["storage2"]
            case_dict["mode"] = data_dict["mode"]
            case_dict["dictvalue"] = data_dict["dictvalue"]
            case_dict["dictvalue2"] = data_dict["dictvalue2"]
            case_dict["fieldname"] = data_dict["fieldname"]
            case_dict["state"] = data_dict["state"]
            case_dict["create_time"] = str(data_dict["create_time"])
            data_list.append(case_dict)

        if len(data_list) > 0:
            self.write(dict(code=0, msg='获取成功', data=data_list))
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
                objlist.append({"k": num, "v": case_dict["obj"]})
            if case_dict["department"] not in de_list:
                de_list.append(case_dict["department"])
                department_list.append({"k": num, "v": case_dict["department"]})
            num = num + 1

        if len(department_list) > 0:
            self.write(dict(code=0, msg='获取成功', data=department_list, objlist=objlist))
        else:
            self.write(dict(code=-1, msg='没有相关数据', count=0, data=[], objlist=[]))


class getstoragelist(BaseHandler):
    def get(self, *args, **kwargs):
        data_list = []
        department = self.get_argument('department', strip=True)
        obj = self.get_argument('obj', strip=True)
        with DBContext('r') as session:
            conditions = []
            # conditions.append(AssetSql.department == department)
            department = "'" + department + "'"
            conditions.append(AssetSql.department.like('%{}%'.format(department)))
            conditions.append(AssetSql.obj == obj)
            todata = session.query(AssetSql).filter(*conditions).all()

        for msg in todata:
            case_dict = {}
            data_dict = model_to_dict(msg)
            case_dict["id"] = data_dict["id"]
            case_dict["obj"] = data_dict["obj"]
            case_dict["name"] = data_dict["name"]
            case_dict["department"] = data_dict["department"]
            case_dict["storage"] = data_dict["storage"]
            data_list.append({"k": case_dict["id"], "v": case_dict["name"], "n": case_dict["storage"]})

        if len(data_list) > 0:
            self.write(dict(code=0, msg='获取成功', data=data_list))
        else:
            self.write(dict(code=-1, msg='没有相关数据', count=0, data=[]))


class getimplementlist(BaseHandler):
    def get(self, *args, **kwargs):
        data_list = []
        data_list2 = []
        parameter = eval(self.get_argument('parameter', strip=True))  # 参数列表
        storage = self.get_argument('storage', strip=True)  # 存储过程id
        flag = self.get_argument('flag', strip=True)  # 1执行sql，2执行存储过程
        targetKeys = self.get_argument('targetKeys', strip=True)  # 需要查询的字段列表
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
            case_dict["storage"] = data_dict["storage"]  # cha xun
            case_dict["storage2"] = data_dict["storage2"]  # shengcheng
            case_dict["fieldlist"] = data_dict["fieldlist"]
            case_dict["fieldname"] = data_dict["fieldname"]
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
                case_dict["db_instance"] = data_dict["db_instance"]  # 库名
                case_dict["db_host"] = data_dict["db_host"]
                case_dict["db_port"] = data_dict["db_port"]
                case_dict["db_user"] = data_dict["db_user"]
                case_dict["db_pwd"] = data_dict["db_pwd"]
                case_dict["db_type"] = data_dict["db_type"]  # oracle/mysql

                data_list2.append(case_dict)
            if str(targetKeys) == "[]":  # 当用户没有选择字段时，默认查询所有字段
                targetKeys = []
                for j in eval(str(data_list[0]["fieldlist"])):
                    targetKeys.append(str(j["name"]))
            title_list = []
            columns_list = []
            table_key = []
            key_list = eval(str(targetKeys))
            for h in eval(str(targetKeys)):
                for j in eval(str(data_list[0]["fieldlist"])):
                    table_key.append(str(j["name"]))  # 获取表全部的字段
                    if str(j["name"]) == str(h):
                        columns_list.append({"title": str(j["zh_name"]), "key": h, "width": 150, "editable": "true"})
                        title_list.append(str(j["zh_name"]))
            # if len(columns_list) > 6:
            #       columns_list[0]["fixed"] = "left"
            #       columns_list[len(columns_list) -1]["fixed"] = "right" 
            # 拼接sql语句
            # flag_date = 0
            # ins_log.read_log('info', "80xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx00")
            # ins_log.read_log('info', targetKeys)
            # ins_log.read_log('info', "800000000000000000000000000000000000")
            # num_temp = len(eval(str(targetKeys)))
            # sql_temp_str  = "select  "
            # for  h in range(0,num_temp -1):
            #     sql_temp_str = sql_temp_str + eval(str(targetKeys))[h] + ",  " 
            # sql_temp_str = sql_temp_str + str(eval(str(targetKeys))[num_temp -1])  +  "  from  "  +   str(data_list[0]["fieldname"])
            # for  t in  eval(str(data_list[0]["fieldlist"])):
            #        if "BEGINDATE" == str(t["name"])  or  "ENDDATE"  == str(t["name"]):
            #            flag_date = 1
            #            sql_temp_str = sql_temp_str +   "  where  begindate>=to_date('sDate','yyyyMMdd')  and  enddate<=to_date('eDate','yyyyMMdd')"
            #        else:
            #            flag_date = 0
            # temp_date_str = str(date).split('-')
            # import calendar
            # tian_num = calendar.monthrange(int(temp_date_str[0]),int(temp_date_str[1]))[1]
            # start_temp_str = temp_date_str[0] + temp_date_str[1] +"01"
            # end_temp_str = temp_date_str[0] + temp_date_str[1] + str(tian_num)

            data_list3 = []
            CUSTOM_DB_INFO = dict(
                host=data_list2[0]["db_host"],
                port=data_list2[0]["db_port"],
                user=data_list2[0]["db_user"],
                passwd=decrypt(data_list2[0]["db_pwd"]),
                db=data_list2[0]["db_instance"])
            try:
                if data_list2[0]["db_type"] == "mysql":
                    mysql_conn = MysqlBase(**CUSTOM_DB_INFO)
                    start_time = time.time()
                    if str(flag) == "1":
                        # db_data = mysql_conn.query(q_sqlstr)
                        pass
                    if str(flag) == "2":
                        pass
                    end_time = time.time()
                    time_storage_str = str(int(end_time - start_time) / 60 / 60) + "小时" + str(
                        int(end_time - start_time) / 60 % 60) + "分" + str(int(end_time - start_time) % 60) + "秒" + str(
                        int((end_time - start_time) * 1000) % 1000) + "毫秒"
                if data_list2[0]["db_type"] == "oracle":
                    temp_str = data_list2[0]["db_host"] + '/' + data_list2[0]["db_instance"]
                    oracle_conn = cx_Oracle.connect(data_list2[0]["db_user"], decrypt(data_list2[0]["db_pwd"]),
                                                    temp_str)
                    cur = oracle_conn.cursor()
                    temp_msg_code = cur.var(cx_Oracle.STRING)
                    temp_msg_remarks = cur.var(cx_Oracle.STRING)
                    msg_data = cur.var(cx_Oracle.DB_TYPE_CURSOR)
                    temp_parameter_list = []
                    for n in range(0, len(parameter)):
                        for h in parameter:
                            if n == int(h["toindex"]):
                                temp_parameter_list.append(str(h["msg"]))
                    temp_parameter_list += [temp_msg_code, temp_msg_remarks, msg_data]
                    ins_log.read_log('info', temp_parameter_list)
                    temp_fieldlist_list5 = eval(str(data_list[0]["fieldlist"]))
                    temp_fieldlist_num = len(temp_fieldlist_list5)

                    start_time = time.time()
                    # 查询存储过程
                    if str(flag) == "1":
                        ins_log.read_log('info', data_list[0]["storage"])
                        temp_table_data = cur.callproc(data_list[0]["storage"], temp_parameter_list)
                    if str(flag) == "2":
                        ins_log.read_log('info', data_list[0]["storage2"])
                        temp_table_data = cur.callproc(data_list[0]["storage2"], temp_parameter_list)

                    end_time = time.time()
                    time_storage_str = str(int(end_time - start_time) / 60 / 60) + "小时" + str(
                        int(end_time - start_time) / 60 % 60) + "分" + str(int(end_time - start_time) % 60) + "秒" + str(
                        int((end_time - start_time) * 1000) % 1000) + "毫秒"
                    ins_log.read_log('info', "80xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx00")
                    ins_log.read_log('info', end_time)
                    ins_log.read_log('info', start_time)
                    ins_log.read_log('info', end_time - start_time)
                    ins_log.read_log('info', time_storage_str)
                    ins_log.read_log('info', "800000000000000000000000000000000000")
                    for i in msg_data.getvalue():
                        len_num = len(i)
                        temp_dict = {}
                        for n in range(0, temp_fieldlist_num):
                            if str(i[n]) == "None":
                                temp_dict[table_key[n]] = ''
                            else:
                                temp_dict[table_key[n]] = str(i[n])
                        data_list3.append(temp_dict)
                    cur.close()
                    oracle_conn.close()

            except:
                traceback.print_exc()

            # ins_log.read_log('info', data_list3)
            if str(flag) == "1":
                update_storage(data_list[0]["storage"], time_storage_str)
            if str(flag) == "2":
                update_storage(data_list[0]["storage2"], time_storage_str)
            data_list3 = [
                {"bianhao": "020", "number": "粵A88888", "username": "張天浩", "sex": "男", "iphone": "13100001235",
                 "chepinpai": "解放牌", "type": "轎車", "zhuangzailiang": "20頓"},
                {"bianhao": "020", "number": "粵A88888", "username": "張天磊", "sex": "男", "iphone": "13100987635",
                 "chepinpai": "解放牌", "type": "轎車", "zhuangzailiang": "20頓"},
                {"bianhao": "020", "number": "粵A88888", "username": "張天武", "sex": "男", "iphone": "13100123935",
                 "chepinpai": "解放牌", "type": "轎車", "zhuangzailiang": "20頓"},
                ]
            if len(data_list3) > 0:
                self.write(dict(code=0, msg='获取成功', data=data_list3, columnslist=columns_list, titlelist=title_list,
                                keylist=key_list))
        else:
            self.write(dict(code=-1, msg='没有相关存储过程数据', data=[], columns_listb=[], titlelist=[], keylist=[]))


class getobjlist(BaseHandler):
    def get(self, *args, **kwargs):
        data_list = []
        data_list2 = []
        temp_list = []
        temp_list2 = []
        temp_list3 = []
        department = self.get_argument('department', strip=True)
        with DBContext('r') as session:
            conditions = []
            department = "'" + department + "'"
            conditions.append(AssetSql.department.like('%{}%'.format(department)))
            conditions.append(AssetSql.totype == "存储过程")
            conditions.append(AssetSql.state == "运行")
            todata = session.query(AssetSql).filter(*conditions).all()
        for msg in todata:
            case_dict = {}
            data_dict = model_to_dict(msg)
            case_dict["id"] = data_dict["id"]
            case_dict["obj"] = data_dict["obj"]
            case_dict["name"] = data_dict["name"]
            case_dict["department"] = data_dict["department"]
            case_dict["storage"] = data_dict["storage"]
            case_dict["storage2"] = data_dict["storage2"]
            case_dict["dictvalue"] = data_dict["dictvalue"]
            case_dict["dictvalue2"] = data_dict["dictvalue2"]
            case_dict["flag"] = data_dict["flag"]
            case_dict["authorized"] = data_dict["authorized"]
            case_dict["fieldlist"] = data_dict["fieldlist"]
            case_dict["fieldname"] = data_dict["fieldname"]
            if case_dict["obj"] not in temp_list:
                temp_list.append(case_dict["obj"])
                data_list.append({"v": case_dict["obj"], "t": case_dict["flag"]})
            data_list2.append(case_dict)

        for i in temp_list:
            temp_list2.append({"name": i, "date": []})
            temp_list3.append({"name": i, "date": []})
        for j in temp_list2:
            for d in data_list2:
                if str(j["name"]) == str(d["obj"]):
                    j["date"].append(
                        {"k": d["id"], "v": d["name"], "t": d["flag"], "s": d["storage"], "st": d["storage2"],
                         "d": d["fieldlist"], "f": d["fieldname"], "c": d["dictvalue"]})
        for k in temp_list3:
            for d in data_list2:
                if str(k["name"]) == str(d["obj"]):
                    if str(d["authorized"]) != "[]":
                        authorized_temp_list = []
                        for a in eval(str(d["authorized"])):
                            k["date"].append(a)
        # ins_log.read_log('info', "800000000000000000000000000000000000")
        # ins_log.read_log('info', temp_list3)
        # ins_log.read_log('info', "800000000000000000000000000000000000")
        temp_list_all = []
        nickname = self.get_current_nickname()
        if self.is_superuser:
            pass
        else:
            for i in temp_list3:
                if nickname in i['date']:
                    for h in data_list:
                        if i["name"] == h["v"]:
                            temp_list_all.append(h)

            data_list = temp_list_all

        if len(data_list) > 0:
            self.write(dict(code=0, msg='获取成功', data=data_list, storagelist=temp_list2))
        else:
            self.write(dict(code=-1, msg='没有相关数据', count=0, data=[]))


def update_storage(name, time_str):
    try:
        with DBContext('w', None, True) as session:
            session.query(Storage).filter(Storage.name == name).update({
                Storage.name: name,
                Storage.consume: time_str,
            })
            session.commit()
    except Exception as e:
        return self.write(dict(code=-2, msg='修改失败，请检查数据是否合法或者重复'))
    return 0


class getSqlobjlist(BaseHandler):
    def get(self, *args, **kwargs):
        data_list = []
        data_list2 = []
        temp_list = []
        temp_list2 = []
        temp_list3 = []
        department = self.get_argument('department', strip=True)
        with DBContext('r') as session:
            conditions = []
            department = "'" + department + "'"
            conditions.append(AssetSql.department.like('%{}%'.format(department)))
            conditions.append(AssetSql.totype == "sql")
            conditions.append(AssetSql.state == "运行")
            todata = session.query(AssetSql).filter(*conditions).all()
        for msg in todata:
            case_dict = {}
            data_dict = model_to_dict(msg)
            case_dict["id"] = data_dict["id"]
            case_dict["obj"] = data_dict["obj"]
            case_dict["name"] = data_dict["name"]
            case_dict["department"] = data_dict["department"]
            case_dict["storage"] = data_dict["storage"]
            case_dict["storage2"] = data_dict["storage2"]
            case_dict["dictvalue"] = data_dict["dictvalue"]
            case_dict["dictvalue2"] = data_dict["dictvalue2"]
            case_dict["flag"] = data_dict["flag"]
            case_dict["authorized"] = data_dict["authorized"]
            case_dict["fieldlist"] = data_dict["fieldlist"]
            case_dict["fieldname"] = data_dict["fieldname"]
            if case_dict["obj"] not in temp_list:
                temp_list.append(case_dict["obj"])
                data_list.append({"v": case_dict["obj"], "t": case_dict["flag"]})
            data_list2.append(case_dict)

        for i in temp_list:
            temp_list2.append({"name": i, "date": []})
            temp_list3.append({"name": i, "date": []})
        for j in temp_list2:
            for d in data_list2:
                if str(j["name"]) == str(d["obj"]):
                    j["date"].append(
                        {"k": d["id"], "v": d["name"], "t": d["flag"], "s": d["storage"], "st": d["storage2"],
                         "d": d["fieldlist"], "f": d["fieldname"], "c": d["dictvalue"]})
        for k in temp_list3:
            for d in data_list2:
                if str(k["name"]) == str(d["obj"]):
                    if str(d["authorized"]) != "[]":
                        authorized_temp_list = []
                        for a in eval(str(d["authorized"])):
                            k["date"].append(a)
        # ins_log.read_log('info', "800000000000000000000000000000000000")
        # ins_log.read_log('info', temp_list3)
        # ins_log.read_log('info', "800000000000000000000000000000000000")
        temp_list_all = []
        nickname = self.get_current_nickname()
        if self.is_superuser:
            pass
        else:
            for i in temp_list3:
                if nickname in i['date']:
                    for h in data_list:
                        if i["name"] == h["v"]:
                            temp_list_all.append(h)

            data_list = temp_list_all

        if len(data_list) > 0:
            self.write(dict(code=0, msg='获取成功', data=data_list, storagelist=temp_list2))
        else:
            self.write(dict(code=-1, msg='没有相关数据', count=0, data=[]))


class Spoonobjlist(BaseHandler):
    def get(self, *args, **kwargs):
        data_list = []
        data_list2 = []
        temp_list = []
        temp_list2 = []
        temp_list3 = []
        department = self.get_argument('department', strip=True)
        with DBContext('r') as session:
            conditions = []
            department = "'" + department + "'"
            conditions.append(AssetSql.department.like('%{}%'.format(department)))
            conditions.append(AssetSql.totype == "自定义sql")
            conditions.append(AssetSql.state == "运行")
            todata = session.query(AssetSql).filter(*conditions).all()
        for msg in todata:
            case_dict = {}
            data_dict = model_to_dict(msg)
            case_dict["id"] = data_dict["id"]
            case_dict["obj"] = data_dict["obj"]
            case_dict["name"] = data_dict["name"]
            case_dict["department"] = data_dict["department"]
            case_dict["storage"] = data_dict["storage"]
            case_dict["storage2"] = data_dict["storage2"]
            case_dict["dictvalue"] = data_dict["dictvalue"]
            case_dict["dictvalue2"] = data_dict["dictvalue2"]
            case_dict["flag"] = data_dict["flag"]
            case_dict["authorized"] = data_dict["authorized"]
            case_dict["fieldlist"] = data_dict["fieldlist"]
            case_dict["fieldname"] = data_dict["fieldname"]
            if case_dict["obj"] not in temp_list:
                temp_list.append(case_dict["obj"])
                data_list.append({"v": case_dict["obj"], "t": case_dict["flag"]})
            data_list2.append(case_dict)

        for i in temp_list:
            temp_list2.append({"name": i, "date": []})
            temp_list3.append({"name": i, "date": []})
        for j in temp_list2:
            for d in data_list2:
                if str(j["name"]) == str(d["obj"]):
                    j["date"].append(
                        {"k": d["id"], "v": d["name"], "t": d["flag"], "s": d["storage"], "st": d["storage2"],
                         "d": d["fieldlist"], "f": d["fieldname"], "c": d["dictvalue"]})
        for k in temp_list3:
            for d in data_list2:
                if str(k["name"]) == str(d["obj"]):
                    if str(d["authorized"]) != "[]":
                        authorized_temp_list = []
                        for a in eval(str(d["authorized"])):
                            k["date"].append(a)
        # ins_log.read_log('info', "800000000000000000000000000000000000")
        # ins_log.read_log('info', temp_list3)
        # ins_log.read_log('info', "800000000000000000000000000000000000")
        temp_list_all = []
        nickname = self.get_current_nickname()
        if self.is_superuser:
            pass
        else:
            for i in temp_list3:
                if nickname in i['date']:
                    for h in data_list:
                        if i["name"] == h["v"]:
                            temp_list_all.append(h)

            data_list = temp_list_all

        if len(data_list) > 0:
            self.write(dict(code=0, msg='获取成功', data=data_list, storagelist=temp_list2))
        else:
            self.write(dict(code=-1, msg='没有相关数据', count=0, data=[]))




class getimplementlist2(BaseHandler):
    def get(self, *args, **kwargs):
        data_list = []
        data_list2 = []
        # parameter = eval(self.get_argument('parameter', strip=True))  # 参数列表
        storage = self.get_argument('storage', strip=True)  # 存储过程id
        # flag = self.get_argument('flag', strip=True)  # 1执行sql，2执行存储过程
        # targetKeys = self.get_argument('targetKeys', strip=True)  # 需要查询的字段列表
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
            case_dict["storage"] = data_dict["storage"]  # cha xun
            case_dict["storage2"] = data_dict["storage2"]  # shengcheng
            case_dict["fieldlist"] = data_dict["fieldlist"]
            case_dict["fieldname"] = data_dict["fieldname"]
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
                case_dict["db_instance"] = data_dict["db_instance"]  # 库名
                case_dict["db_host"] = data_dict["db_host"]
                case_dict["db_port"] = data_dict["db_port"]
                case_dict["db_user"] = data_dict["db_user"]
                case_dict["db_pwd"] = data_dict["db_pwd"]
                case_dict["db_type"] = data_dict["db_type"]  # oracle/mysql

                data_list2.append(case_dict)
            # if str(targetKeys) == "[]":  # 当用户没有选择字段时，默认查询所有字段
            #     targetKeys = []
            #     for j in eval(str(data_list[0]["fieldlist"])):
            #         targetKeys.append(str(j["name"]))
            # 解析excel表头
            # q_header.split('|')
            temp_copy = copy.deepcopy(data_list[0]["header"])
            temp_copy2 = temp_copy.split('|')
            title_list = []
            columns_list = []
            table_key = []
            key_list = temp_copy2
            for h in temp_copy2:
                columns_list.append({"title": h, "key": h, "width": 150, "editable": "true"})
                title_list.append(str(h))
                table_key.append(str(h))

            # for h in eval(str(targetKeys)):
            #     for j in eval(str(data_list[0]["fieldlist"])):
            #         table_key.append(str(j["name"]))  # 获取表全部的字段
            #         if str(j["name"]) == str(h):
            #             columns_list.append({"title": str(j["zh_name"]), "key": h, "width": 150, "editable": "true"})
            #             title_list.append(str(j["zh_name"]))
            # if len(columns_list) > 6:
            #       columns_list[0]["fixed"] = "left"
            #       columns_list[len(columns_list) -1]["fixed"] = "right"
            # 拼接sql语句
            # flag_date = 0
            # ins_log.read_log('info', "80xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx00")
            # ins_log.read_log('info', targetKeys)
            # ins_log.read_log('info', "800000000000000000000000000000000000")
            # num_temp = len(eval(str(targetKeys)))
            # sql_temp_str  = "select  "
            # for  h in range(0,num_temp -1):
            #     sql_temp_str = sql_temp_str + eval(str(targetKeys))[h] + ",  "
            # sql_temp_str = sql_temp_str + str(eval(str(targetKeys))[num_temp -1])  +  "  from  "  +   str(data_list[0]["fieldname"])
            # for  t in  eval(str(data_list[0]["fieldlist"])):
            #        if "BEGINDATE" == str(t["name"])  or  "ENDDATE"  == str(t["name"]):
            #            flag_date = 1
            #            sql_temp_str = sql_temp_str +   "  where  begindate>=to_date('sDate','yyyyMMdd')  and  enddate<=to_date('eDate','yyyyMMdd')"
            #        else:
            #            flag_date = 0
            # temp_date_str = str(date).split('-')
            # import calendar
            # tian_num = calendar.monthrange(int(temp_date_str[0]),int(temp_date_str[1]))[1]
            # start_temp_str = temp_date_str[0] + temp_date_str[1] +"01"
            # end_temp_str = temp_date_str[0] + temp_date_str[1] + str(tian_num)

            data_list3 = []
            CUSTOM_DB_INFO = dict(
                host=data_list2[0]["db_host"],
                port=data_list2[0]["db_port"],
                user=data_list2[0]["db_user"],
                passwd=decrypt(data_list2[0]["db_pwd"]),
                db=data_list2[0]["db_instance"])
            try:
                if data_list2[0]["db_type"] == "mysql":
                    mysql_conn = MysqlBase(**CUSTOM_DB_INFO)
                    # start_time = time.time()
                    # if str(flag) == "1":
                    #     # db_data = mysql_conn.query(q_sqlstr)
                    #     pass
                    db_data = mysql_conn.query(data_list[0]["sqlstr"])

                    table_colsname = mysql_conn.cur.description  # 获取sql查询字段列表
                    temp_table_key = [i[0] for i in table_colsname]
                    if str(table_key) == "['']":
                        table_key =[]
                        key_list = []
                        columns_list = []
                        title_list = []
                        table_key = temp_table_key
                        temp_copy2 = temp_table_key
                        key_list = temp_copy2
                        for h in temp_copy2:
                            columns_list.append({"title": h, "key": h, "width": 150, "editable": "true"})
                            title_list.append(str(h))

                    for i in db_data:
                        len_num = len(i)
                        temp_dict = {}
                        for n in range(0, len(i)):
                            if str(i[n]) == "None":
                                temp_dict[table_key[n]] = ''
                            else:
                                temp_dict[table_key[n]] = str(i[n])
                        data_list3.append(temp_dict)

                    # if str(flag) == "2":
                    #     pass

                    # end_time = time.time()
                    # time_storage_str = str(int(end_time - start_time) / 60 / 60) + "小时" + str(
                    #     int(end_time - start_time) / 60 % 60) + "分" + str(int(end_time - start_time) % 60) + "秒" + str(
                    #     int((end_time - start_time) * 1000) % 1000) + "毫秒"
                if data_list2[0]["db_type"] == "oracle":
                    temp_str = data_list2[0]["db_host"] + '/' + data_list2[0]["db_instance"]
                    oracle_conn = cx_Oracle.connect(data_list2[0]["db_user"], decrypt(data_list2[0]["db_pwd"]),
                                                    temp_str)
                    cur = oracle_conn.cursor()
                    db_data2 = cur.execute(data_list[0]["sqlstr"])
                    table_colsname = cur.description  # 获取sql查询字段列表
                    temp_table_key = [i[0] for i in table_colsname]
                    if str(table_key) == "['']":
                        table_key = key_list = columns_list = title_list = []
                        table_key = temp_table_key
                        temp_copy2 = temp_table_key
                        key_list = temp_copy2
                        for h in temp_copy2:
                            columns_list.append({"title": h, "key": h, "width": 150, "editable": "true"})
                            title_list.append(str(h))
                    for i in db_data2:
                        len_num = len(i)
                        temp_dict = {}
                        for n in range(0, len(i)):
                            if str(i[n]) == "None":
                                temp_dict[table_key[n]] = ''
                            else:
                                temp_dict[table_key[n]] = str(i[n])
                        data_list3.append(temp_dict)
                    # temp_msg_code = cur.var(cx_Oracle.STRING)
                    # temp_msg_remarks = cur.var(cx_Oracle.STRING)
                    # msg_data = cur.var(cx_Oracle.DB_TYPE_CURSOR)
                    # temp_parameter_list = []
                    # for n in range(0, len(parameter)):
                    #     for h in parameter:
                    #         if n == int(h["toindex"]):
                    #             temp_parameter_list.append(str(h["msg"]))
                    # temp_parameter_list += [temp_msg_code, temp_msg_remarks, msg_data]
                    # ins_log.read_log('info', temp_parameter_list)
                    # temp_fieldlist_list5 = eval(str(data_list[0]["fieldlist"]))
                    # temp_fieldlist_num = len(temp_fieldlist_list5)

                    # start_time = time.time()
                    # # 查询存储过程
                    # if str(flag) == "1":
                    #     ins_log.read_log('info', data_list[0]["storage"])
                    #     temp_table_data = cur.callproc(data_list[0]["storage"], temp_parameter_list)
                    # if str(flag) == "2":
                    #     ins_log.read_log('info', data_list[0]["storage2"])
                    #     temp_table_data = cur.callproc(data_list[0]["storage2"], temp_parameter_list)

                    # end_time = time.time()
                    # time_storage_str = str(int(end_time - start_time) / 60 / 60) + "小时" + str(
                    #     int(end_time - start_time) / 60 % 60) + "分" + str(int(end_time - start_time) % 60) + "秒" + str(
                    #     int((end_time - start_time) * 1000) % 1000) + "毫秒"
                    # ins_log.read_log('info', "80xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx00")
                    # ins_log.read_log('info', end_time)
                    # ins_log.read_log('info', start_time)
                    # ins_log.read_log('info', end_time - start_time)
                    # ins_log.read_log('info', time_storage_str)
                    # ins_log.read_log('info', "800000000000000000000000000000000000")
                    # for i in msg_data.getvalue():
                    #     len_num = len(i)
                    #     temp_dict = {}
                    #     for n in range(0, temp_fieldlist_num):
                    #         if str(i[n]) == "None":
                    #             temp_dict[table_key[n]] = ''
                    #         else:
                    #             temp_dict[table_key[n]] = str(i[n])
                    #     data_list3.append(temp_dict)
                    cur.close()
                    oracle_conn.close()

            except:
                traceback.print_exc()

            # ins_log.read_log('info', data_list3)
            # if str(flag) == "1":
            #     update_storage(data_list[0]["storage"], time_storage_str)
            # if str(flag) == "2":
            #     update_storage(data_list[0]["storage2"], time_storage_str)
            # data_list3 = [
            #     {"bianhao": "020", "number": "粵A88888", "username": "張天浩", "sex": "男", "iphone": "13100001235",
            #      "chepinpai": "解放牌", "type": "轎車", "zhuangzailiang": "20頓"},
            #     {"bianhao": "020", "number": "粵A88888", "username": "張天磊", "sex": "男", "iphone": "13100987635",
            #      "chepinpai": "解放牌", "type": "轎車", "zhuangzailiang": "20頓"},
            #     {"bianhao": "020", "number": "粵A88888", "username": "張天武", "sex": "男", "iphone": "13100123935",
            #      "chepinpai": "解放牌", "type": "轎車", "zhuangzailiang": "20頓"},
            #     ]
            if len(data_list3) > 0:
                self.write(dict(code=0, msg='获取成功', data=data_list3, columnslist=columns_list, titlelist=title_list,
                                keylist=key_list))
        else:
            self.write(dict(code=-1, msg='没有相关存储过程数据', data=[], columns_listb=[], titlelist=[], keylist=[]))


assetSql_urls = [
    (r"/v1/sql/add/", SqlListHandler),
    (r"/v1/sql/list/", getSqlListHandler),
    (r"/v1/sql/Idlist/", getSqlIdList),
    (r"/v1/sql/IdDate/", getSqlIdDate),
    (r"/v1/sql/delete/", sqlDelete),
    (r"/v1/sql/departmentlist/", getdepartmentlist),
    (r"/v1/sql/storagelist/", getstoragelist),
    (r"/v1/sql/objlist/", getobjlist),
    (r"/v1/sql/Sqlobjlist/", getSqlobjlist),
    (r"/v1/sql/Spoonobjlist/", Spoonobjlist),
    (r"/v1/sql/implement/", getimplementlist),
    (r"/v1/sql/implement2/", getimplementlist2),
]

if __name__ == "__main__":
    pass
