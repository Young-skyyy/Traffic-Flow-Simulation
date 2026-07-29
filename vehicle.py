# -*- coding: utf-8 -*-
"""
车辆基本参数 + 行驶阻力 + 加速/制动/跟车
"""

import math


class Vehicle:
    """一辆车的物理参数 + 动力总成参数"""

    def __init__(self, name, mass_kg, power_kw, drag_coeff=0.3, frontal_area_m2=2.2,
                 max_torque_nm=180, idle_rpm=800, max_rpm=6000,
                 gear_ratios=None, final_drive=4.0, wheel_radius_m=0.32,
                 trans_efficiency=0.90, fuel_density_gl=740, fuel_type="gasoline",
                 # 横向动力学参数
                 wheelbase_m=None, cg_to_front_m=None,
                 cornering_stiffness_f=None, cornering_stiffness_r=None,
                 yaw_inertia=None):
        self.name = name
        self.mass = mass_kg
        self.power = power_kw * 1000          # 发动机功率（W）
        self.cd = drag_coeff
        self.area = frontal_area_m2
        self.rolling_coeff = 0.015
        # 动力总成参数
        self.max_torque = max_torque_nm       # 发动机最大扭矩（Nm）
        self.idle_rpm = idle_rpm
        self.max_rpm = max_rpm
        self.gear_ratios = gear_ratios or [3.55, 2.11, 1.42, 1.00, 0.78]  # 各档速比
        self.final_drive = final_drive        # 主减速比
        self.wheel_radius = wheel_radius_m    # 轮胎滚动半径（m）
        self.trans_efficiency = trans_efficiency  # 传动效率
        self.fuel_density = fuel_density_gl   # 燃油密度（g/L），汽油 740，柴油 840
        self.fuel_type = fuel_type
        # 横向动力学参数
        self.wheelbase = wheelbase_m or 2.65          # 轴距（m），典型轿车
        self.cg_to_front = cg_to_front_m or self.wheelbase * 0.45  # 质心到前轴距离（m）
        self.cg_to_rear = self.wheelbase - self.cg_to_front         # 质心到后轴距离（m）
        # 侧偏刚度（N/rad），典型值：前轮 -80000，后轮 -70000（负号表示侧向力与侧偏角反向）
        self.cornering_stiffness_f = cornering_stiffness_f or 80000
        self.cornering_stiffness_r = cornering_stiffness_r or 70000
        # 横摆转动惯量（kg·m²），估算公式 Iz ≈ m × a × b
        self.yaw_inertia = yaw_inertia or self.mass * self.cg_to_front * self.cg_to_rear

    def select_gear(self, speed_kmh):
        """根据车速选择合适档位（简化的经济性换挡策略）"""
        if speed_kmh <= 0:
            return 0
        speed_ms = speed_kmh / 3.6
        # 目标发动机转速 1500-2500 RPM 为经济区间
        target_rpm = 2000
        best_gear = 1
        best_diff = float("inf")
        for g, ratio in enumerate(self.gear_ratios, start=1):
            rpm = speed_ms * ratio * self.final_drive / (2 * math.pi * self.wheel_radius) * 60
            # 不能低于怠速，不能高于红线
            if rpm < self.idle_rpm or rpm > self.max_rpm:
                continue
            diff = abs(rpm - target_rpm)
            if diff < best_diff:
                best_diff = diff
                best_gear = g
        return best_gear

    def __repr__(self):
        return f"{self.name} ({self.mass}kg, {self.power/1000:.0f}kW)"


# 定义三辆车做对比（含动力总成参数）
car_sedan = Vehicle("普通轿车", 1500, 100, drag_coeff=0.28,
                    max_torque_nm=180, idle_rpm=800, max_rpm=6200,
                    gear_ratios=[3.55, 2.11, 1.42, 1.00, 0.78],
                    final_drive=4.06, wheel_radius_m=0.32, trans_efficiency=0.90,
                    fuel_density_gl=740, fuel_type="gasoline",
                    wheelbase_m=2.65, cg_to_front_m=1.2,
                    cornering_stiffness_f=80000, cornering_stiffness_r=70000)
car_suv = Vehicle("SUV", 2000, 140, drag_coeff=0.35, frontal_area_m2=2.7,
                  max_torque_nm=250, idle_rpm=700, max_rpm=6000,
                  gear_ratios=[3.83, 2.36, 1.55, 1.00, 0.79],
                  final_drive=3.89, wheel_radius_m=0.36, trans_efficiency=0.88,
                  fuel_density_gl=740, fuel_type="gasoline",
                  wheelbase_m=2.75, cg_to_front_m=1.3,
                  cornering_stiffness_f=90000, cornering_stiffness_r=75000)
car_truck = Vehicle("重型卡车", 15000, 300, drag_coeff=0.65, frontal_area_m2=7.0,
                    max_torque_nm=1000, idle_rpm=600, max_rpm=4000,
                    gear_ratios=[5.50, 3.20, 1.90, 1.00, 0.73],
                    final_drive=4.30, wheel_radius_m=0.52, trans_efficiency=0.85,
                    fuel_density_gl=840, fuel_type="diesel",
                    wheelbase_m=5.0, cg_to_front_m=2.5,
                    cornering_stiffness_f=200000, cornering_stiffness_r=180000)


def rolling_coeff_dynamic(speed_ms):
    """SAE J2263 滑行阻力标准形式：μ(v) = f₀ + f₁·(v/100) + f₄·(v/100)⁴
    
    f₀：静态变形阻力（车速=0 时也存在的损耗）
    f₁：一次项，轮胎迟滞损耗随转速线性增长
    f₄：四次项，高速驻波效应，100km/h 以上才抬头
    系数来源：乘用车 coast-down 测试典型值（EPA 公开数据）
    """
    v = speed_ms * 3.6            # m/s → km/h，SAE 标准用 100km/h 归一化
    f0 = 0.010                    # 截距项
    f1 = 0.005                    # 速度一次项
    f4 = 0.002                    # 速度四次项
    return f0 + f1 * (v / 100) + f4 * (v / 100) ** 4


def calc_resistance(vehicle, speed_ms, dynamic_rr=False):
    """计算车辆在给定速度下的总阻力（N）
    
    dynamic_rr=False: 使用常量滚动阻力系数（0.015）
    dynamic_rr=True:  使用 SAE J2263 二次模型动态计算
    """
    # 滚动阻力：F = μ × m × g
    if dynamic_rr:
        coeff = rolling_coeff_dynamic(speed_ms)
    else:
        coeff = vehicle.rolling_coeff

    rolling = coeff * vehicle.mass * 9.8

    # 空气阻力：F = 0.5 × ρ × Cd × A × v²（ρ=空气密度1.225）
    aero = 0.5 * 1.225 * vehicle.cd * vehicle.area * speed_ms ** 2

    return rolling + aero


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


def calc_braking_distance(speed_kmh, friction_coeff=0.7, reaction_time=1.5):
    """计算制动总距离 = 反应距离 + 制动距离"""
    speed_ms = speed_kmh / 3.6

    # 反应距离 = 速度 × 反应时间（人看到危险到踩刹车）
    reaction_dist = speed_ms * reaction_time

    # 制动距离 = v² / (2 × μ × g)（物理公式，μ=路面摩擦系数）
    braking_dist = speed_ms ** 2 / (2 * friction_coeff * 9.8)

    total = reaction_dist + braking_dist
    return reaction_dist, braking_dist, total


def calc_grade_power(vehicle, speed_ms, grade_percent=5):
    """计算爬坡功率（W）
    
    爬坡阻力 F = m × g × sin(θ)，sin(θ) ≈ grade_percent / 100
    功率 P = F × v
    """
    grade_rad = math.atan(grade_percent / 100)
    grade_force = vehicle.mass * 9.8 * math.sin(grade_rad)
    return grade_force * speed_ms


def calc_power_to_weight(vehicle):
    """计算比功率（W/kg 和 kW/ton）
    
    比功率 = 发动机最大功率 / 整车质量
    是衡量车辆动力性的重要指标：
    - 轿车: 60-100 W/kg
    - 跑车: 150+ W/kg
    - 卡车: 10-30 W/kg
    """
    watt_per_kg = vehicle.power / vehicle.mass
    kw_per_ton = watt_per_kg  # W/kg == kW/ton（因为 1 kW / 1000 kg = 1 W/kg）
    return watt_per_kg, kw_per_ton


def calc_aero_drag_power(vehicle, speed_ms):
    """计算风阻功率（W）
    
    风阻 F = 0.5 × ρ × Cd × A × v²
    功率 P = F × v = 0.5 × ρ × Cd × A × v³
    风阻功率与速度的立方成正比，高速时是主要阻力来源
    """
    aero_force = 0.5 * 1.225 * vehicle.cd * vehicle.area * speed_ms ** 2
    return aero_force * speed_ms


def show_power_breakdown(vehicle, speed_kmh=100, grade_percent=5):
    """展示车辆在指定工况下的各功率分解"""
    speed_ms = speed_kmh / 3.6

    rolling_power_const = vehicle.rolling_coeff * vehicle.mass * 9.8 * speed_ms
    rolling_power_dyn = rolling_coeff_dynamic(speed_ms) * vehicle.mass * 9.8 * speed_ms
    aero_power = calc_aero_drag_power(vehicle, speed_ms)
    grade_power = calc_grade_power(vehicle, speed_ms, grade_percent)
    total_resistance_power = rolling_power_const + aero_power + grade_power
    total_dyn = rolling_power_dyn + aero_power + grade_power
    wpk, kpt = calc_power_to_weight(vehicle)

    print(f"\n{'='*60}")
    print(f"{vehicle.name} 功率分解 @ {speed_kmh}km/h, 坡度 {grade_percent}%")
    print(f"{'='*60}")
    print(f"  发动机最大功率:  {vehicle.power/1000:8.1f} kW")
    print(f"  比功率:          {wpk:8.1f} W/kg ({kpt:.1f} kW/ton)")
    print(f"{'-'*40}")
    print(f"  滚动阻力功率(常量 μ=0.015):  {rolling_power_const/1000:8.2f} kW")
    print(f"  滚动阻力功率(动态 SAE J2263): {rolling_power_dyn/1000:8.2f} kW")
    print(f"  风阻功率:                     {aero_power/1000:8.2f} kW")
    print(f"  爬坡功率:                     {grade_power/1000:8.2f} kW")
    print(f"{'-'*40}")
    print(f"  需求总功率(常量):  {total_resistance_power/1000:8.2f} kW")
    print(f"  需求总功率(动态):  {total_dyn/1000:8.2f} kW")
    print(f"  功率利用率:        {total_resistance_power/vehicle.power*100:8.1f} %")


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
