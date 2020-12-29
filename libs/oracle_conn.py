#!/usr/bin/env python
# -*-coding:utf-8-*-
'''
role   : oracle操作
'''

import cx_Oracle
import logging

logger = logging.getLogger("Oracle")


class OracleBase:
    def __init__(self, **args):
        self.host = args.get('host')
        self.user = args.get('user')
        self.pswd = args.get('passwd')
        self.db = args.get('db', 'orcl')
        self.port = int(args.get('port', 1521))
        self.charset = args.get('charset', 'utf8')

        try:
            uri = '{0}/{1}@{2}:{3}/{4}'.format(self.user, self.pswd, self.host, self.port, self.db)
            self.conn = cx_Oracle.connect(uri)
            self.cur = self.conn.cursor()
        except:
            raise ValueError('Oracle connect error {0}'.format(self.host))

    ###释放资源
    def __del__(self):
        self.cur.close()
        self.conn.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cur.close()
        self.conn.close()

    ### 查询
    def query(self, sql):
        try:
            self.cur.execute(sql)  # 执行sql语句
            res = self.cur.fetchall()  # 获取查询的所有记录
        except Exception as e:
            logger.error(["execute sql err...", sql])
            raise e

        return res

    def change(self, sql):
        resnum = 0
        try:
            resnum = self.cur.execute(sql)
            # 提交
            self.conn.commit()
        except Exception as e:
            # 错误回滚
            logger.error(["execute sql err...", sql])
            self.conn.rollback()
        return resnum

    ### 测试连接
    def test(self):
        try:
            self.conn.ping()
            return True
        except:
            return False


if __name__ == '__main__':
    pass


