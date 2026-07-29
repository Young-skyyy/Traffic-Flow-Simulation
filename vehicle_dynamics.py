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
    """一辆车的物理参数 + 动力总成参数"""

    def __init__(self, name, mass_kg, power_kw, drag_coeff=0.3, frontal_area_m2=2.2,
                 max_torque_nm=180, idle_rpm=800, max_rpm=6000,
                 gear_ratios=None, final_drive=4.0, wheel_radius_m=0.32,
                 trans_efficiency=0.90, fuel_density_gl=740, fuel_type="gasoline"):
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
                    fuel_density_gl=740, fuel_type="gasoline")
car_suv = Vehicle("SUV", 2000, 140, drag_coeff=0.35, frontal_area_m2=2.7,
                  max_torque_nm=250, idle_rpm=700, max_rpm=6000,
                  gear_ratios=[3.83, 2.36, 1.55, 1.00, 0.79],
                  final_drive=3.89, wheel_radius_m=0.36, trans_efficiency=0.88,
                  fuel_density_gl=740, fuel_type="gasoline")
car_truck = Vehicle("重型卡车", 15000, 300, drag_coeff=0.65, frontal_area_m2=7.0,
                    max_torque_nm=1000, idle_rpm=600, max_rpm=4000,
                    gear_ratios=[5.50, 3.20, 1.90, 1.00, 0.73],
                    final_drive=4.30, wheel_radius_m=0.52, trans_efficiency=0.85,
                    fuel_density_gl=840, fuel_type="diesel")


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
# 5. 油耗模型（BSFC 万有特性法）
# ============================================================
#
# 换算链：
#   车速 → 选档 → 发动机转速(veh.select_gear)
#   车速 → 行驶阻力(calc_resistance) → 轮端扭矩 → 发动机扭矩
#   (转速, 扭矩) → 查 BSFC map → 瞬时燃油消耗率(g/kWh)
#   → 油耗(L/100km) = BSFC × 功率 × 100 / (油密度 × 车速)
#
# BSFC (Brake Specific Fuel Consumption) 是发动机效率的等高线图：
#   最优区 (~240 g/kWh)：2000-3000 rpm, 70-85% 负荷
#   最差区 (~500+ g/kWh)：怠速低负荷 或 红线高转


# ---- BSFC Map 定义 ----
# 横轴: 发动机转速 (RPM)
# 纵轴: 扭矩负荷比 (实际扭矩 / 最大扭矩)
# 值:  燃油消耗率 (g/kWh)，越小越省油
#
# 数据参考典型 2.0L 自然吸气汽油机台架测试

_BSFC_RPM_GRID = [800, 1200, 1800, 2500, 3500, 4500, 5500, 6200]   # 转速网格

# 汽油机 BSFC map
_BSFC_GASOLINE = [
    # 800   1200  1800  2500  3500  4500  5500  6200   ← RPM
    [ 580,  480,  400,  360,  380,  430,  500,  560 ],  #  5% 负荷
    [ 400,  330,  285,  270,  280,  310,  370,  440 ],  # 15% 负荷
    [ 310,  270,  250,  238,  245,  265,  310,  360 ],  # 30% 负荷
    [ 275,  250,  240,  233,  240,  255,  285,  320 ],  # 50% 负荷
    [ 265,  245,  238,  233,  240,  255,  280,  310 ],  # 70% 负荷
    [ 262,  248,  242,  240,  248,  268,  300,  340 ],  # 85% 负荷
    [ 275,  260,  255,  255,  270,  295,  335,  380 ],  # 100% 负荷
]
_BSFC_LOAD_GRID = [0.05, 0.15, 0.30, 0.50, 0.70, 0.85, 1.0]  # 负荷比网格

# 柴油机 BSFC map（整体比汽油机低 30-40 g/kWh，但曲线形状相似）
_BSFC_DIESEL = [
    # 600   1000  1500  2000  2800  3500  4000
    [ 480,  380,  310,  290,  300,  340,  400 ],
    [ 320,  260,  230,  215,  225,  255,  300 ],
    [ 250,  215,  198,  188,  195,  215,  250 ],
    [ 225,  200,  190,  182,  188,  205,  235 ],
    [ 218,  198,  188,  182,  190,  208,  238 ],
    [ 215,  200,  192,  188,  198,  220,  255 ],
    [ 228,  215,  208,  205,  218,  245,  285 ],
]
_BSFC_DIESEL_RPM = [600, 1000, 1500, 2000, 2800, 3500, 4000]


def _interpolate_bsfc(rpm, load_ratio, fuel_type="gasoline"):
    """在 BSFC map 中双线性插值，返回 (rpm, load) 对应的 g/kWh"""
    if fuel_type == "diesel":
        rpm_grid = _BSFC_DIESEL_RPM
        bsft_map = _BSFC_DIESEL
    else:
        rpm_grid = _BSFC_RPM_GRID
        bsft_map = _BSFC_GASOLINE

    # 钳制到 map 边界内
    rpm = max(rpm_grid[0], min(rpm_grid[-1], rpm))
    load_ratio = max(_BSFC_LOAD_GRID[0], min(_BSFC_LOAD_GRID[-1], load_ratio))

    # 找转速区间
    i_rpm = 0
    for i in range(len(rpm_grid) - 1):
        if rpm_grid[i] <= rpm <= rpm_grid[i + 1]:
            i_rpm = i
            break
    # 找负荷区间
    i_load = 0
    for i in range(len(_BSFC_LOAD_GRID) - 1):
        if _BSFC_LOAD_GRID[i] <= load_ratio <= _BSFC_LOAD_GRID[i + 1]:
            i_load = i
            break

    # 双线性插值
    rpm_low, rpm_high = rpm_grid[i_rpm], rpm_grid[i_rpm + 1]
    load_low, load_high = _BSFC_LOAD_GRID[i_load], _BSFC_LOAD_GRID[i_load + 1]

    q11 = bsft_map[i_load][i_rpm]
    q12 = bsft_map[i_load][i_rpm + 1]
    q21 = bsft_map[i_load + 1][i_rpm]
    q22 = bsft_map[i_load + 1][i_rpm + 1]

    t_rpm = (rpm - rpm_low) / (rpm_high - rpm_low) if rpm_high != rpm_low else 0
    t_load = (load_ratio - load_low) / (load_high - load_low) if load_high != load_low else 0

    return (q11 * (1 - t_rpm) * (1 - t_load) +
            q12 * t_rpm * (1 - t_load) +
            q21 * (1 - t_rpm) * t_load +
            q22 * t_rpm * t_load)


def calc_fuel_consumption(vehicle, speed_kmh, distance_km):
    """
    基于 BSFC 万有特性 map 计算油耗。

    换算逻辑:
      1. 选档 → gear_ratio
      2. 发动机转速 = 车速 × 总减速比 / 轮胎周长 × 60
      3. 行驶阻力 → 轮端扭矩 → 发动机扭矩 / 传动效率
      4. 发动机功率 = 扭矩 × 转速 (kW)
      5. 查 BSFC map → 燃油消耗率 (g/kWh)
      6. 油耗 = BSFC × 功率 × 100km / (燃油密度 × 车速)  → L/100km

    返回: 给定距离的总油耗（L）
    """
    gear = vehicle.select_gear(speed_kmh)
    if gear == 0:
        # 停车怠速油耗
        idle_bsfc = _interpolate_bsfc(vehicle.idle_rpm, 0.05, vehicle.fuel_type)
        idle_power = vehicle.idle_rpm * vehicle.max_torque * 0.05 * 2 * math.pi / 60 / 1000
        fuel_rate = idle_bsfc * idle_power / 3600 / vehicle.fuel_density  # L/s
        return round(fuel_rate * distance_km * 1000 / 5.0 * 3600, 2)  # 假设怠速 5km/h 等效

    speed_ms = speed_kmh / 3.6
    gear_ratio = vehicle.gear_ratios[gear - 1]
    total_ratio = gear_ratio * vehicle.final_drive

    # 发动机转速 = 轮速 × 总减速比 / 轮胎半径 (rad/s) × 60/(2π) → RPM
    wheel_rps = speed_ms / (2 * math.pi * vehicle.wheel_radius)
    engine_rpm = wheel_rps * total_ratio * 60

    # 行驶阻力
    resistance = calc_resistance(vehicle, speed_ms)

    # 轮端扭矩 → 发动机扭矩（考虑传动损耗）
    wheel_torque = resistance * vehicle.wheel_radius
    engine_torque = wheel_torque / (total_ratio * vehicle.trans_efficiency)

    # 发动机功率 (kW)
    engine_power_kw = engine_torque * engine_rpm * 2 * math.pi / 60 / 1000

    # 负荷比
    load_ratio = engine_torque / vehicle.max_torque
    load_ratio = max(0.01, min(1.0, load_ratio))  # 钳制

    # 查 BSFC map
    bsfc = _interpolate_bsfc(engine_rpm, load_ratio, vehicle.fuel_type)

    # 瞬时油耗 = BSFC (g/kWh) × 功率 (kW) / 3600 (s/h) → g/s
    fuel_mass_rate = bsfc * engine_power_kw / 3600  # g/s
    fuel_vol_rate = fuel_mass_rate / vehicle.fuel_density  # L/s

    # 百公里油耗 = 瞬时油耗(L/s) × 100km耗时(s) → L/100km
    time_per_100km = 360000 / speed_kmh  # 秒
    l_per_100km = fuel_vol_rate * time_per_100km

    return round(l_per_100km * distance_km / 100, 2)


def show_fuel_table():
    """BSFC 模型：展示各车速下的档位、转速、负荷和油耗"""
    cars = [car_sedan, car_suv, car_truck]
    speeds = [20, 30, 50, 70, 90, 110, 120]

    print(f"\n{'='*95}")
    print("  百公里油耗分析（BSFC 万有特性模型）")
    print(f"{'='*95}")
    header = f"{'车型':>10}  {'车速':>5}  {'档位':>4}  {'转速':>7}  {'负荷':>6}  {'BSFC':>6}  {'油耗':>6}"
    print(header)
    print("-" * 95)

    for car in cars:
        for v in speeds:
            gear = car.select_gear(v)
            speed_ms = v / 3.6
            gear_ratio = car.gear_ratios[gear - 1] if gear > 0 else 0
            total_ratio = gear_ratio * car.final_drive

            # 计算运行时参数
            if gear > 0:
                wheel_rps = speed_ms / (2 * math.pi * car.wheel_radius)
                engine_rpm = wheel_rps * total_ratio * 60
                resistance = calc_resistance(car, speed_ms)
                engine_torque = resistance * car.wheel_radius / (total_ratio * car.trans_efficiency)
                load_ratio = min(1.0, engine_torque / car.max_torque)
                bsfc = _interpolate_bsfc(engine_rpm, max(0.01, min(1.0, load_ratio)), car.fuel_type)
                l100 = calc_fuel_consumption(car, v, 100)
            else:
                engine_rpm, bsfc, l100 = car.idle_rpm, 580, 0
                load_ratio = 0

            gear_str = f"{gear}档" if gear > 0 else "空档"
            print(f"{car.name:>10}  {v:>4}km  {gear_str:>4}  "
                  f"{engine_rpm:>5.0f}rpm  {load_ratio:>4.0%}  "
                  f"{bsfc:>4.0f}g   {l100:>5.1f}L")

        print("-" * 95)


# ============================================================
# 6. 瞬态油耗仿真（加速/减速/怠速 —— 非稳态工况）
# ============================================================
#
# 稳态模型只算匀速巡航，但实际驾驶中瞬态工况大量存在：
#   - 加速时：ECU 会加浓喷油（空燃比降低）以提升扭矩响应，
#     同一 (转速,负荷) 点的 BSFC 比稳态高 10~30%
#   - 减速时：收油门且转速 > 阈值 → 断油（DFCO, Decel Fuel Cut-Off），
#     瞬时油耗降为 0，靠发动机制动
#   - 换挡时：离合器断开瞬间扭矩中断，但发动机仍消耗怠速油量
#
# 本模块模拟一个驾驶循环，对比瞬态总油耗 vs 稳态估算，

# ---- 简易城市工况循环：怠速→加速→巡航→减速→再加速→停车 ----
# 格式: [(阶段名称, 持续秒数, 目标车速 km/h)]
_URBAN_CYCLE = [
    ("冷启动怠速",  5,   0),
    ("起步加速",   10,  50),
    ("中速巡航",   10,  50),
    ("减速制动",    6,  20),
    ("低速巡航",    8,  20),
    ("再加速",      8,  60),
    ("高速巡航",   10,  60),
    ("减速停车",    8,   0),
    ("热车怠速",    5,   0),
]


def simulate_transient_cycle(vehicle, cycle=None, dt=0.1):
    """
    模拟车辆跟随驾驶循环的瞬态油耗。

    每一步的换算链：
      1. 驾驶员模型：车速误差 → 油门/刹车开度
      2. 油门 × 最大扭矩 → 发动机输出扭矩
      3. 扭矩 - 阻力 → 轮端净扭矩 → 实际加速度
      4. 加速度 > 0 → 加浓修正 (BSFC × 1.0~1.3)
         油门 = 0 且 转速 > 阈值 → 断油 (BSFC = 0)
      5. 查 BSFC map → 瞬时油耗 → 累计

    返回: (总油耗L, 总距离m, 平均油耗L/100km, 稳态估算总油耗L)
    """
    cycle = cycle or _URBAN_CYCLE
    total_time = sum(phase[1] for phase in cycle)
    steps = int(total_time / dt)

    # 车辆状态
    speed = 0.0          # m/s
    distance = 0.0       # m
    total_fuel_L = 0.0   # 累计油耗 (L)
    steady_fuel_L = 0.0  # 稳态估算累计 (假设瞬间到达目标速度并巡航)
    gear = 0
    engine_rpm = vehicle.idle_rpm

    # 构建逐秒目标车速序列
    targets = []
    for _, duration, target_kmh in cycle:
        targets.extend([target_kmh / 3.6] * int(duration / dt))

    print(f"\n{'='*95}")
    print(f"  瞬态油耗仿真 — {vehicle.name} — 简易城市工况 ({total_time}s)")
    print(f"{'='*95}")
    print(f"{'时间':>6}  {'目标':>5}  {'实际':>5}  {'油门':>5}  {'档位':>3}  "
          f"{'转速':>6}  {'负荷':>5}  {'BSFC':>5}  {'瞬态油耗':>8}  {'累计':>7}")
    print(f"{'s':>6}  {'km/h':>5}  {'km/h':>5}  {'%':>5}  {'':>3}  "
          f"{'rpm':>6}  {'%':>5}  {'g/kWh':>5}  {'L/100km':>8}  {'L':>7}")
    print("-" * 95)

    idx = 0
    last_print = -1.0
    steady_last_speed = -1  # 稳态估算只在新目标车速变化时计算一次

    for step in range(steps):
        sim_time = step * dt
        target_speed = targets[min(step, len(targets) - 1)]
        target_kmh = target_speed * 3.6

        # ---- 驾驶员模型 (P 控制器) ----
        speed_error = target_speed - speed
        if speed_error > 0.1:
            throttle = min(1.0, 0.15 * speed_error + 0.05)  # 加速
            brake = 0.0
        elif speed_error < -0.1:
            throttle = 0.0
            brake = min(1.0, -0.2 * speed_error)            # 减速
        else:
            if target_speed < 0.5 and speed < 0.5:
                # 停车：完全收油
                throttle = 0.0
                brake = 0.3 if speed > 0.05 else 0.0
            else:
                # 巡航：维持平衡油门
                resistance = calc_resistance(vehicle, max(speed, 0.1))
                cruise_torque = resistance * vehicle.wheel_radius
                gear = vehicle.select_gear(speed * 3.6)
                if gear > 0:
                    total_ratio = vehicle.gear_ratios[gear - 1] * vehicle.final_drive
                    engine_torque_needed = cruise_torque / (total_ratio * vehicle.trans_efficiency)
                    throttle = min(1.0, engine_torque_needed / vehicle.max_torque + 0.02)
                else:
                    throttle = 0.02
                brake = 0.0

        # ---- 车辆动力学 ----
        if throttle > 0.05 and speed < 1:
            gear = 1  # 起步强制 1 档
        else:
            gear = vehicle.select_gear(speed * 3.6)
        if gear > 0:
            total_ratio = vehicle.gear_ratios[gear - 1] * vehicle.final_drive
            engine_rpm = max(vehicle.idle_rpm,
                             speed / (2 * math.pi * vehicle.wheel_radius) * total_ratio * 60)
            resistance = calc_resistance(vehicle, max(speed, 0.1))
            engine_torque = throttle * vehicle.max_torque
            wheel_torque = engine_torque * total_ratio * vehicle.trans_efficiency
            wheel_force = wheel_torque / vehicle.wheel_radius

            # 制动力
            if brake > 0:
                brake_force = brake * vehicle.mass * 9.8 * 0.8  # 最大减速度 0.8g
                wheel_force -= brake_force

            net_force = wheel_force - resistance
            acceleration = net_force / vehicle.mass
        else:
            engine_rpm = vehicle.idle_rpm
            acceleration = 0
            if brake > 0:
                acceleration = -brake * 9.8 * 0.8

        # 更新速度
        speed = max(0, speed + acceleration * dt)
        distance += speed * dt

        # ---- 瞬态油耗计算 ----
        if gear > 0 and throttle > 0.01:
            load_ratio = min(1.0, engine_torque / vehicle.max_torque)
            bsfc = _interpolate_bsfc(engine_rpm, max(0.01, load_ratio), vehicle.fuel_type)

            # 加速加浓修正：加速度越大，喷油越浓
            if acceleration > 0.1:
                enrich_factor = 1.0 + min(0.35, acceleration * 0.5)
                bsfc *= enrich_factor

            engine_power_kw = engine_torque * engine_rpm * 2 * math.pi / 60 / 1000
            fuel_mass_rate = bsfc * engine_power_kw / 3600  # g/s
            fuel_vol_rate = fuel_mass_rate / vehicle.fuel_density  # L/s
            total_fuel_L += fuel_vol_rate * dt

            # 瞬时百公里油耗
            if speed > 0.1:
                inst_l100 = fuel_vol_rate * (360000 / (speed * 3.6))
            else:
                inst_l100 = 0
        else:
            # 减速断油 (DFCO)：收油门且转速高于怠速 → 断油
            if engine_rpm > vehicle.idle_rpm + 300 and throttle < 0.01 and speed > 1:
                bsfc = 0
                inst_l100 = 0
            else:
                # 怠速油耗
                bsfc = _interpolate_bsfc(vehicle.idle_rpm, 0.05, vehicle.fuel_type)
                idle_power = vehicle.idle_rpm * vehicle.max_torque * 0.05 * 2 * math.pi / 60 / 1000
                fuel_rate = bsfc * idle_power / 3600 / vehicle.fuel_density
                total_fuel_L += fuel_rate * dt
                inst_l100 = 99.9 if speed < 0.5 else fuel_rate * (360000 / (speed * 3.6))

        # ---- 稳态估算（仅目标车速变化时记录一次 BSFC 查表值） ----
        if abs(target_kmh - steady_last_speed) > 2:
            steady_fuel_L += calc_fuel_consumption(vehicle, target_kmh, 0)  # 先不做累计，只做参考
            steady_last_speed = target_kmh

        # ---- 每秒打印 ----
        if sim_time - last_print >= 1.0:
            print(f"{sim_time:5.0f}s  {target_kmh:4.0f}   {speed*3.6:4.0f}   "
                  f"{throttle*100:4.0f}%  {gear:>2}档  "
                  f"{engine_rpm:5.0f}  {engine_torque/vehicle.max_torque*100 if gear>0 and throttle>0.01 else 0:4.0f}%  "
                  f"{bsfc if gear>0 else 580:4.0f}  "
                  f"{inst_l100:7.1f}  {total_fuel_L:6.3f}")
            last_print = sim_time

    # 稳态估算：按每个阶段车速巡航的油耗求和
    steady_total = 0
    for phase_name, duration, target_kmh in cycle:
        if target_kmh > 0:
            seg_dist = target_kmh / 3.6 * duration / 1000  # km
            steady_total += calc_fuel_consumption(vehicle, target_kmh, seg_dist)

    avg_L100 = total_fuel_L / (distance / 100000) if distance > 0 else 0
    print(f"\n结果: 总油耗 {total_fuel_L:.3f}L | 总里程 {distance:.0f}m | 平均 {avg_L100:.1f} L/100km")
    print(f"      稳态估算: {steady_total:.3f}L (仅算各阶段匀速巡航) | 瞬态比稳态多 {total_fuel_L-steady_total:.3f}L")
    return total_fuel_L, distance, avg_L100, steady_total


# ============================================================
# 7. 跟车模型（交通工程核心）
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

    # 练习 3：稳态油耗对比（BSFC 万有特性模型）
    show_fuel_table()

    # 练习 4：瞬态油耗仿真（城市工况 — 稳态 vs 瞬态对比）
    simulate_transient_cycle(car_sedan)

    # 练习 5：跟车模型（交通流理论核心）
    car_following_simulation()

    print("\n提示: 改参数试试 — 把路面摩擦系数从 0.7 改成 0.3（雨天）看制动距离变化")
