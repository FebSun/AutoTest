#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2020/8/6 18:42
# @Author  : FebSun
# @FileName: error.py
# @Software: PyCharm


class ResourceNotMeetConstraintError(Exception):
    def __init__(self, constraint):
        super().__init__(constraint.get_description())
