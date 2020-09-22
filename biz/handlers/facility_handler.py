#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File    : facility_handler.py
# @Role    : 设备管理


import json
from libs.base_handler import BaseHandler
from models.server import Facility, model_to_dict
from websdk.db_context import DBContext
from libs.aes_coder import encrypt, decrypt


class FacilityHandler(BaseHandler):
    def get(self, *args, **kwargs):
        key = self.get_argument('key', default=None, strip=True)
        value = self.get_argument('value', default=None, strip=True)
        page_size = self.get_argument('page', default=1, strip=True)
        limit = self.get_argument('limit', default=15, strip=True)
        limit_start = (int(page_size) - 1) * int(limit)
        facility_list = []
        with DBContext('w') as session:
            if key and value:
                count = session.query(Facility).filter_by(**{key: value}).count()
                facility_data = session.query(Facility).filter_by(**{key: value}).order_by(
                    Facility.id).offset(limit_start).limit(int(limit))
            else:
                count = session.query(Facility).count()
                facility_data = session.query(Facility).order_by(Facility.id).offset(
                    limit_start).limit(int(limit))

        for data in facility_data:
            data_dict = model_to_dict(data)
            data_dict['create_time'] = str(data_dict['create_time'])
            facility_list.append(data_dict)

        return self.write(dict(code=0, msg='获取成功', count=count, data=facility_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        facility_na = data.get('facility_na', '')
        facility_id = data.get('facility_id', '')
        facility_sn = data.get('facility_sn', '')
        facility_ip = data.get('facility_ip', '')
        remarks = data.get('remarks', '')

        if not facility_na:
            return self.write(dict(code=-2, msg='名称不能为空'))

        with DBContext('r') as session:
            exist_id = session.query(Facility.id).filter(Facility.facility_na == facility_na).first()

        if exist_id:
            return self.write(dict(code=-2, msg='不要重复记录'))

        with DBContext('w', None, True) as session:
            new_facility = Facility(facility_na=facility_na, facility_id=facility_id, facility_sn=facility_sn,
                                    facility_ip=facility_ip, remarks=remarks)
            session.add(new_facility)
        return self.write(dict(code=0, msg='添加成功'))

    def put(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        id = data.get('id')
        facility_na = data.get('facility_na', '')
        facility_id = data.get('facility_id', '')
        facility_sn = data.get('facility_sn', '')
        facility_ip = data.get('facility_ip', '')
        remarks = data.get('remarks', '')

        if not facility_na:
            return self.write(dict(code=-2, msg='名称不能为空'))

        update_info = {
            "facility_na": facility_na,
            "facility_id": facility_id,
            "facility_sn": facility_sn,
            "facility_ip": facility_ip,
            "remarks": remarks,
        }

        with DBContext('w', None, True) as session:
            session.query(Facility).filter(Facility.id == id).update(update_info)
        self.write(dict(code=0, msg='更新成功'))

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        id = data.get('id')
        if not id:
            return self.write(dict(code=-2, msg='关键参数不能为空'))

        with DBContext('w', None, True) as session:
            session.query(Facility).filter(Facility.id == id).delete(synchronize_session=False)

        self.write(dict(code=0, msg='删除成功'))


facility_urls = [
    (r"/v1/cmdb/facility/", FacilityHandler)
]
