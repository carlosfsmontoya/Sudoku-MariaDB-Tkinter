#-*-coding: utf-8-*-
"""
    @author fausto.maradiaga@unah.hn
    @version 0.1.0
    @date 2021/04/16
"""

from configparser import ConfigParser

class ConfigConnection:
    def __init__(self):
        conf = ConfigParser()
        conf.read('Core/config.ini') 
        self.host = conf.get('dbinfo','host')
        self.port = conf.get('dbinfo','port')
        self.user = conf.get('dbinfo','user')
        self.password = conf.get('dbinfo','password')
        self.database = conf.get('dbinfo','database')