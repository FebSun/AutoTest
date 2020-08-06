#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2020/8/4 20:21
# @Author  : FebSun
# @FileName: test_pool.py
# @Software: PyCharm
import json

from core.resource.pool import ResourceDevice, ResourcePool

switch = ResourceDevice(name='switch1')
switch.add_port('ETH1/1')
switch.add_port('ETH1/2')

switch2 = ResourceDevice(name='switch2')
switch2.add_port('ETH1/1')
switch2.add_port('ETH1/2')

switch.ports['ETH1/1'].remote_ports.append(switch2.ports['ETH1/1'])
switch2.ports['ETH1/1'].remote_ports.append(switch.ports['ETH1/1'])

rp = ResourcePool()
rp.topology['switch1'] = switch
rp.topology['switch2'] = switch2
rp.save('test.json')
rp.load('test.json')
print('done')
print(json.dumps(switch.to_dict(), indent=4))
