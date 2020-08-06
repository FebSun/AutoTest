from core.resource.pool import *

ap1 = ResourceDevice(name='ap1', type='AP')
ap1.add_port('ETH1/1', type='ETH')
ap1.add_port('ETH1/2', type='ETH')
ap1.add_port('WIFI', type='WIFI')

sta1 = ResourceDevice(name='sta1', type='STA')
sta1.add_port('WIFI', type='WIFI')
sta1.add_port('ETH1/1', type='ETH')
sta1.add_port('ETH1/2', type='ETH')

sta2 = ResourceDevice(name='sta2', type='STA')
sta2.add_port('WIFI', type='WIFI')
sta2.add_port('ETH1/1', type='ETH')
sta2.add_port('ETH1/2', type='ETH')

sta3 = ResourceDevice(name='sta3', type='STA')
sta3.add_port('WIFI', type='WIFI')
sta3.add_port('ETH1/1', type='ETH')
sta3.add_port('ETH1/2', type='ETH')

traffic_gen = ResourceDevice(name='trafficGen', type='TrafficGen')
traffic_gen.add_port('PORT1/1/1', type='ETH')
setattr(traffic_gen.ports['PORT1/1/1'], 'speed', 1000)
traffic_gen.add_port('PORT1/1/2', type='ETH')
setattr(traffic_gen.ports['PORT1/1/2'], 'speed', 1000)
traffic_gen.add_port('PORT1/1/3', type='ETH')
setattr(traffic_gen.ports['PORT1/1/3'], 'speed', 1000)
traffic_gen.add_port('PORT1/1/4', type='ETH')
setattr(traffic_gen.ports['PORT1/1/4'], 'speed', 1000)

# 建立 AP 和 TrafficGen 之间的连接
ap1.ports['ETH1/1'].remote_ports.append(traffic_gen.ports['PORT1/1/1'])
traffic_gen.ports['PORT1/1/1'].remote_ports.append(ap1.ports['ETH1/1'])

# 建立 AP 和 STA 之间的连接
ap1.ports['WIFI'].remote_ports.append(sta1.ports['WIFI'])
sta1.ports['WIFI'].remote_ports.append(ap1.ports['WIFI'])

ap1.ports['WIFI'].remote_ports.append(sta2.ports['WIFI'])
sta2.ports['WIFI'].remote_ports.append(ap1.ports['WIFI'])

ap1.ports['WIFI'].remote_ports.append(sta3.ports['WIFI'])
sta3.ports['WIFI'].remote_ports.append(ap1.ports['WIFI'])

# 建立 TrafficGen 和 STA 之间的连接
sta1.ports['ETH1/1'].remote_ports.append(traffic_gen.ports['PORT1/1/2'])
traffic_gen.ports['PORT1/1/2'].remote_ports.append(sta1.ports['ETH1/1'])

sta2.ports['ETH1/1'].remote_ports.append(traffic_gen.ports['PORT1/1/3'])
traffic_gen.ports['PORT1/1/3'].remote_ports.append(sta2.ports['ETH1/1'])

sta3.ports['ETH1/1'].remote_ports.append(traffic_gen.ports['PORT1/1/4'])
traffic_gen.ports['PORT1/1/4'].remote_ports.append(sta3.ports['ETH1/1'])

# AP 必须有 STA 连接
constraint1 = ApMustHaveStaConnected()

# AP 至少有3个STA连接
constraint2 = ApMustHaveStaConnected(sta_count=3)

# AP 至少有4个STA连接
constraint3 = ApMustHaveStaConnected(sta_count=4)

# 设备必须有速率为 1000 Mbit/s的测试仪表端口连接
constraint4 = DeviceMustHaveTrafficGeneratorConnected(
    speed_consrtaint=TrafficGeneratorSpeedMustGreaterThen(1000))

# 设备必须有速率为 10000 Mbit/s的测试仪表端口连接
constraint5 = DeviceMustHaveTrafficGeneratorConnected(
    speed_consrtaint=TrafficGeneratorSpeedMustGreaterThen(10000))

# AP必须有至少3个STA连接，并且STA必须有速率为 1000 Mbit/s以上的测试仪表端口连接
constraint6 = ApMustHaveStaConnected(sta_constraints=[constraint4], sta_count=3)

print(constraint1.is_meet(ap1),
      constraint2.is_meet(ap1),
      constraint3.is_meet(ap1),
      constraint4.is_meet(ap1),
      constraint5.is_meet(ap1),
      constraint6.is_meet(ap1))


