#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/6/8 10:40
# @Author  : Fengjianping
# @Role    : SoftWare Models

from sqlalchemy import Column, String, Integer, Text, DateTime, TIMESTAMP, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import class_mapper, relationship
from datetime import datetime

Base = declarative_base()

soft_type_dict = {
    1: '操作系统',
    2: '虚拟化',
    3: '数据库',
    4: '服务',
    5: '中间件',
    6: '应用服务',
    7: 'Web服务',
    8: '其他',
}


def model_to_dict(model):
    model_dict = {}
    for key, column in class_mapper(model.__class__).c.items():
        model_dict[column.name] = getattr(model, key, None)
    return model_dict


class Soft(Base):
    __tablename__ = 'asset_soft'

    id = Column(Integer, primary_key=True, autoincrement=True)
    soft_name = Column('soft_name', String(255))  # 软件名称
    soft_type = Column('soft_type', Integer)  # 类型
