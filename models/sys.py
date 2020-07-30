#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/6/8 10:40
# @Author  : Fengjianping
# @Role    : sys Models

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


class Sys(Base):
    __tablename__ = 'asset_sys'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sys_name = Column('sys_name', String(50))  # 系统名称
    sys_version = Column('sys_version', String(50))  # 版本号
    # sys_manager_phone = Column('sys_manager_phone', String(50))  # 系统负责人电话
    # sys_manager = Column('sys_manager', String(50))  # 系统负责人
    sys_info = Column('sys_info', String(512))  # 系统简介
    online_time = Column('online_time', DateTime())  # 上线时间
    development_phone = Column('development_phone', String(50))  # 开发单位电话
    development_contact = Column('development_contact', String(50))  # 开发单位联系人
    development = Column('development', String(50))  # 开发单位
    uploadList = Column('uploadList', Text)  # 附件


class SysSoft(Base):
    __tablename__ = 'asset_sys_soft'

    id = Column(Integer, primary_key=True, autoincrement=True)
    soft_name = Column('soft_name', String(50))  # 软件名称
    soft_type = Column('soft_type', Integer)  # 软件类型
    soft_version = Column('soft_version', String(50))  # 版本号
    soft_ip = Column('soft_ip', String(50))  # IP
    soft_hostname = Column('soft_hostname', String(50))  # 主机名
    soft_usage = Column('soft_usage', String(50))  # 用途
    sys_id = Column('sys_id', Integer, index=True)  # 关联的系统ID


class SysManager(Base):
    __tablename__ = 'asset_sys_manager'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sys_manager_name = Column('sys_manager_name', String(50))  # 系统负责人
    sys_manager_phone = Column('sys_manager_phone', String(50))  # 系统负责人电话
    sys_manager_role = Column('sys_manager_role', String(50))  # 角色
    sys_id = Column('sys_id', Integer, index=True)  # 关联的系统ID


class SysUpgrade(Base):
    __tablename__ = 'asset_sys_upgrade'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sys_version = Column('sys_version', String(50))  # 版本号
    up_content = Column('up_content', String(512))  # 升级内容
    up_stime = Column('up_stime', DateTime())  # 升级开始时间
    up_etime = Column('up_etime', DateTime())  # 升级结束时间
    issued_time = Column('issued_time', DateTime())  # 下发时间
    isPilot = Column('isPilot', String(50))  # 是否试点
    pilot_unit = Column('pilot_unit', String(50))  # 试点单位
    up_real_time = Column('up_real_time', String(50))  # 升级实际完成时间
    isAffect = Column('isAffect', String(50))  # 是否影响业务
    sys_id = Column('sys_id', Integer, index=True)  # 关联的系统ID
