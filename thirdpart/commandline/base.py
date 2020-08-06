#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2020/8/6 19:09
# @Author  : FebSun
# @FileName: base.py
# @Software: PyCharm

from abc import ABCMeta, abstractmethod


class CommandLine(metaclass=ABCMeta):

    @abstractmethod
    def send(self, string):
        pass

    @abstractmethod
    def send_and_wait(self, string, wait_for, timeout=60, **kwargs):
        pass

    @abstractmethod
    def receive(self):
        pass

    @abstractmethod
    def send_binary(self, binary):
        pass

    @abstractmethod
    def receive_binary(self):
        pass

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def _login(self):
        pass
