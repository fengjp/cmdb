#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/6/9 15:40
# @Author  : Fengjianping
# @Role    : SoftWare Models

from sqlalchemy import Column, String, Integer, Text, DateTime, TIMESTAMP, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import class_mapper, relationship
from datetime import datetime

Base = declarative_base()


def model_to_dict(model):
    model_dict = {}
    for key, column in class_mapper(model.__class__).c.items():
        model_dict[column.name] = getattr(model, key, None)
    return model_dict


class DeviceSoft(Base):
    __tablename__ = 'asset_device_soft'

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column('device_id', Integer)
    soft_id = Column('soft_id', Integer)


class Device(Base):
    __tablename__ = 'asset_device'

    ### 设备信息
    id = Column(Integer, primary_key=True, autoincrement=True)  # ID自增长
    device_id = Column('device_id', String(50), default='')     # 设备编号
    device_sn = Column('device_sn', String(50), default='')     # 设备SN
    device_brand = Column('device_brand', String(50))              # 设备品牌
    device_type = Column('device_type', String(50))                # 设备类型
    buy_time = Column('buy_time', DateTime(), default='')       # 购买时间
    maintenance_company = Column('maintenance_company', String(50), default='')     # 维保公司
    maintenance_st = Column('maintenance_st', String(50), default='')           # 维保开始时间
    maintenance_et = Column('maintenance_et', String(50), default='')           # 维保结束时间
    device_place = Column('device_place', String(255), default='')              # 存放位置
    device_softs = Column('device_softs', String(255), default='')              # 关联软件
    device_ip = Column('device_ip', String(255), default='')                    # ip
    create_time = Column('create_time', DateTime(), default=datetime.now)       # 创建时间
    update_time = Column('update_time', DateTime(), default=datetime.now, onupdate=datetime.now)  # 记录更新时间




