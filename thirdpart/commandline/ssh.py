#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2020/8/6 19:10
# @Author  : FebSun
# @FileName: ssh.py
# @Software: PyCharm
import paramiko
from .base import CommandLine


class SshClient(CommandLine):
    def __init__(self, host, port, username, password, **kwargs):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssh = None
        self.session = None

    def connect(self):
        if self.ssh is None:
            try:
                self.ssh = paramiko.SSHClient()
                self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh.connect(self.host, self.port, self.username, self.password)
                trans = self.ssh.get_transport()
                # self.session = trans.o
            except:
                pass
