#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2020/8/4 20:05
# @Author  : FebSun
# @FileName: dict_demo3.py
# @Software: PyCharm

import json


class TestClass1:
    def __init__(self):
        self.field1 = 'value1'
        self.field2 = 123
        self.field3 = True
        self.field4 = None


class TestClass2:
    def __init__(self):
        self.field1 = 'value1'
        self.field2 = 123
        self.field3 = True
        self.field4 = None


test1 = TestClass1()
test2 = TestClass2()
test1.field4 = test2
test2.field4 = test1

# print(TestClass1().__dict__)
print(json.dumps(test1, default=lambda o: o.__dict__))