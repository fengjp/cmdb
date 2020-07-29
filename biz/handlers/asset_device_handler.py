#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/6/8 10:14
# @Author  : Fengjianping
# @Role    : Device
from datetime import datetime
import json
from libs.base_handler import BaseHandler
from sqlalchemy import or_
from models.software import Soft
from models.device import model_to_dict, Device, DeviceSoft
from websdk.db_context import DBContext
from websdk.web_logs import ins_log


class DeviceHandler(BaseHandler):
    def get(self, *args, **kwargs):
        nickname = self.get_current_nickname()
        key = self.get_argument('key', default=None, strip=True)
        value = self.get_argument('value', default=None, strip=True)
        page_size = self.get_argument('page', default=1, strip=True)
        limit = self.get_argument('limit', default="999", strip=True)
        limit_start = (int(page_size) - 1) * int(limit)

        device_list = []
        with DBContext('r') as session:
            if limit == "999":
                ### 查看所有
                count = session.query().count()
                device_info = session.query(Device).order_by(Device.id).all()
            else:
                ## 正常分页搜索
                if key and value:
                    count = session.query(Device).filter_by(**{key: value}).count()
                    device_info = session.query(Device).filter_by(**{key: value}).order_by(Device.id).offset(
                        limit_start).limit(int(limit))
                else:
                    count = session.query(Device).count()
                    device_info = session.query(Device).order_by(Device.id).offset(limit_start).limit(int(limit))

            for msg in device_info:
                soft_list = []
                data_dict = model_to_dict(msg)
                device_softs = session.query(Soft.soft_name).outerjoin(DeviceSoft,
                                                                       Soft.id == DeviceSoft.soft_id).filter(
                    DeviceSoft.device_id == data_dict['id']).all()
                for d in device_softs:
                    soft_list.append(d[0])
                data_dict['create_time'] = str(data_dict['create_time'])
                data_dict['update_time'] = str(data_dict['update_time'])
                data_dict['buy_time'] = str(data_dict['buy_time'])
                data_dict['maintenance_st'] = str(data_dict['maintenance_st'])
                data_dict['maintenance_et'] = str(data_dict['maintenance_et'])
                data_dict['soft_list'] = soft_list
                device_list.append(data_dict)

        self.write(dict(code=0, msg='获取成功', count=count, data=device_list))

    def post(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        nickname = self.get_current_nickname()
        ip = data.get('ip', None)
        buy_time = data.get('buy_time', '')
        device_brand = data.get('device_brand', '')
        device_id = data.get('idc', '')
        device_ip = data.get('device_ip', '')
        device_place = data.get('device_place', '')
        device_sn = data.get('device_sn', '')
        device_softs = data.get('device_softs', '')
        device_type = data.get('device_type', '')
        maintenance_company = data.get('maintenance_company', '')
        maintenance_et = data.get('maintenance_et', '')
        maintenance_st = data.get('maintenance_st', '')

        # if not hostname or not ip or not port:
        #     return self.write(dict(code=-1, msg='关键参数不能为空'))
        #
        # if not check_ip(ip):
        #     return self.write(dict(code=-1, msg="IP格式不正确"))

        with DBContext('r') as session:
            exist_id = session.query(Device.id).filter(Device.device_id == device_id).first()
            exist_sn = session.query(Device.id).filter(Device.device_sn == device_sn).first()

        if exist_id or exist_sn:
            return self.write(dict(code=-2, msg='不要重复记录'))

        with DBContext('w', None, True) as session:
            new_device = Device(buy_time=datetime.now(), device_brand=device_brand, device_id=device_id, device_ip=device_ip,
                                device_place=device_place, device_sn=device_sn,
                                device_type=device_type, maintenance_company=maintenance_company,
                                maintenance_et=datetime.now(), maintenance_st=datetime.now())
            session.add(new_device)

            all_soft = session.query(Soft.id).filter(Soft.soft_name.in_(device_softs)).order_by(Soft.id).all()
            # print('all_tags', all_tags)
            if all_soft:
                for soft_id in all_soft:
                    session.add(DeviceSoft(device_id=new_device.id, soft_id=soft_id[0]))
            session.commit()

        return self.write(dict(code=0, msg='添加成功'))

    def delete(self, *args, **kwargs):
        data = json.loads(self.request.body.decode("utf-8"))
        id = data.get('id')

        with DBContext('w', None, True) as session:
            if id:
                session.query(Soft).filter(Soft.id == id).delete(synchronize_session=False)

            else:
                return self.write(dict(code=1, msg='关键参数不能为空'))

        self.write(dict(code=0, msg='删除成功'))


dev_urls = [
    (r"/v1/cmdb/dev/", DeviceHandler),
]
