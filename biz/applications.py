#!/usr/bin/env python
# -*-coding:utf-8-*-
"""
"""

from websdk.application import Application as myApplication
from biz.handlers.asset_server_handler import asset_server_urls
from biz.handlers.asset_db_handler import asset_db_urls
from biz.handlers.admin_user_handler import admin_user_urls
from biz.handlers.asset_tag_handler import tag_urls
# from biz.handlers.system_user_handler import system_user_urls
# from biz.handlers.asset_configs_handler import asset_configs_urls
from biz.handlers.hand_update_asset_handler import asset_hand_server_urls
# from biz.handlers.aws_events_handler import aws_events_urls
# from biz.handlers.asset_idc_handler import asset_idc_urls
from biz.handlers.asset_operational_audit_handler import asset_audit_urls
from biz.handlers.asset_soft_handler import soft_urls
from biz.handlers.asset_sys_handler import sys_urls
from biz.handlers.assetSql import assetSql_urls
from biz.handlers.facility_handler import facility_urls


class Application(myApplication):
    def __init__(self, **settings):
        urls = []
        urls.extend(asset_server_urls)
        urls.extend(asset_db_urls)
        urls.extend(admin_user_urls)
        urls.extend(tag_urls)
        # urls.extend(system_user_urls)
        # urls.extend(asset_configs_urls)
        urls.extend(asset_hand_server_urls)
        # urls.extend(aws_events_urls)
        # urls.extend(asset_idc_urls)
        urls.extend(asset_audit_urls)
        urls.extend(soft_urls)
        urls.extend(sys_urls)
        urls.extend(assetSql_urls)
        urls.extend(facility_urls)
        super(Application, self).__init__(urls, **settings)


if __name__ == '__main__':
    pass
