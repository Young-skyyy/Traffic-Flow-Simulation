# Vehicle Dynamics Engineering Toolkit — SAE J2263 · BSFC Map · CAN Bus · UDS

Python 车辆动力学工程工具包。覆盖纵向动力学（发动机扭矩曲线/SAE J2263 动态滚动阻力/加速制动/WLTC 瞬态油耗/功率分解）、横向动力学（2-DOF 自行车模型/不足转向梯度/阶跃瞬态）、IDM 跟车模型、5-ECU CAN 总线仿真 + UDS 诊断协议栈，190 条 pytest 测试。

## 项目结构

```
.
├── vehicle.py                  # Vehicle 类、扭矩曲线、行驶阻力、加速/制动、IDM 跟车/ACC
├── lateral_dynamics.py         # 2-DOF 自行车模型、侧偏角、不足转向、稳态/瞬态转向
├── bsfc.py                     # BSFC 万有特性数据、双线性插值、油耗计算
├── wltc.py                     # WLTC Class 3 工况、瞬态油耗仿真（DFCO + 加浓）
├── can_demo.py                 # CAN 5-ECU 仿真、Motorola/Intel 字节序、DBC/ASC 生成
├── uds.py                      # UDS (ISO 14229) 诊断协议栈：Session/DID/DTC/ECU Reset
├── plotting.py                 # BSFC 热力图（三次样条 + contourf + 等功率线）
├── plot_dashboard.py           # 五合一汇总仪表盘（BSFC+转向+半径+瞬态+ACC）
├── vehicle_dynamics.py         # 主入口：结构化数据 + 终端显示
├── _constants.py               # 物理常量（G/ρ/kmh-m/s 换算）
├── _plot_utils.py              # matplotlib 跨平台中文字体检测
├── pyproject.toml              # 项目元数据 + pytest 配置
├── test_vehicle_dynamics.py    # 车辆动力学测试（含扭矩曲线/IDM/ACC）
├── test_can_demo.py            # CAN 总线测试（编解码/字节序/DBC）
├── test_uds.py                 # UDS 诊断协议测试
├── requirements.txt            # Python 依赖
└── README.md
```

## 模块

| 模块 | 文件 | 说明 |
|------|------|------|
| 车辆物理 | `vehicle.py` | Vehicle 类、发动机扭矩曲线、行驶阻力、加速、制动 |
| 功率分解 | `vehicle.py` | 爬坡功率、风阻功率（v³）、比功率、SAE J2263 动态滚动阻力 |
| 跟车/ACC | `vehicle.py` | IDM (Intelligent Driver Model) 跟车 + ACC 自适应巡航场景 |
| 横向动力学 | `lateral_dynamics.py` | 2-DOF 自行车模型、侧偏角、不足转向梯度、稳态/瞬态转向 |
| 油耗模型 | `bsfc.py` | BSFC Map（180 数据点）、双线性插值、L/100km |
| WLTC 工况 | `wltc.py` | Class 3 行驶工况（1800s）、瞬态油耗仿真（DFCO 断油 + 加速加浓） |
| CAN 总线 | `can_demo.py` | 5-ECU 报文生成、Motorola/Intel 字节序、DBC/ASC 导出、负载率/错误注入 |
| UDS 诊断 | `uds.py` | ISO 14229 协议栈：0x10/0x22/0x19/0x3E/0x11、Session 管理、DTC Status Byte |
| 可视化 | `plotting.py`, `plot_dashboard.py` | BSFC 热力图、五合一汇总仪表盘 |

## 功能

### 纵向动力学

- 发动机扭矩曲线模型：归一化外特性曲线 × 最大扭矩 → 线性插值查表 → 变速箱速比 → 轮端驱动力，替代传统 P=Fv 简化模型
- 加速仿真：0-100 km/h 全油门加速，含 5 速自动换挡逻辑（92% 红线升档）
- 制动距离：反应距离 + 制动距离，不同路面摩擦系数
- SAE J2263 动态滚动阻力：μ(v) = f₀ + f₁v + f₄v⁴
- 油耗计算：BSFC 双线性插值 + WLTC 瞬态仿真（含 DFCO 减速断油/加速加浓/怠速油耗）
- 功率分解：滚动阻力功率、风阻功率（v³）、爬坡功率、比功率（W/kg）

### 横向动力学

- 2-DOF 自行车模型：侧偏角 αf/αr、横摆角速度 r、侧向速度 vy
- 不足转向梯度 Kus = Wf/Cf - Wr/Cr（Cα 存储正值 magnitude，负号在侧向力公式中体现）
- 稳态转向响应：定方向盘转角下，横摆角速度、侧向加速度、转弯半径 vs 车速
- 阶跃转向瞬态：欧拉积分仿真，90% 上升时间 + 超调量 + ±2% 调节时间

### IDM 跟车 / ACC

- IDM (Intelligent Driver Model)：a = a_max × [1 - (v/v₀)ᵟ - (s*/s)²]，含安全时距 T / 最小间距 s₀ / 舒适减速度 b
- 定速跟车仿真：后车从高速接近前车 → IDM 平缓减速 → 稳态跟车
- ACC 场景：前车加速→巡航→减速，后车自适应巡航跟随

### CAN 总线仿真

- 5 个模拟 ECU：EMS、BMS、ABS、TCU、BCM
- Motorola (MSB) / Intel (LSB) 双字节序 CAN 帧编解码
- 自动生成标准 DBC 文件（Vector CANoe/CANalyzer 可读）+ ASC 日志
- 总线负载率实时监控 + 错误帧注入

### UDS 诊断协议

- ISO 14229 协议栈：ECU 诊断服务器 + 诊断仪交互
- 支持服务：0x10 (Diagnostic Session Control)、0x22 (Read DID)、0x19 (Read DTC)、0x3E (Tester Present)、0x11 (ECU Reset)
- S3 超时自动回退 default session + session 级权限校验 + 负响应码（NRC）
- DTC Status Byte 8 位完整实现（ISO 14229-1 Table D.1）

## 快速开始

### 环境

- Python 3.8+
- 依赖见 `requirements.txt`

### 安装

```bash
git clone https://github.com/Young-skyyy/vehicle-dynamics-toolkit.git
cd vehicle-dynamics-toolkit
pip install -r requirements.txt
```

### 运行

```bash
# 车辆动力学：加速、制动、油耗、功率分解、横向转向、IDM 跟车
python vehicle_dynamics.py

# CAN 总线仿真：ECU 报文、DBC 生成、ASC 日志、UDS 诊断演示
python can_demo.py

# 五合一仪表盘汇总图
python plot_dashboard.py
```

### 输出

运行 `vehicle_dynamics.py` 输出：

- 加速曲线（0-100 km/h，扭矩曲线 + 自动换挡）
- 制动距离对照表
- 三车型油耗对比（L/100km）
- 功率分解（常量 vs SAE J2263 动态滚动阻力）
- IDM 跟车模型 + ACC 自适应巡航
- 横向动力学分析（不足转向梯度、稳态转向、阶跃瞬态响应）
- BSFC 热力图（`bsfc_map_*.png`）
- 五合一汇总仪表盘（`dashboard_*.png`）

## 可视化

### 五合一汇总仪表盘

![Dashboard](dashboard_20260730_141955.png)

*BSFC 万有特性 + 等功率线 / 稳态转向响应 / 转弯半径 vs 车速 / 阶跃转向瞬态响应 / IDM ACC 跟车*

## 测试

[![pytest](https://github.com/Young-skyyy/vehicle-dynamics-toolkit/actions/workflows/test.yml/badge.svg)](https://github.com/Young-skyyy/vehicle-dynamics-toolkit/actions/workflows/test.yml)

190 条单元测试，覆盖核心函数。本地运行：

```bash
pip install -r requirements.txt
python -m pytest test_vehicle_dynamics.py test_can_demo.py test_uds.py -v
```

**测试覆盖：**

- `Vehicle` 类：初始化、档位选择、扭矩曲线生成、横向参数默认值
- `calc_resistance`：滚动+风阻公式、动态/常量滚动阻力对比
- `calc_braking_distance`：反应+制动物理、湿/干路面
- `calc_acceleration` / `calc_wheel_force`：扭矩曲线驱动模型、油门/档位覆盖
- 扭矩曲线：`get_engine_torque` 峰值/怠速/钳位/线性缩放
- `_interpolate_bsfc`：双线性插值、边界钳位、柴油 vs 汽油
- `_calc_l100_raw`：各车速巡航油耗
- `get_wltc_profile`：WLTC Class 3 数据完整性（1801 数据点，四阶段验证）
- 功率函数：爬坡功率、比功率、风阻功率（v³ 关系）
- 横向动力学：侧偏角、不足转向梯度、特征/临界车速、稳态转向、阶跃瞬态收敛
- IDM 跟车：空旷加速/过近减速/稳态跟车/跟车仿真收敛
- CAN 信号：编解码、Motorola/Intel 字节序 roundtrip、DBC 生成、ECU 状态机
- UDS 诊断：Session 控制/超时、DID 读写、DTC 查询（正/负响应）、ECU Reset 权限

## 关键技术

- **发动机扭矩曲线**：归一化外特性 → 线性插值 → 变速箱速比放大 → 轮端驱动力
- **BSFC 双线性插值**：在发动机万有特性图上查找瞬时油耗
- **SAE J2263 滑行阻力模型**：f₀ + f₁v + f₄v⁴ 动态滚动阻力系数
- **2-DOF 自行车模型**：侧偏角 → 侧向力 → 横摆力矩 → 状态空间欧拉积分
- **不足转向梯度**：Kus = Wf/Cf - Wr/Cr，区分不足/中性/过度转向
- **IDM 跟车模型**：自由加速项 + 交互制动项，参数化安全时距与舒适减速度
- **CAN 帧编解码**：11-bit 仲裁域、Intel/Motorola 字节序、8 字节载荷信号打包
- **UDS 诊断协议**：ISO 14229 会话管理、DID 数据读取、DTC Status Byte 位级解析

## License

MIT
