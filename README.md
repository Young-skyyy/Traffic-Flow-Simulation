# Traffic-Flow-Simulation

交通流仿真与车辆动力学分析工具，基于 Python 实现，涵盖交通工程核心模型。

## 功能模块

| 模块 | 文件 | 说明 |
|------|------|------|
| 交通流量计算 | `traffic_flow.py` | 根据车速/间距计算单车道通行能力 |
| 车辆动力学 | `vehicle_dynamics.py` | 加速性能、制动距离、油耗、跟车模型 |
| 交通流仿真 | `traffic_sim.py` | 信号灯、多车道、事故影响、排队分析 |
| CAN 总线仿真 | `can_demo.py` | 多 ECU 报文生成、DBC 式信号解析、DTC 故障码 |

## 技术栈

- Python 3
- 物理建模（阻力、制动、油耗）
- 交通工程理论（流量、延误、排队、通行能力）

## 快速开始

```bash
# 交通流量计算
python traffic_flow.py

# 车辆动力学仿真（加速/制动/油耗/跟车）
python vehicle_dynamics.py

# 交通流仿真（信号灯/多车道/事故场景）
python traffic_sim.py

# CAN 总线仿真（5 个 ECU + 故障码扫描）
python can_demo.py
```

## 仿真场景

- 不同车速/间距下的通行能力对比
- 轿车/SUV/卡车/公交的加速与制动性能
- 信号灯控制下的排队与延误分析
- 双车道左转专用相位仿真
- 突发事故对通行能力的影响
- 多车型百公里油耗对比
