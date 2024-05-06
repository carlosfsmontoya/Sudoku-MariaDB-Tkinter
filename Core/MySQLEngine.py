# -*- coding: utf-8 -*-
"""
    @author fausto.maradiaga@unah.hn
    @version 0.1.0
    @date 2021/04/25
"""

import mysql.connector
from Core.ConfigConnection import ConfigConnection

class MySQLEngine:

    def __init__(self):
        self.config = ConfigConnection()

        self.mydb = mysql.connector.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            password=self.config.password,
            database=self.config.database
        )
        self.link = self.mydb.cursor()

    def getAll(self,query):
        self.link.execute(query)
        return self.link.fetchall()

    def getOne(self,query):
        self.link.execute(query)
        return self.link.fetchone()
    
    def callSP(self, call, args):
        result = self.link.callproc(call, args)
        self.mydb.commit()
        return result

    def insertUpdateDelete(self,query):
        self.link.execute(query)
        self.mydb.commit()
    
    def closeCon(self):
        self.mydb.close()

