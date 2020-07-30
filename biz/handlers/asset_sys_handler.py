#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/6/14
# @Author  : Fengjianping


import json
from libs.base_handler import BaseHandler
from sqlalchemy import or_, and_
from models.sys import Sys, model_to_dict, SysSoft, SysUpgrade, SysManager
from models.server import Server
from models.software import soft_type_dict
from websdk.db_context import DBContext
from websdk.web_logs import ins_log
import os
import json
from settings import CODO_PROBLEM_DB_INFO
from libs.mysql_conn import MysqlBase
import urllib
from settings import onlinePreview

SOFT_TYPE = {
    '1': '操作系统',
    '2': '虚拟化',
    '3': '数据库',
    '4': '服务',
    '5': '中间件',
    '6': '应用服务',
    '7': 'Web服务',
    '8': '其他'
}


def getPreviewUrl(request, url):
    url = urllib.parse.quote_plus(url)
    onlinePreviewurl = onlinePreview.format(request.host_name)
    viewUrl = '{0}{1}&officePreviewType=pdf'.format(onlinePreviewurl, url)
    return viewUrl


class SysHandler(BaseHandler):
    def get(self, *args, **kwargs):
        # nickname = self.get_current_nickname()
        key = self.get_argument('key', default=None, strip=True)
        value = self.get_argument('value', default=None, strip=True)
        page_size = self.get_argument('page', default=1, strip=True)
        limit = self.get_argument('limit', default="999", strip=True)
        limit_start = (int(page_size) - 1) * int(limit)
        sys_list = []
        mysql_conn = MysqlBase(**CODO_PROBLEM_DB_INFO)

        with DBContext('r') as session:
            if key == 'sys_name' and value:
                count = session.query(Sys).filter(Sys.sys_name.like('%{}%'.format(value))).count()
                all_sys = session.query(Sys).filter(Sys.sys_name.like('%{}%'.format(value))).order_by(
                    Sys.id).offset(
                    limit_start).limit(int(limit))
            elif key and key != 'sys_name' and value:
                count = session.query(Sys).filter_by(**{key: value}).count()
                all_sys = session.query(Sys).order_by(Sys.id).filter_by(**{key: value}).order_by(Sys.id).offset(
                    limit_start).limit(int(limit))
            elif limit == '999':
                count = session.query(Sys).count()
                all_sys = session.query(Sys).order_by(Sys.id).all()
            else:
                count = session.query(Sys).count()
                all_sys = session.query(Sys).order_by(Sys.id).offset(limit_start).limit(int(limit))

            for msg in all_sys:
                data_dict = model_to_dict(msg)
                data_dict['online_time'] = str(data_dict['online_time'])
                soft_list = session.query(SysSoft).filter(SysSoft.sys_id == data_dict['id']).all()
                data_dict['soft_list'] = []
                if data_dict['uploadList'] and data_dict['uploadList'] != 'null':
                    data_dict['uploadList'] = json.loads(str(data_dict['uploadList']))
                    # data_dict['uploadList']['url'] = getPreviewUrl(self.request, data_dict['uploadList']['url'])
                    for i in data_dict['uploadList']:
                        i['url'] = getPreviewUrl(self.request, i['url'])
                else:
                    data_dict['uploadList'] = []

                for soft in soft_list:
                    soft_dict = model_to_dict(soft)
                    soft_dict['soft_type_name'] = [int(soft_dict['soft_type']), soft_dict['soft_name']]
                    soft_dict['soft_type'] = soft_type_dict.get(soft_dict['soft_type'], soft_dict['soft_type'])
                    data_dict['soft_list'].append(soft_dict)

                sys_manager_list = session.query(SysManager).filter(SysManager.sys_id == data_dict['id']).all()
                data_dict['sys_manager_list'] = []
                for sys_mg in sys_manager_list:
                    sys_mg_dict = model_to_dict(sys_mg)
                    data_dict['sys_manager_list'].append(sys_mg_dict)

                select_docx_sql = 'select f_name, f_url from pb_docxs where sysID = {}'.format(data_dict['id'])
                sys_docx_list = mysql_conn.query(select_docx_sql)
                # ins_log.read_log('info', sys_docx_list)
                data_dict['sys_docx_list'] = []
                for l in sys_docx_list:
                    _d = {
                        'name': l[0],
                        'url': getPreviewUrl(self.request, l[1])
                    }
                    data_dict['sys_docx_list'].append(_d)

                sys_list.append(data_dict)

        if len(sys_list) > 0:
            self.write(dict(code=0, msg='获取成功', count=count, data=sys_list))
        else:
            self.write(dict(code=-1, msg='没有查询到数据', count=count, data=sys_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        sys_name = data.get('sys_name')
        sys_version = data.get('sys_version')
        sys_info = data.get('sys_info')
        online_time = data.get('online_time')
        development_phone = data.get('development_phone')
        development_contact = data.get('development_contact')
        development = data.get('development')
        soft_list = data.get('soft_list')
        sys_manager_list = data.get('sys_manager_list')
        uploadList = data.get('uploadList')

        if not sys_name:
            return self.write(dict(code=-1, msg='系统名称不能为空'))

        with DBContext('r') as session:
            exist_id = session.query(Sys.id).filter(Sys.sys_name == sys_name).first()

        if exist_id:
            return self.write(dict(code=-2, msg='系统名称重复'))

        with DBContext('w', None, True) as session:
            new_sys = Sys(
                sys_name=sys_name, sys_version=sys_version, sys_info=sys_info, online_time=online_time,
                development_phone=development_phone, development_contact=development_contact,
                development=development, uploadList=json.dumps(uploadList),
            )
            session.add(new_sys)
            session.commit()

        with DBContext('r') as session:
            sys_id = session.query(Sys.id).filter(Sys.sys_name == sys_name).first()[0]

        with DBContext('w', None, True) as session:
            for soft in soft_list:
                if not soft['soft_type_name']:
                    continue
                soft_type = int(soft['soft_type_name'][0])
                soft_name = soft['soft_type_name'][1]
                new_sys_soft = SysSoft(
                    soft_name=soft_name, soft_type=soft_type, soft_version=soft['soft_version'],
                    soft_ip=soft['soft_ip'], soft_hostname=soft['soft_hostname'],
                    soft_usage=soft['soft_usage'], sys_id=sys_id,
                )
                session.add(new_sys_soft)
            session.commit()

        with DBContext('w', None, True) as session:
            for sys_mg in sys_manager_list:
                if not sys_mg['sys_manager_name']:
                    continue
                sys_manager_name = sys_mg['sys_manager_name']
                sys_manager_phone = sys_mg['sys_manager_phone']
                sys_manager_role = sys_mg['sys_manager_role']
                new_sys_soft = SysManager(
                    sys_manager_name=sys_manager_name,
                    sys_manager_phone=sys_manager_phone,
                    sys_manager_role=sys_manager_role,
                    sys_id=sys_id,
                )
                session.add(new_sys_soft)
            session.commit()

        self.write(dict(code=0, msg='添加成功'))

    def put(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        sys_name = data.get('sys_name')
        sys_version = data.get('sys_version')
        sys_info = data.get('sys_info')
        online_time = data.get('online_time')
        development_phone = data.get('development_phone')
        development_contact = data.get('development_contact')
        development = data.get('development')
        soft_list = data.get('soft_list')
        sys_manager_list = data.get('sys_manager_list')
        sys_id = data.get('id')
        uploadList = data.get('uploadList')

        if not sys_name:
            return self.write(dict(code=-1, msg='系统名称不能为空'))

        with DBContext('r') as session:
            exist_id = session.query(Sys.id).filter(and_(Sys.sys_name == sys_name,
                                                         Sys.id != sys_id,
                                                         )).first()

        if exist_id:
            return self.write(dict(code=-2, msg='已存在的系统名称'))

        with DBContext('w', None, True) as session:
            session.query(Sys).filter(Sys.id == sys_id).update({
                Sys.sys_name: sys_name, Sys.sys_version: sys_version, Sys.sys_info: sys_info,
                Sys.online_time: online_time,
                Sys.development_phone: development_phone, Sys.development_contact: development_contact,
                Sys.development: development, Sys.uploadList: json.dumps(uploadList),
            }, synchronize_session=False)

            for soft in soft_list:
                soft_id = soft.get('id', 0)
                if not soft['soft_type_name']:
                    continue
                soft_type = int(soft['soft_type_name'][0])
                soft_name = soft['soft_type_name'][1]
                if soft_id:
                    session.query(SysSoft).filter(SysSoft.id == soft_id).update({
                        SysSoft.soft_name: soft_name, SysSoft.soft_type: soft_type, SysSoft.soft_ip: soft['soft_ip'],
                        SysSoft.soft_usage: soft['soft_usage'], SysSoft.soft_version: soft['soft_version'],
                        SysSoft.soft_hostname: soft['soft_hostname'],
                    }, synchronize_session=False)
                else:
                    new_sys_soft = SysSoft(
                        soft_name=soft_name, soft_type=soft_type, soft_version=soft['soft_version'],
                        soft_ip=soft['soft_ip'], soft_hostname=soft['soft_hostname'],
                        soft_usage=soft['soft_usage'], sys_id=sys_id,
                    )
                    session.add(new_sys_soft)

            for sys_mg in sys_manager_list:
                sys_mg_id = sys_mg.get('id', 0)
                if not sys_mg['sys_manager_name']:
                    continue
                sys_manager_name = sys_mg['sys_manager_name']
                sys_manager_phone = sys_mg['sys_manager_phone']
                sys_manager_role = sys_mg['sys_manager_role']
                if sys_mg_id:
                    session.query(SysManager).filter(SysManager.id == sys_mg_id).update({
                        SysManager.sys_manager_name: sys_manager_name,
                        SysManager.sys_manager_phone: sys_manager_phone,
                        SysManager.sys_manager_role: sys_manager_role,
                    }, synchronize_session=False)
                else:
                    new_sys_manager = SysManager(
                        sys_manager_name=sys_manager_name,
                        sys_manager_phone=sys_manager_phone,
                        sys_manager_role=sys_manager_role,
                        sys_id=sys_id
                    )
                    session.add(new_sys_manager)

            session.commit()

        return self.write(dict(code=0, msg='编辑成功'))

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        id = data.get('id')

        with DBContext('w', None, True) as session:
            if id:
                session.query(Sys).filter(Sys.id == id).delete(synchronize_session=False)
                session.query(SysSoft).filter(SysSoft.sys_id == id).delete(synchronize_session=False)
                session.query(SysUpgrade).filter(SysUpgrade.sys_id == id).delete(synchronize_session=False)
                session.query(SysManager).filter(SysManager.sys_id == id).delete(synchronize_session=False)
                session.commit()
            else:
                return self.write(dict(code=1, msg='关键参数不能为空'))

        self.write(dict(code=0, msg='删除成功'))


class SysUpdateHandler(BaseHandler):
    def get(self, *args, **kwargs):
        nickname = self.get_current_nickname()
        key = self.get_argument('key', default=None, strip=True)
        value = self.get_argument('value', default=None, strip=True)
        page_size = self.get_argument('page', default=1, strip=True)
        limit = self.get_argument('limit', default="999", strip=True)
        limit_start = (int(page_size) - 1) * int(limit)
        sys_list = []
        count = 0
        try:
            with DBContext('r') as session:
                if key == 'sys_id':
                    count = session.query(SysUpgrade).filter(SysUpgrade.sys_id == value).count()
                    all_upgrade = session.query(SysUpgrade).filter(SysUpgrade.sys_id == value).order_by(
                        SysUpgrade.id.desc())
                    sys_name = session.query(Sys.sys_name).filter(Sys.id == value).first()
                    _sn = ''
                    if sys_name:
                        _sn = sys_name[0]

                    for msg in all_upgrade:
                        data_dict = model_to_dict(msg)
                        data_dict['up_stime'] = str(data_dict['up_stime'])
                        data_dict['up_etime'] = str(data_dict['up_etime'])
                        data_dict['issued_time'] = str(data_dict['issued_time'])
                        data_dict['up_real_time'] = str(data_dict['up_real_time'])
                        data_dict['sys_name'] = _sn
                        sys_list.append(data_dict)

        except Exception as e:
            ins_log.read_log('error:', '{err}'.format(err=e))

        self.write(dict(code=0, msg='获取成功', count=count, data=sys_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        sys_id = data.get('id')
        sys_version = data.get('sys_version')
        up_stime = data.get('up_stime')
        up_etime = data.get('up_etime')
        issued_time = data.get('issued_time')
        isPilot = data.get('isPilot')
        up_content = data.get('up_content')
        pilot_unit = data.get('pilot_unit')
        up_real_time = data.get('up_real_time')
        isAffect = data.get('isAffect')

        if not sys_id:
            return self.write(dict(code=-1, msg='系统ID不能为空'))

        with DBContext('w', None, True) as session:
            new_sysUpdate = SysUpgrade(
                sys_id=sys_id, sys_version=sys_version, up_content=up_content,
                up_stime=up_stime, up_etime=up_etime, issued_time=issued_time,
                isPilot=isPilot, pilot_unit=pilot_unit, up_real_time=up_real_time,
                isAffect=isAffect,
            )
            session.add(new_sysUpdate)

            # 更新软件信息
            session.query(Sys).filter(Sys.id == int(sys_id)).update(
                {
                    Sys.sys_version: sys_version,
                })

            session.commit()

        self.write(dict(code=0, msg='添加成功'))

    def put(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        id = data.get('id')
        # sys_id = data.get('sys_id')
        sys_version = data.get('sys_version')
        up_stime = data.get('up_stime')
        up_etime = data.get('up_etime')
        issued_time = data.get('issued_time')
        isPilot = data.get('isPilot')
        up_content = data.get('up_content')
        pilot_unit = data.get('pilot_unit')
        up_real_time = data.get('up_real_time')
        isAffect = data.get('isAffect')

        if not id:
            return self.write(dict(code=-1, msg='ID不能为空'))

        with DBContext('w', None, True) as session:
            session.query(SysUpgrade).filter(SysUpgrade.id == id).update({
                SysUpgrade.sys_version: sys_version, SysUpgrade.up_stime: up_stime, SysUpgrade.up_etime: up_etime,
                SysUpgrade.issued_time: issued_time, SysUpgrade.isPilot: isPilot, SysUpgrade.up_content: up_content,
                SysUpgrade.pilot_unit: pilot_unit, SysUpgrade.up_real_time: up_real_time, SysUpgrade.isAffect: isAffect,
            }, synchronize_session=False)

            session.commit()

        self.write(dict(code=0, msg='编辑成功'))


class SysUpLoadFileHandler(BaseHandler):
    def post(self, *args, **kwargs):
        ###文件保存到本地
        Base_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        upload_path = '{}/static'.format(Base_DIR)
        file_metas = self.request.files.get('file', None)  # 提取表单中‘name’为‘file’的文件元数据
        ret = {'result': 'OK', 'msg': "上传成功", 'code': 0}
        if not file_metas:
            ret['result'] = 'Invalid Args'
            ret['msg'] = '上传失败'
            ret['code'] = 1
            ret['url'] = ''
            return ret

        for meta in file_metas:
            filename = meta['filename']
            print('filename---->', filename)
            ret['url'] = 'http://' + self.request.host + '/static/' + filename
            file_path = os.path.join(upload_path, filename)
            with open(file_path, 'wb') as up:
                up.write(meta['body'])

        self.write(json.dumps(ret))

        # self.write(dict(code=0, msg="上传成功"))


class TreeHandler(BaseHandler):
    def get(self, *args, **kwargs):
        isMonitor = self.get_argument('isMonitor', default=None)
        _tree = [{
            "expand": True,
            "title": '应用系统',
            "children": [
            ]
        }]

        with DBContext('r', None, True) as session:
            sys_tags = session.query(Sys).order_by(Sys.id).all()
            for msg in sys_tags:
                sys_dict = {}
                # sys_dict['expand'] = True
                soft_tags_count = session.query(SysSoft).filter(SysSoft.sys_id == msg.id).count()
                soft_tags = session.query(SysSoft).filter(SysSoft.sys_id == msg.id).all()
                # sys_dict['the_len'] = len(soft_tags)
                sys_dict['title'] = msg.sys_name + ' ({})'.format(soft_tags_count)
                sys_dict['tag_name'] = msg.sys_name
                sys_dict['sys_id'] = msg.id

                if isMonitor:
                    sys_dict['children'] = []
                    soft_tags_Obj = {}
                    for soft_m in soft_tags:
                        soft_type = str(soft_m.soft_type)
                        if soft_type not in soft_tags_Obj:
                            soft_tags_Obj[soft_type] = []
                        soft_tags_Obj[soft_type].append(soft_m.soft_ip)

                    # ins_log.read_log('info', soft_tags_Obj)
                    for soft_type, soft_ips in soft_tags_Obj.items():
                        soft_dict = {}
                        soft_dict['title'] = SOFT_TYPE[soft_type] + ' ({})'.format(len(soft_ips))
                        soft_dict['type'] = soft_type
                        soft_dict['children'] = []
                        for ip in soft_ips:
                            _d = {}
                            _d['title'] = ip
                            _d['type'] = soft_type
                            soft_dict['children'].append(_d)

                        sys_dict['children'].append(soft_dict)

                _tree[0]["children"].append(sys_dict)

        self.write(dict(code=0, msg='获取成功', data=_tree))


class SerHostHandler(BaseHandler):
    def get(self, *args, **kwargs):
        key = self.get_argument('key', default=None, strip=True)
        value = self.get_argument('value', default=None, strip=True)
        page_size = self.get_argument('page', default=1)
        limit = self.get_argument('limit', default="999", strip=True)
        limit_start = (int(page_size) - 1) * int(limit)
        hostIp_list = []
        try:
            with DBContext('r') as session:
                serObj = session.query(Server).all()

                for msg in serObj:
                    data_dict = {}
                    data_dict['host'] = msg.hostname
                    data_dict['ip'] = msg.ip
                    hostIp_list.append(data_dict)

        except Exception as e:
            ins_log.read_log('error:', '{err}'.format(err=e))

        self.write(dict(code=0, msg='获取成功', data=hostIp_list))


sys_urls = [
    (r"/v1/cmdb/sys/", SysHandler),
    (r"/v1/cmdb/sys_update/", SysUpdateHandler),
    (r"/v1/cmdb/sys/upload/", SysUpLoadFileHandler),
    (r"/v1/cmdb/sys_tree/", TreeHandler),
    (r"/v1/cmdb/ser_host/", SerHostHandler),
]
