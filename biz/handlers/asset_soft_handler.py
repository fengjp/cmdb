#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/6/8 10:14
# @Author  : Fengjianping
# @Role    : Soft


import json
from libs.base_handler import BaseHandler
from sqlalchemy import or_, and_
from models.software import Soft, model_to_dict, soft_type_dict
from models.device import Device, DeviceSoft
from websdk.db_context import DBContext
from websdk.web_logs import ins_log


class SoftHandler(BaseHandler):
    def get(self, *args, **kwargs):
        nickname = self.get_current_nickname()
        key = self.get_argument('key', default=None, strip=True)
        value = self.get_argument('value', default=None, strip=True)
        page_size = self.get_argument('page', default=1, strip=True)
        limit = self.get_argument('limit', default="999", strip=True)
        limit_start = (int(page_size) - 1) * int(limit)
        soft_obj = {
            1: [],
            2: [],
            3: [],
            4: [],
            5: [],
            6: [],
            7: [],
            8: [],
        }

        with DBContext('r') as session:
            count = session.query(Soft).count()
            all_softs = session.query(Soft).all()
            for msg in all_softs:
                data_dict = model_to_dict(msg)
                soft_obj[data_dict['soft_type']].append(data_dict)

        self.write(dict(code=0, msg='获取成功', count=count, data=soft_obj))

    def post(self, *args, **kwargs):
        soft_list = json.loads(self.request.body.decode("utf-8"))
        # soft_list = data.get('soft_list')
        soft_type = soft_list[0].get('soft_type', 0)

        if soft_type:
            with DBContext('w', None, True) as session:
                session.query(Soft).filter(Soft.soft_type == soft_type).delete(synchronize_session=False)
                session.commit()

        else:
            return self.write(dict(code=1, msg='类型不能为空'))

        with DBContext('w', None, True) as session:
            for soft in soft_list:
                soft_name = soft['soft_name']
                soft_type = soft['soft_type']

                if not soft_name:
                    continue

                new_soft = Soft(
                    soft_name=soft_name, soft_type=soft_type,
                )
                session.add(new_soft)
            session.commit()

        self.write(dict(code=0, msg='添加成功'))

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        id = data.get('id')

        with DBContext('w', None, True) as session:
            if id:
                session.query(Soft).filter(Soft.id == id).delete(synchronize_session=False)

            else:
                return self.write(dict(code=1, msg='关键参数不能为空'))

        self.write(dict(code=0, msg='删除成功'))


class SoftTypeHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.write(dict(code=0, msg='获取成功', count=len(soft_type_dict), data=soft_type_dict))


soft_urls = [
    (r"/v1/cmdb/soft/", SoftHandler),
    (r"/v1/cmdb/soft_type/", SoftTypeHandler),
]
