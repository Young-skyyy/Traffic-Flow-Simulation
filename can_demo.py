# -*- coding: utf-8 -*-
"""
CAN 总线多 ECU 仿真器
纯 Python，模拟真实整车 CAN 网络中的多个 ECU 周期性发送报文，
支持 DBC 式信号解析 + DTC 故障码生成。

适用场景：
  - 理解 CAN 报文格式与信号解析
  - 模拟 HiL 测试中的 ECU 数据源
  - CAN 日志生成，供上位机/诊断工具消费
"""

import time
import random
import struct


# ============================================================
# 1. CAN 帧定义（DBC 风格：每条消息的 ID、周期、信号列表）
# ============================================================

CAN_MESSAGES = {
    # 发动机 ECU —— 周期 10ms
    "EngineData": {
        "id": 0x0C9,
        "cycle_ms": 10,
        "desc": "发动机数据",
        "signals": [
            {"name": "节气门位置",   "start": 0,  "len": 8,  "scale": 0.4,   "offset": 0,    "unit": "%"},
            {"name": "发动机转速",   "start": 8,  "len": 16, "scale": 0.25,  "offset": 0,    "unit": "rpm"},
            {"name": "冷却液温度",   "start": 24, "len": 8,  "scale": 1,     "offset": -40,  "unit": "degC"},
            {"name": "车速",         "start": 32, "len": 16, "scale": 0.01,  "offset": 0,    "unit": "km/h"},
            {"name": "进气歧管压力", "start": 48, "len": 8,  "scale": 1,     "offset": 0,    "unit": "kPa"},
        ],
    },

    # 电池管理系统 BMS —— 周期 100ms
    "BatteryStatus": {
        "id": 0x180,
        "cycle_ms": 100,
        "desc": "电池状态",
        "signals": [
            {"name": "SOC",          "start": 0,  "len": 8,  "scale": 0.5,   "offset": 0,   "unit": "%"},
            {"name": "总电压",       "start": 8,  "len": 16, "scale": 0.1,   "offset": 0,   "unit": "V"},
            {"name": "电流",         "start": 24, "len": 16, "scale": 0.1,   "offset": -500, "unit": "A"},
            {"name": "最高单体温度",  "start": 40, "len": 8,  "scale": 1,     "offset": -40, "unit": "degC"},
            {"name": "最低单体温度",  "start": 48, "len": 8,  "scale": 1,     "offset": -40, "unit": "degC"},
        ],
    },

    # ABS/ESP 制动控制器 —— 周期 20ms
    "ABS_WheelSpeed": {
        "id": 0x210,
        "cycle_ms": 20,
        "desc": "轮速与制动",
        "signals": [
            {"name": "左前轮速",    "start": 0,  "len": 16, "scale": 0.01,  "offset": 0,   "unit": "km/h"},
            {"name": "右前轮速",    "start": 16, "len": 16, "scale": 0.01,  "offset": 0,   "unit": "km/h"},
            {"name": "左后轮速",    "start": 32, "len": 16, "scale": 0.01,  "offset": 0,   "unit": "km/h"},
            {"name": "右后轮速",    "start": 48, "len": 16, "scale": 0.01,  "offset": 0,   "unit": "km/h"},
        ],
    },

    # 变速箱 TCU —— 周期 50ms
    "Transmission": {
        "id": 0x288,
        "cycle_ms": 50,
        "desc": "变速箱状态",
        "signals": [
            {"name": "当前档位",   "start": 0,  "len": 4,  "scale": 1,   "offset": 0,   "unit": ""},
            {"name": "变速箱油温", "start": 8,  "len": 8,  "scale": 1,   "offset": -40, "unit": "degC"},
            {"name": "输出轴转速", "start": 16, "len": 16, "scale": 1,   "offset": 0,   "unit": "rpm"},
        ],
    },

    # 车身控制器 BCM —— 周期 200ms
    "BodyControl": {
        "id": 0x320,
        "cycle_ms": 200,
        "desc": "车身状态",
        "signals": [
            {"name": "左前门",     "start": 0,  "len": 2,  "scale": 1, "offset": 0, "unit": ""},
            {"name": "右前门",     "start": 2,  "len": 2,  "scale": 1, "offset": 0, "unit": ""},
            {"name": "左后门",     "start": 4,  "len": 2,  "scale": 1, "offset": 0, "unit": ""},
            {"name": "右后门",     "start": 6,  "len": 2,  "scale": 1, "offset": 0, "unit": ""},
            {"name": "近光灯",     "start": 8,  "len": 2,  "scale": 1, "offset": 0, "unit": ""},
            {"name": "远光灯",     "start": 10, "len": 2,  "scale": 1, "offset": 0, "unit": ""},
            {"name": "转向灯",     "start": 12, "len": 2,  "scale": 1, "offset": 0, "unit": ""},
            {"name": "后备箱",     "start": 14, "len": 2,  "scale": 1, "offset": 0, "unit": ""},
        ],
    },
}


# ============================================================
# 2. CAN 帧编码/解码（基于信号定义）
# ============================================================

def encode_signal(value, sig):
    """将物理值编码为原始整数值"""
    raw = int((value - sig["offset"]) / sig["scale"])
    max_val = (1 << sig["len"]) - 1
    return max(0, min(raw, max_val))


def decode_signal(raw, sig):
    """将原始整数值解码为物理值"""
    return round(raw * sig["scale"] + sig["offset"], 2)


def build_can_frame(msg_def, signal_values):
    """根据信号值列表构建 8 字节 CAN 数据帧"""
    data = [0] * 8
    for i, sig in enumerate(msg_def["signals"]):
        raw = encode_signal(signal_values[i], sig)
        start_bit = sig["start"]
        # 按 Motorola 序写入（大端）
        for bit in range(sig["len"]):
            byte_idx = (start_bit + bit) // 8
            bit_idx = 7 - ((start_bit + bit) % 8)
            if byte_idx < 8:
                if raw & (1 << (sig["len"] - 1 - bit)):
                    data[byte_idx] |= (1 << bit_idx)
    return data


def parse_can_frame(data, msg_def):
    """根据信号定义解析 8 字节 CAN 数据帧"""
    result = {}
    for sig in msg_def["signals"]:
        raw = 0
        start_bit = sig["start"]
        for bit in range(sig["len"]):
            byte_idx = (start_bit + bit) // 8
            bit_idx = 7 - ((start_bit + bit) % 8)
            if byte_idx < 8 and (data[byte_idx] & (1 << bit_idx)):
                raw |= (1 << (sig["len"] - 1 - bit))
        result[sig["name"]] = decode_signal(raw, sig)
    return result


# ============================================================
# 3. ECU 仿真器 —— 每辆车的运行状态
# ============================================================

class VehicleECU:
    """整车 ECU 状态机，维持车辆运行参数随时间连续变化"""

    def __init__(self):
        self.rpm = 800                              # 怠速
        self.throttle = 0
        self.speed = 0                              # km/h
        self.coolant_temp = 25                      # 冷启动
        self.gear = 0                               # P 档
        self.soc = 80.0                             # 电池 SOC
        self.brake_pressure = 0
        self.accelerating = False

    def update(self, dt_s):
        """每 dt 秒更新一次车辆状态"""
        # 模拟一个简单的驾驶循环
        if not self.accelerating and self.speed <= 0:
            self.accelerating = True
            self.gear = 1
        if self.speed >= 80:
            self.accelerating = False

        if self.accelerating:
            self.throttle = min(80, self.throttle + random.uniform(0, 10) * dt_s)
            self.rpm += int(500 * dt_s)
            self.speed += 3 * dt_s
        else:
            self.throttle = max(0, self.throttle - random.uniform(5, 15) * dt_s)
            self.rpm -= int(300 * dt_s)
            self.speed = max(0, self.speed - 2 * dt_s)

        self.rpm = max(800, min(6000, self.rpm))
        self.speed = max(0, min(120, self.speed))
        self.coolant_temp = min(95, self.coolant_temp + 0.5 * dt_s)
        self.soc -= 0.001 * dt_s  # 缓慢放电

        # 档位随车速变化
        if self.speed > 60:
            self.gear = 5
        elif self.speed > 40:
            self.gear = 4
        elif self.speed > 25:
            self.gear = 3
        elif self.speed > 10:
            self.gear = 2
        elif self.speed > 0:
            self.gear = 1
        else:
            self.gear = 0

        self.brake_pressure = random.uniform(0, 5) if not self.accelerating else 0


# ============================================================
# 4. CAN 总线仿真主循环
# ============================================================

def simulate_can_bus(duration_s=5, print_interval_ms=500):
    """
    模拟 CAN 总线运行 duration_s 秒。
    每 print_interval_ms 毫秒打印一次总线快照。
    """
    veh = VehicleECU()
    dt = 0.01  # 10ms 主循环步长
    total_steps = int(duration_s / dt)

    # 各消息的发送计数器
    timers = {name: 0 for name in CAN_MESSAGES}

    print(f"\nCAN 总线仿真启动（{duration_s}s）\n")
    print(f"{'时间':>8}  {'ID':>6}  {'消息名称':<16}  {'信号值'}")
    print("-" * 70)

    last_print = -print_interval_ms / 1000.0
    msg_count = 0
    pending_prints = []  # 当前打印周期内积攒的消息

    for step in range(total_steps):
        sim_time = step * dt
        veh.update(dt)

        # 检查每条消息是否到发送周期
        for name, msg_def in CAN_MESSAGES.items():
            timers[name] += dt * 1000  # 累计毫秒
            if timers[name] >= msg_def["cycle_ms"]:
                timers[name] -= msg_def["cycle_ms"]

                # 根据当前车辆状态生成信号值
                frame_data = generate_frame(name, msg_def, veh, sim_time)
                parsed = parse_can_frame(frame_data, msg_def)

                # 收集到待打印列表
                signals_str = ", ".join(
                    f"{k}={v}{msg_def['signals'][i]['unit']}"
                    for i, (k, v) in enumerate(parsed.items())
                    if i < 4
                )
                pending_prints.append((sim_time, msg_def['id'], name, signals_str))
                msg_count += 1

        # 按打印间隔输出积攒的消息
        if sim_time - last_print >= print_interval_ms / 1000.0:
            for t, mid, mname, mstr in pending_prints:
                print(f"{t:7.2f}s  0x{mid:03X}  {mname:<16}  {mstr}")
            pending_prints.clear()
            last_print = sim_time

    print(f"\n总计发送 {msg_count} 条 CAN 帧")


def generate_frame(name, msg_def, veh, sim_time):
    """根据 ECU 类型和当前车辆状态，生成 8 字节 CAN 数据"""
    if name == "EngineData":
        return build_can_frame(msg_def, [
            veh.throttle,
            veh.rpm,
            veh.coolant_temp,
            veh.speed,
            random.randint(30, 50),  # 进气压力
        ])
    elif name == "BatteryStatus":
        return build_can_frame(msg_def, [
            veh.soc,
            random.uniform(350, 400),
            random.uniform(-10, 50),
            random.uniform(25, 35),
            random.uniform(22, 30),
        ])
    elif name == "ABS_WheelSpeed":
        base = veh.speed
        return build_can_frame(msg_def, [
            base + random.uniform(-0.5, 0.5),
            base + random.uniform(-0.5, 0.5),
            base + random.uniform(-0.3, 0.3),
            base + random.uniform(-0.3, 0.3),
        ])
    elif name == "Transmission":
        return build_can_frame(msg_def, [
            veh.gear,
            veh.coolant_temp + 10,
            veh.rpm,
        ])
    elif name == "BodyControl":
        # 0=关闭 1=打开 2=故障 3=无效
        return build_can_frame(msg_def, [
            0, 0, 0, 0,  # 四门关闭
            1 if sim_time > 2 else 0,  # 近光灯
            0, 0,  # 远光/转向灯关
            0,  # 后备箱关
        ])


# ============================================================
# 5. DTC 故障码仿真
# ============================================================

DTC_DATABASE = {
    "P0301": {"desc": "1缸失火检测", "ecu": "EMS"},
    "P0420": {"desc": "催化转化器效率低于阈值", "ecu": "EMS"},
    "U0100": {"desc": "与 ECM/PCM 失去通讯", "ecu": "CAN"},
    "C0035": {"desc": "左前轮速传感器电路故障", "ecu": "ABS"},
    "B1A00": {"desc": "环境光传感器故障", "ecu": "BCM"},
    "P0A7F": {"desc": "电池组劣化", "ecu": "BMS"},
}


def simulate_dtc_check():
    """模拟诊断仪读取故障码"""
    print(f"\nDTC 故障码扫描")
    print("-" * 40)
    active = random.sample(list(DTC_DATABASE.keys()), k=random.randint(0, 2))
    if not active:
        print("  无故障码（系统正常）")
    else:
        for code in active:
            dtc = DTC_DATABASE[code]
            print(f"  {code} | {dtc['ecu']} | {dtc['desc']}")


# ============================================================
# 6. 主程序
# ============================================================

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════╗
║     CAN 总线多 ECU 仿真器                      ║
║     发动机 | BMS | ABS | 变速箱 | 车身         ║
╚══════════════════════════════════════════════╝
    """)

    # 场景 1：CAN 总线运行仿真
    simulate_can_bus(duration_s=5, print_interval_ms=300)

    # 场景 2：DTC 故障码扫描
    simulate_dtc_check()

    print("\n提示: 修改 VehicleECU.update() 可自定义驾驶循环，")
    print("      修改 CAN_MESSAGES 可增删 ECU 和信号定义。")
