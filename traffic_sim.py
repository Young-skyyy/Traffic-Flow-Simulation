# -*- coding: utf-8 -*-
"""
交通流仿真器 v2.0
从单辆车 → 多车道路段 → 可模拟信号灯、拥堵波、事故影响
交通工程专业课的核心工具
"""

import random
import time
from vehicle_dynamics import Vehicle

# ============================================================
# 1. 路段设置
# ============================================================

VEHICLE_POOL = [
    Vehicle("轿车", 1500, 100, drag_coeff=0.28, frontal_area_m2=2.2),
    Vehicle("SUV", 2000, 140, drag_coeff=0.35, frontal_area_m2=2.7),
    Vehicle("卡车", 15000, 300, drag_coeff=0.65, frontal_area_m2=7.0),
    Vehicle("公交车", 12000, 200, drag_coeff=0.55, frontal_area_m2=6.5),
]

VEHICLE_LENGTHS = {"轿车": 5, "SUV": 5, "卡车": 12, "公交车": 12}
SAFE_GAP = 2.0  # 最小安全间距（米）

# ============================================================
# 2. 单车道仿真（含信号灯）
# ============================================================


def simulate_single_lane(duration_min=30, flow_rate=800, green_ratio=0.5, cycle_length=60):
    """
    单车道 + 信号灯 仿真

    参数：
        duration_min  : 仿真时长（分钟）
        flow_rate     : 到达流量（辆/小时）
        green_ratio   : 绿灯占比（0-1）
        cycle_length  : 信号周期（秒）

    返回：通过车辆数、总延误、平均延误、最大排队长度
    """
    total_seconds = duration_min * 60
    headway = 3600 / flow_rate  # 平均车头时距（秒/辆）
    next_arrival = 0
    queue = []
    passed = 0
    total_delay = 0
    max_queue = 0
    signal_green = True

    print(f"\n{'='*60}")
    print(f"单车道仿真 | 流量 {flow_rate} 辆/h | 绿信比 {green_ratio:.1%} | 周期 {cycle_length}s")
    print(f"{'='*60}")

    results = []  # 每秒记录一次，用于分析

    for sec in range(total_seconds):
        # 信号灯切换
        phase = sec % cycle_length
        signal_green = phase < cycle_length * green_ratio

        # 车辆到达（泊松分布随机性）
        if random.random() < 1 / headway:
            vtype = random.choice(["轿车", "轿车", "轿车", "SUV", "卡车", "公交车"])
            queue.append({"type": vtype, "arrive": sec, "depart": None, "delay": 0})

        # 车辆离开
        if signal_green and queue:
            # 饱和流率：约 1800 辆/小时/车道 → 2秒车头时距
            if sec - next_arrival >= 2.0:
                veh = queue.pop(0)
                veh["depart"] = sec
                veh["delay"] = sec - veh["arrive"]
                total_delay += veh["delay"]
                passed += 1
                next_arrival = sec

        qlen = len(queue)
        max_queue = max(max_queue, qlen)

        # 每秒记录状态
        results.append({
            "second": sec,
            "signal": "G" if signal_green else "R",
            "queue": qlen,
            "passed": passed,
        })

        # 首次达到最大排队时打印
        if qlen >= 10 and qlen == max_queue:
            print(f"  {sec//60:2d}:{sec%60:02d}  {'🟢' if signal_green else '🔴'}  排队 {qlen} 辆  ← 开始拥堵！")

    avg_delay = total_delay / passed if passed > 0 else 0
    print(f"\n结果: 通过 {passed} 辆 | 平均延误 {avg_delay:.1f}s | 最大排队 {max_queue} 辆")

    return {"passed": passed, "avg_delay": avg_delay, "max_queue": max_queue, "total_delay": total_delay, "results": results}


# ============================================================
# 3. 多方案对比（流量递增，找到通行能力瓶颈）
# ============================================================


def compare_scenarios():
    """不同流量下的通行表现对比"""
    flows = [400, 600, 800, 1000, 1200, 1400, 1600]
    print(f"\n{'='*70}")
    print(f"{'流量递增对比分析（绿信比 0.5，周期 60s）':^60}")
    print(f"{'='*70}")
    print(f"{'流量(辆/h)':>10}  {'通过':>6}  {'延误(s)':>8}  {'排队':>6}  {'通行率':>8}")
    print("-" * 50)

    for flow in flows:
        r = simulate_single_lane(duration_min=15, flow_rate=flow, green_ratio=0.5, cycle_length=60)
        pass_rate = r["passed"] / (flow * 0.25) * 100  # 15分钟理论到达数
        print(f"{flow:>10}  {r['passed']:>6}  {r['avg_delay']:>8.1f}  {r['max_queue']:>6}  {pass_rate:>7.1f}%")


# ============================================================
# 4. 双车道对比（有/无专用左转车道）
# ============================================================


def simulate_two_lanes(flow_rate=1200, left_turn_ratio=0.2):
    """双车道：直行+左转混行 vs 专用左转车道"""
    duration = 15 * 60
    headway = 3600 / flow_rate

    # 直行车道
    straight_flow = flow_rate * (1 - left_turn_ratio)
    straight_headway = 3600 / straight_flow if straight_flow > 0 else 9999
    straight_queue = []
    straight_passed = 0
    straight_delay = 0

    # 左转专用车道（假设有保护相位，绿信比 0.3）
    left_flow = flow_rate * left_turn_ratio
    left_headway = 3600 / left_flow if left_flow > 0 else 9999
    left_queue = []
    left_passed = 0
    left_delay = 0

    results = {"straight": [], "left": []}

    for sec in range(duration):
        # 直行绿灯（绿信比 0.5）
        straight_green = (sec % 60) < 30
        # 左转保护相位（绿信比 0.3）
        left_green = (sec % 60) < 18

        # 车辆到达
        if random.random() < 1 / straight_headway:
            straight_queue.append({"arrive": sec})
        if random.random() < 1 / left_headway:
            left_queue.append({"arrive": sec})

        # 车辆离开
        if straight_green and straight_queue and sec % 2 == 0:  # 2秒车头时距
            veh = straight_queue.pop(0)
            straight_delay += sec - veh["arrive"]
            straight_passed += 1

        if left_green and left_queue and sec % 2 == 0:
            veh = left_queue.pop(0)
            left_delay += sec - veh["arrive"]
            left_passed += 1

        results["straight"].append(len(straight_queue))
        results["left"].append(len(left_queue))

    avg_s = straight_delay / straight_passed if straight_passed else 0
    avg_l = left_delay / left_passed if left_passed else 0

    print(f"\n{'='*60}")
    print(f"双车道仿真 | 总流量 {flow_rate} 辆/h | 左转比例 {left_turn_ratio:.0%}")
    print(f"{'='*60}")
    print(f"  直行车道: 通过 {straight_passed} 辆, 平均延误 {avg_s:.1f}s, 剩余排队 {len(straight_queue)}")
    print(f"  左转车道: 通过 {left_passed} 辆, 平均延误 {avg_l:.1f}s, 剩余排队 {len(left_queue)}")

    return {"straight_passed": straight_passed, "straight_delay": avg_s,
            "left_passed": left_passed, "left_delay": avg_l}


# ============================================================
# 5. 事故/施工区仿真（车道封闭，通行能力骤降）
# ============================================================


def simulate_incident(flow_rate=1200, incident_start_min=5, incident_duration_min=10):
    """模拟突发事故导致车道封闭"""
    duration_min = 20
    total_seconds = duration_min * 60
    headway = 3600 / flow_rate
    queue = []
    passed = 0
    total_delay = 0

    # 事故期间通行能力降至 400 辆/h（单车道缓慢通行）
    incident_start = incident_start_min * 60
    incident_end = incident_start + incident_duration_min * 60

    print(f"\n{'='*60}")
    print(f"事故仿真 | 流量 {flow_rate} 辆/h | 事故 {incident_start_min}-{incident_start_min+incident_duration_min} 分钟")
    print(f"{'='*60}")

    for sec in range(total_seconds):
        in_incident = incident_start <= sec < incident_end
        effective_headway = 3600 / 400 if in_incident else headway  # 事故时通行能力大幅下降

        if random.random() < 1 / headway:
            queue.append({"arrive": sec})

        if queue and random.random() < 1 / effective_headway:
            veh = queue.pop(0)
            veh["delay"] = sec - veh["arrive"]
            total_delay += veh["delay"]
            passed += 1

        if in_incident and len(queue) >= 15 and len(queue) - 1 < 15:
            m = sec // 60
            print(f"  {m}:{sec%60:02d}  🚧 事故中！排队 {len(queue)} 辆")

    # 事故结束后多久清空
    recovery_time = 0
    for sec in range(incident_end, total_seconds):
        if not queue:
            break
        recovery_time += 1

    avg_delay = total_delay / passed if passed else 0
    print(f"\n结果: 通过 {passed} 辆 | 平均延误 {avg_delay:.1f}s | 事故恢复时间 ~{recovery_time}s")
    print(f"对比: 无事故时理论通过 {flow_rate * duration_min / 60:.0f} 辆")
    return {"passed": passed, "avg_delay": avg_delay, "recovery": recovery_time}


# ============================================================
# 6. 燃油经济性分析（不同车速下的百公里油耗）
# ============================================================


def fuel_economy_analysis():
    """对比 4 种车型在不同匀速下的百公里油耗"""
    speeds = [40, 60, 80, 100, 120]
    print(f"\n{'='*70}")
    print(f"百公里油耗分析 (L/100km)")
    print(f"{'='*70}")

    header = f"{'车型':>8}"
    for s in speeds:
        header += f"  {s:>6}km/h"
    print(header)
    print("-" * 70)

    for veh in VEHICLE_POOL:
        # 导入之前的油耗函数
        from vehicle_dynamics import calc_resistance
        line = f"{veh.name:>8}"

        for s in speeds:
            res = calc_resistance(veh, s / 3.6)
            work = res * 100000  # 100km
            fuel = work / (34e6 * 0.30) * 1.2
            line += f"  {fuel:6.1f}"
        print(line)

    print(f"\n最佳经济车速: 60-80 km/h（空气阻力小，引擎效率高）")
    print("120 km/h 时油耗比 80 km/h 高约 40-60%")


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════╗
║       交通流仿真工具 v2.0                          ║
║       信号灯 · 多车道 · 事故 · 油耗 · 排队        ║
╚══════════════════════════════════════════════════╝
    """)

    # 实验 1：流量逐渐增加，找到瓶颈
    compare_scenarios()

    # 实验 2：双车道 vs 单车道
    simulate_two_lanes(flow_rate=1200, left_turn_ratio=0.2)

    # 实验 3：事故影响
    simulate_incident(flow_rate=1000, incident_start_min=5, incident_duration_min=8)

    # 实验 4：油耗分析
    fuel_economy_analysis()

    print("\n💡 试试改成不同参数看效果:")
    print("   simulate_single_lane(flow_rate=2000, green_ratio=0.7)  # 高峰期 + 延长绿灯")
    print("   simulate_incident(flow_rate=1500, incident_duration_min=20)  # 大车流 + 长事故")
