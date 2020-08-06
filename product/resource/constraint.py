#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2020/8/6 19:02
# @Author  : FebSun
# @FileName: constraint.py
# @Software: PyCharm
from core.resource.pool import Constraint, ConnectionConstraint, DevicePort, ResourceDevice


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
