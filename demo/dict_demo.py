#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2020/8/4 19:43
# @Author  : FebSun
# @FileName: dict_demo.py
# @Software: PyCharm


class TestClass:
    def __init__(self):
        self.field1 = 'value1'
        self.field2 = 123
        self.field3 = True

print(TestClass().__dict__)
