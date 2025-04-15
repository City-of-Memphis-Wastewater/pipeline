'''
Title: eds_point
Author: George Clayton Bennett
'''
from collections import deque
class Point:
    point_dict = dict()
    point_set = set()
    max_history = 1000
    @classmethod
    def register_point_to_class_dict(cls,self):
        cls.point_dict.update({self.sid:self})
    @classmethod
    def register_point_to_class_set(cls,self):
        cls.point_set.add(self)
    @classmethod
    def get_point_dict(cls):
        return cls.point_dict
    @classmethod
    def get_point_set(cls):
        return cls.point_set
    @classmethod
    def alter_max_history(cls,value):
        cls.max_history = value
    def __init__(self):
        self.ip_address = str()
        self.idcs = str()
        self.sid = int()
        self.zd = int()
        self.unit = str()
        self.live_value = float()
        self.live_timestamp = None
        self.history = deque(maxlen=self.max_history)
        self.rjn_siteid = str()
        self.rjn_entityid = str()
        self.rjn_name= str()
        self.register_point_to_class_set(self)
    def populate_eds_characteristics(self,ip_address,idcs,sid,zd):
        self.ip_address = ip_address
        self.idcs = idcs
        self.sid = sid
        self.zd = zd
        return self # big money, allows fore chaining
    def populate_rjn_characteristics(self,rjn_siteid,rjn_entityid,rjn_name):
        self.rjn_siteid = rjn_siteid
        self.rjn_entityid = rjn_entityid
        self.rjn_name= rjn_name
        return self # big money, allows fore chaining
    def set_value(self,value = float(), timestamp = int()):
        self.value = value
        self.timestamp = timestamp
        self.add_value_to_value_dict()
