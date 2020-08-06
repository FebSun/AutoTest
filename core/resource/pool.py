#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2020/8/4 19:16
# @Author  : FebSun
# @FileName: pool.py
# @Software: PyCharm
import json
import os
from datetime import datetime
from abc import ABCMeta, abstractmethod
from core.resource.error import ResourceNotMeetConstraintError

_resource_device_mapping = dict()
_resource_port_mapping = dict()


def register_resource(category, resource_type, comm_callback):
    """
    注册配置接口实例化的方法或类
    """
    if category == 'device':
        _resource_device_mapping[resource_type] = comm_callback
    elif category == 'port':
        _resource_port_mapping[resource_type] = comm_callback


class ResourceError(Exception):
    def __init__(self, ErrorInfo):
        super().__init__(self)
        self.error_info = ErrorInfo

    def __str__(self):
        return self.error_info


class ResourceDevice:
    """
    代表所有测试资源设备的配置类，字段动态定义
    """

    def __init__(self, name='', *args, **kwargs):
        self.name = name
        self.type = kwargs.get('type', None)
        self.description = kwargs.get('description', None)
        self.ports = dict()

    def add_port(self, name, *args, **kwargs):
        if name in self.ports:
            raise ResourceError(f"Port Name {name} already exists")
        self.ports[f"{name}"] = DevicePort(self, name, *args, **kwargs)

    def to_dict(self):
        ret = dict()
        for key, value in self.__dict__.items():
            if key == 'ports':
                ret[key] = dict()
                for port_name, port in value.items():
                    ret[key][port_name] = port.to_dict()
            else:
                ret[key] = value
        return ret

    @staticmethod
    def from_dict(dict_obj):
        ret = ResourceDevice()
        for key, value in dict_obj.items():
            if key == 'ports':
                ports = dict()
                for port_name, port in value.items():
                    ports[port_name] = DevicePort.from_dict(port, ret)
                setattr(ret, 'ports', ports)
            else:
                setattr(ret, key, value)
        return ret

    def get_comm_instance(self):
        if self.type not in _resource_device_mapping:
            raise ResourceError(f"type {self.type} is not registered")
        return _resource_device_mapping[self.type](self)


class DevicePort:
    """
    代表设备的连接端口
    """

    def __init__(self, parent_device=None, name='', *args, **kwargs):
        self.parent = parent_device
        self.type = kwargs.get('type', None)
        self.name = name
        self.description = kwargs.get('description', None)
        self.remote_ports = list()

    def to_dict(self):
        ret = dict()
        for key, value in self.__dict__.items():
            if key == 'parent':
                ret[key] = value.name
            elif key == 'remote_ports':
                ret[key] = list()
                for remote_port in value:
                    # 使用 device 的名称和 port 的名称来表示远端的端口
                    # 在反序列化的时候可以方便地找到相应的对象名称
                    ret[key].append(
                        {
                            "device": remote_port.parent.name,
                            "port": remote_port.name
                        }
                    )
            else:
                ret[key] = value
        return ret

    @staticmethod
    def from_dict(dict_obj, parent):
        ret = DevicePort(parent)
        for key, value in dict_obj.items():
            if key == 'remote_ports' or key == 'parent':
                continue
            setattr(ret, key, value)
        return ret

    def get_comm_instance(self):
        if self.type not in _resource_port_mapping:
            raise ResourceError(f"type {self.type} is not registered")
        return _resource_port_mapping[self.type](self)


class ResourcePool:
    """
    资源池类，负责资源的序列化和反序列化，以及存储和读取
    """

    def __init__(self):
        self.reserved = None
        self.topology = dict()
        self.information = dict()
        self.file_name = None
        self.owner = None

    def add_device(self, device_name, **kwargs):
        if device_name in self.topology:
            raise ResourceError(f"device {device_name} already exists")
        self.topology[device_name] = ResourceDevice(device_name)

    def reserve(self):
        if self.file_name is None:
            raise ResourceError('load a resource file first')
        self.load(self.file_name, self.owner)
        self.reserved = {
            "owner": self.owner,
            "date": datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S')
        }
        self.save(self.file_name)

    def release(self):
        if self.file_name is None:
            raise ResourceError('load a resource file first')
        self.load(self.file_name)
        self.reserved = None
        self.save(self.file_name)

    def load(self, filename, owner):
        if not os.path.exists(filename):
            raise ResourceError(f"Cannot find file {filename}")
        self.file_name = filename
        # 初始化
        self.topology.clear()
        # self.reserved = False
        self.information = dict()

        # 读取资源配置的 JSON 字符串
        with open(filename) as file:
            json_object = json.load(file)
            if 'reserved' in json_object and json_object['reserved']['owner'] != owner:
                raise ResourceError(f"Resource is reserved by {json_object['reserved']['owner']}")
            self.owner = owner
        if 'info' in json_object:
            self.information = json_object['info']
        for key, value in json_object['devices'].items():
            device = ResourceDevice.from_dict(value)
            self.topology[key] = device

        # 映射所有设备的连接关系
        for key, device in json_object['devices'].items():
            for port_name, port in device['ports'].items():
                for remote_port in port['remote_ports']:
                    remote_port_obj = self.topology[remote_port['device']].ports[remote_port['port']]
                    self.topology[key].ports[port_name].remote_ports.append(remote_port_obj)

    def save(self, filename):
        with open(filename, mode='w') as file:
            root_object = dict()
            root_object['devices'] = dict()
            root_object['info'] = self.information
            root_object['reserved'] = self.reserved
            for device_key, device in self.topology.items():
                root_object['devices'][device_key] = device.to_dict()
            json.dump(root_object, file, indent=4)

    def collect_device(self, device_type, count, constraints=list()):
        ret = list()
        for key, value in self.topology.items():
            if value.type == device_type:
                for constraint in constraints:
                    if not constraint.is_meet(value):
                        break
                    else:
                        ret.append(value)
            if len(ret) >= count:
                return ret
        else:
            return list()

    def collect_all_device(self, device_type, constraints=list()):
        ret = list()
        for key, value in self.topology.items():
            if value.type == device_type:
                for constraint in constraints:
                    if not constraint.is_meet(value):
                        break
                    else:
                        ret.append(value)
        return ret

    def collect_connection_route(self, resource, constraints=list()):
        """
        获取资源连接路由
        """
        # 限制类必须是连接限制 ConnectionConstraint
        for constraint in constraints:
            if not isinstance(constraint, ConnectionConstraint):
                raise ResourceError("collect_connection_route only accept ConnectionConstraints type")
        ret = list()
        for constraint in constraints:
            conns = constraint.get_connection(resource)
            if not any(conns):
                raise ResourceNotMeetConstraintError([constraint])
            for conn in conns:
                ret.append(conn)
        return ret


class Constraint(metaclass=ABCMeta):
    """
    资源选择器限制条件的基类
    """

    def __init__(self):
        self.description = None

    @abstractmethod
    def is_meet(self, resource, *args, **kwargs):
        pass


class ConnectionConstraint(Constraint, metaclass=ABCMeta):
    """
    用户获取 remote_port 的限制条件
    """

    @abstractmethod
    def get_connection(self, resource, *args, **kwargs):
        pass
