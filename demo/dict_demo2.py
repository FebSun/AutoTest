#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2020/8/4 19:50
# @Author  : FebSun
# @FileName: dict_demo2.py
# @Software: PyCharm
import json


class TestClass1:
    def __init__(self):
        self.field1 = 'value1'
        self.field2 = 123
        self.field3 = True
        self.field4 = TestClass2()


class TestClass2:
    def __init__(self):
        self.field1 = 'value1'
        self.field2 = 123
        self.field3 = True


# print(TestClass1().__dict__)
print(json.dumps(TestClass1(), default=lambda o: o.__dict__))