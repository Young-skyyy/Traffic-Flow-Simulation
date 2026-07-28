# -*- coding: utf-8 -*-
"""
车辆动力学基础仿真
从 traffic_flow.py 扩展 —— 把"车流量"升级为"一辆车怎么跑"
涉及：加速度、制动距离、油耗、跟车模型
"""

import math


# ============================================================
# 1. 车辆基本参数（可以换成任意车型）
# ============================================================


class Vehicle:
    """一辆车的物理参数"""

    def __init__(self, name, mass_kg, power_kw, drag_coeff=0.3, frontal_area_m2=2.2):
        self.name = name              # 车型名称
        self.mass = mass_kg           # 质量（kg）
        self.power = power_kw * 1000  # 发动机功率（W）
        self.cd = drag_coeff          # 空气阻力系数
        self.area = frontal_area_m2   # 迎风面积（m²）
        self.rolling_coeff = 0.015    # 滚动阻力系数（普通沥青路面）

    def __repr__(self):
        return f"{self.name} ({self.mass}kg, {self.power/1000:.0f}kW)"


# 定义两辆车做对比
car_sedan = Vehicle("普通轿车", 1500, 100, drag_coeff=0.28)
car_suv = Vehicle("SUV", 2000, 140, drag_coeff=0.35, frontal_area_m2=2.7)
car_truck = Vehicle("重型卡车", 15000, 300, drag_coeff=0.65, frontal_area_m2=7.0)


# ============================================================
# 2. 行驶阻力计算（牛顿第二定律的工程应用）
# ============================================================

def calc_resistance(vehicle, speed_ms):
    """计算车辆在给定速度下的总阻力（N）"""
    # 滚动阻力：F = μ × m × g（μ=滚动摩擦系数, g=9.8）
    rolling = vehicle.rolling_coeff * vehicle.mass * 9.8

    # 空气阻力：F = 0.5 × ρ × Cd × A × v²（ρ=空气密度1.225）
    aero = 0.5 * 1.225 * vehicle.cd * vehicle.area * speed_ms ** 2

    return rolling + aero


# ============================================================
# 3. 加速性能
# ============================================================

def calc_acceleration(vehicle, speed_ms):
    """计算车辆在当前速度下的加速度（m/s²）"""
    resistance = calc_resistance(vehicle, speed_ms)
    # 驱动力 = 功率 / 速度（P = F × v）
    force_drive = vehicle.power / speed_ms if speed_ms > 0 else 0
    # 净力 = 驱动力 - 阻力
    net_force = force_drive - resistance
    # F = m × a → a = F / m
    return max(0, net_force / vehicle.mass)


def simulate_acceleration(vehicle, target_speed_kmh=100, dt=0.1):
    """模拟车辆从 0 加速到目标速度的过程"""
    target = target_speed_kmh / 3.6  # km/h → m/s
    speed = 1.0  # 从 1 m/s 起步（避免除以零）
    distance = 0
    time_elapsed = 0

    print(f"\n{'='*50}")
    print(f"{vehicle.name} 加速到 {target_speed_kmh} km/h")
    print(f"{'='*50}")
    print(f"{'时间(s)':>8}  {'速度(km/h)':>10}  {'加速度(m/s²)':>12}  {'距离(m)':>8}")
    print("-" * 50)

    while speed < target and time_elapsed < 120:  # 最长模拟 120 秒
        acc = calc_acceleration(vehicle, speed)
        speed += acc * dt
        distance += speed * dt
        time_elapsed += dt

        if int(time_elapsed * 10) % 10 == 0:  # 每秒打印一次
            print(f"{time_elapsed:8.1f}  {speed*3.6:10.1f}  {acc:12.3f}  {distance:8.1f}")

    print(f"\n结果: {time_elapsed:.1f} 秒跑完 {distance:.0f} 米")


# ============================================================
# 4. 制动距离（安全相关，交通工程必备）
# ============================================================

def calc_braking_distance(speed_kmh, friction_coeff=0.7, reaction_time=1.5):
    """计算制动总距离 = 反应距离 + 制动距离"""
    speed_ms = speed_kmh / 3.6

    # 反应距离 = 速度 × 反应时间（人看到危险到踩刹车）
    reaction_dist = speed_ms * reaction_time

    # 制动距离 = v² / (2 × μ × g)（物理公式，μ=路面摩擦系数）
    braking_dist = speed_ms ** 2 / (2 * friction_coeff * 9.8)

    total = reaction_dist + braking_dist
    return reaction_dist, braking_dist, total


def show_braking_table():
    """展示不同车速下的制动距离"""
    print(f"\n{'='*60}")
    print("制动距离对照表（干燥沥青路面，反应时间 1.5s）")
    print(f"{'='*60}")
    print(f"{'车速(km/h)':>10}  {'反应距离(m)':>12}  {'制动距离(m)':>12}  {'总距离(m)':>10}")
    print("-" * 60)

    for v in [30, 50, 60, 80, 100, 120]:
        rd, bd, td = calc_braking_distance(v)
        print(f"{v:10.0f}  {rd:12.1f}  {bd:12.1f}  {td:10.1f}")


# ============================================================
# 5. 油耗估算
# ============================================================

def calc_fuel_consumption(vehicle, speed_kmh, distance_km):
    """估算给定速度和距离下的油耗（L）"""
    speed_ms = speed_kmh / 3.6
    resistance = calc_resistance(vehicle, speed_ms)

    # 做功 = 阻力 × 距离（W = F × d）
    work_joules = resistance * distance_km * 1000
    # 汽油热值约 34 MJ/L，发动机热效率约 30%
    fuel_liters = work_joules / (34e6 * 0.30)

    # 加上怠速/附件损耗（约 20% 额外消耗）
    return round(fuel_liters * 1.2, 2)


def show_fuel_table():
    """对比不同车型在不同速度下的油耗"""
    cars = [car_sedan, car_suv, car_truck]
    speeds = [60, 80, 100, 120]
    dist = 100  # 按 100 公里算

    print(f"\n{'='*70}")
    print(f"百公里油耗估算（L/100km）")
    print(f"{'='*70}")
    header = f"{'车型':>12}"
    for s in speeds:
        header += f"  {s}km/h"
    print(header)
    print("-" * 70)

    for car in cars:
        line = f"{car.name:>12}"
        for s in speeds:
            fuel = calc_fuel_consumption(car, s, dist)
            line += f"  {fuel:5.1f}"
        print(line)


# ============================================================
# 6. 跟车模型（交通工程核心）
# ============================================================

def car_following_simulation(lead_speed_kmh=60, follower_speed_kmh=70,
                              initial_gap_m=30, reaction_time=1.5, duration_s=30):
    """模拟后车跟随前车：前车匀速，后车需要减速避免碰撞"""
    lead_speed = lead_speed_kmh / 3.6
    follower_speed = follower_speed_kmh / 3.6
    gap = initial_gap_m
    time_elapsed = 0
    dt = 1.0

    print(f"\n{'='*60}")
    print(f"跟车模型仿真（前车{lead_speed_kmh}km/h, 后车{follower_speed_kmh}km/h, 初始间距{gap}m）")
    print(f"{'='*60}")
    print(f"{'时间(s)':>8}  {'间距(m)':>8}  {'后车速度':>8}  {'状态':>10}")
    print("-" * 50)

    for t in range(duration_s):
        # 前车匀速前进
        lead_pos = t * lead_speed

        # 后车如果没有反应延迟，减速
        if gap < 10:
            # 紧急制动（减速度 6 m/s²）
            follower_speed = max(0, follower_speed - 6 * dt)
        elif gap < 30:
            # 轻微减速（减速度 2 m/s²）
            follower_speed = max(lead_speed, follower_speed - 2 * dt)

        follower_pos = t * follower_speed
        gap = initial_gap_m + (lead_pos - follower_pos)

        status = "安全" if gap > 15 else ("警告" if gap > 5 else "危险！")
        print(f"{t:8.0f}  {gap:8.1f}  {follower_speed*3.6:8.1f}  {status:>10}")

        if gap <= 0:
            print(f"\n!!! 碰撞发生 !!! 时间: {t}s")
            break
        time_elapsed = t


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════╗
║       车辆动力学基础仿真                       ║
║       交通工程 + Python + 物理                ║
╚══════════════════════════════════════════════╝
    """)

    # 练习 1：看轿车加速到 100 km/h 的过程
    simulate_acceleration(car_sedan, target_speed_kmh=100)

    # 练习 2：制动距离表（交通工程设计必算）
    show_braking_table()

    # 练习 3：不同车型油耗对比
    show_fuel_table()

    # 练习 4：跟车模型（交通流理论核心）
    car_following_simulation()

    print("\n提示: 改参数试试 — 把路面摩擦系数从 0.7 改成 0.3（雨天）看制动距离变化")
