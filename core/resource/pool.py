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


class PhoneMustBeAndroidConstraint(Constraint):
    """
    判断手机的操作系统是否是 Android，可以附带版本大小判断
    """

    def __init__(self, version_op=None, version=None):
        super().__init__()
        self.version = version
        self.version_op = version_op
        if self.version_op is not None:
            self.description = f"Phone Type must be Android and version {self.version_op}{self.version}"
        else:
            self.description = f"Phone Type must be Android"

    def is_meet(self, resource, *args, **kwargs):
        # 首先判断资源类型是否是 ResourceType，type 的值是否是 Android
        if isinstance(resource, ResourceDevice) and resource.type == 'Android':
            if self.version_op:
                # 判断资源是否有 version 字段和值
                device_version = getattr(resource, 'version')
                if device_version is None:
                    return False
                if self.version_op == '=':
                    return device_version == self.version
                elif self.version_op == '>':
                    return device_version > self.version
                elif self.version_op == '<':
                    return device_version < self.version
                elif self.version_op == '>=':
                    return device_version >= self.version
                elif self.version_op == '<=':
                    return device_version <= self.version
                elif self.version_op == '!=':
                    return device_version != self.version
                else:
                    return False
            else:
                # 没有版本判断操作符，说明资源满足条件
                return True
        return False


class ApMustHaveStaConnected(ConnectionConstraint):
    """
    判断 AP 是否有 STA 连接
    """

    def __init__(self, sta_constraints=list(), sta_count=1):
        super().__init__()
        # constraint 分类
        self.sta_constraints = list()
        self.sta_conn_constraints = list()
        for sta_constraint in sta_constraints:
            if isinstance(sta_constraint, ConnectionConstraint):
                self.sta_conn_constraints.append(sta_constraint)
            else:
                self.sta_constraints.append(sta_constraint)
        self.sta_count = sta_count
        self.description = f"AP Must have {sta_count} STA Connected"
        for sta_constraint in self.sta_constraints:
            self.description += f"\n{sta_constraint.description}"

    def is_meet(self, resource, *args, **kwargs):
        return any(self.get_connection(resource))

    def get_connection(self, resource, *args, **kwargs):
        if not isinstance(resource, ResourceDevice) or resource.type != 'AP':
            return False
        for port_key, port in resource.ports.items():
            if port.type != 'WIFI':
                continue
            ret = list()
            for remote_port in port.remote_ports:
                if remote_port.parent.type == 'STA':
                    # 用 STA Constraint 判断远端端口的 STA 设备是否符合条件
                    meet_all = True
                    for sta_constraint in self.sta_constraints:
                        if not sta_constraint.is_meet(remote_port.parent):
                            meet_all = False
                            break
                    # 如果没有满足基本的限制条件，就不再测试 connection 的限制条件
                    if not meet_all:
                        continue
                    # 根据 connection 的限制条件，返回对端口的所有端口
                    conn_remote = list()
                    meet_connection = True
                    for sta_conn_constraint in self.sta_conn_constraints:
                        conns = sta_conn_constraint.get_connection(remote_port.parent)
                        # 不满足 Connection 的限制条件
                        if not any(conns):
                            meet_connection = False
                            break
                        for conn in conns:
                            conn_remote.append(conn)

                    if not meet_connection:
                        continue

                    ret.append((remote_port, conn_remote))
            if len(ret) >= self.sta_count:
                return ret[0:self.sta_count]
        return list()


class DeviceMustHaveTrafficGeneratorConnected(ConnectionConstraint):
    """
    判断 AP 是否有测试仪表连接
    """

    def __init__(self, speed_consrtaint=None, port_count=None):
        super().__init__()
        self.speed = speed_consrtaint
        self.port_count = port_count
        self.description = "AP Must have Traffic Generator Connected"
        if speed_consrtaint:
            self.description += f", {speed_consrtaint.description}"
        if port_count:
            self.description += f", Port Count at least {port_count}"

    def is_meet(self, resource, *args, **kwargs):
        return any(self.get_connection(resource))

    def get_connection(self, resource, *args, **kwargs):
        if not isinstance(resource, ResourceDevice):
            return False
        meet_port = list()
        for port_key, port in resource.ports.items():
            # 假设测试仪表端口连在 ETH 端口上，跳过非 ETH 端口的判断
            if port.type != 'ETH':
                continue
            # 遍历 remote_ports
            for remote_port in port.remote_ports:
                if remote_port.parent.type == 'TrafficGen':
                    # 如果端口速率有限制，则调用该限制实例
                    if self.speed:
                        if self.speed.is_meet(remote_port):
                            meet_port.append(remote_port)
                    else:
                        meet_port.append(remote_port)
        if self.port_count:
            if len(meet_port) > self.port_count:
                return meet_port[0, self.port_count]
        else:
            if len(meet_port) > 0:
                return meet_port[0:1]
        return list()


class TrafficGeneratorSpeedMustGreaterThen(Constraint):
    """
    判断测试仪表端口速率是否大于给定速度
    """

    def __init__(self, speed):
        super().__init__()
        self.speed = speed
        self.description = f"Traffic Generator Port Speed Must Greater Then {speed}M"

    def is_meet(self, resource, *args, **kwargs):
        if not isinstance(resource, DevicePort) or resource.parent.type != 'TrafficGen':
            return False
        return getattr(resource, 'speed', None) is not None and getattr(resource, 'speed') >= self.speed

