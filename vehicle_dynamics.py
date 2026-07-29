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
    基于 BSFC 万有特性 map 计算油耗（取整版，用于展示）。
    """
    return round(_calc_l100_raw(vehicle, speed_kmh) * distance_km / 100, 2)


def _calc_l100_raw(vehicle, speed_kmh):
    """返回 L/100km 的精确值（不取整，供内部累加使用）"""
    gear = vehicle.select_gear(speed_kmh)
    if gear == 0:
        return 0.0
    speed_ms = speed_kmh / 3.6
    gear_ratio = vehicle.gear_ratios[gear - 1]
    total_ratio = gear_ratio * vehicle.final_drive
    wheel_rps = speed_ms / (2 * math.pi * vehicle.wheel_radius)
    engine_rpm = wheel_rps * total_ratio * 60
    resistance = calc_resistance(vehicle, speed_ms)
    wheel_torque = resistance * vehicle.wheel_radius
    engine_torque = wheel_torque / (total_ratio * vehicle.trans_efficiency)
    load_ratio = max(0.01, min(1.0, engine_torque / vehicle.max_torque))
    bsfc = _interpolate_bsfc(engine_rpm, load_ratio, vehicle.fuel_type)
    engine_power_kw = engine_torque * engine_rpm * 2 * math.pi / 60 / 1000
    fuel_mass_rate = bsfc * engine_power_kw / 3600  # g/s
    fuel_vol_rate = fuel_mass_rate / vehicle.fuel_density  # L/s
    return fuel_vol_rate * (360000 / speed_kmh)  # L/100km


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


def plot_bsfc_map(save_path=None):
    """
    绘制汽油机 BSFC 万有特性等高线图。

    横轴: 发动机转速 (RPM)
    纵轴: 扭矩负荷比
    等高线: BSFC (g/kWh)，越低越省油

    面试时打开这张图，直接指给面试官看：
      - 中间那片"岛"（~233 g/kWh）是最优区
      - 左下角（低速低负荷）和右上角（高速满负荷）都是费油区
      - 你的仿真模型每一步就是从车速推到这张图上的某个点
    """
    import matplotlib
    matplotlib.use("Agg")  # 非交互式后端，避免弹窗报错
    import matplotlib.pyplot as plt
    import numpy as np

    # 设置中文字体（Windows 用 SimHei / Microsoft YaHei）
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

    rpm = np.array(_BSFC_RPM_GRID)
    load = np.array(_BSFC_LOAD_GRID) * 100  # 转为百分比
    bsfc_data = np.array(_BSFC_GASOLINE)
    R, L = np.meshgrid(rpm, load)

    fig, ax = plt.subplots(figsize=(10, 7))

    # 填充等高线
    levels = [220, 240, 260, 280, 300, 330, 370, 420, 500]
    cs = ax.contourf(R, L, bsfc_data, levels=levels, cmap="RdYlGn_r", alpha=0.85)
    cbar = fig.colorbar(cs, ax=ax, label="BSFC (g/kWh)", shrink=0.85)
    cbar.ax.tick_params(labelsize=9)

    # 标注线
    ax.contour(R, L, bsfc_data, levels=levels, colors="black", linewidths=0.3)

    # 标注最优区（找数组中最小值位置）
    min_flat = np.argmin(bsfc_data)
    min_row, min_col = min_flat // len(rpm), min_flat % len(rpm)
    ax.annotate(f"最优 {bsfc_data[min_row, min_col]:.0f} g/kWh",
                xy=(rpm[min_col], load[min_row]),
                xytext=(rpm[min_col] + 500, load[min_row] + 8),
                fontsize=10, color="darkgreen", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="darkgreen"))

    # 标注几个典型工况点
    examples = [
        (800, 5, "怠速", "red"),
        (2500, 75, "经济巡航", "darkgreen"),
        (5500, 90, "全油门加速", "darkred"),
    ]
    for r, l, label, color in examples:
        ax.plot(r, l, "o", color=color, markersize=8)
        ax.annotate(label, (r + 100, l + 3), fontsize=9, color=color, fontweight="bold")

    ax.set_xlabel("发动机转速 (RPM)", fontsize=11)
    ax.set_ylabel("扭矩负荷比 (%)", fontsize=11)
    ax.set_title("发动机 BSFC 万有特性 Map (2.0L 汽油机)", fontsize=13, fontweight="bold")

    # 标注左上角"高效率"和右下角"低效率"
    ax.text(6500, 95, "高效率", fontsize=9, color="green", ha="right")
    ax.text(6500, 10, "高油耗", fontsize=9, color="red", ha="right")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"BSFC 热力图已保存: {save_path}")
    else:
        plt.savefig("bsfc_map.png", dpi=150)
        print("BSFC 热力图已保存: bsfc_map.png")
    plt.close()


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

# ---- WLTC Class 3 标准循环工况 ----
# 全球统一轻型车测试循环，4 阶段共 1800 秒，23.27 km
# 格式: [(时间s, 车速km/h), ...] 关键拐点，内部线性插值生成 1Hz 速度曲线

_WLTC_WAYPOINTS = [
    # === Phase 1: Low (0-589s, 市区低速, avg 25.7 km/h, max 56.5) ===
    (0,0),(11,0),(15,12.7),(23,12.7),(28,0),(33,0),(38,18.3),(48,18.3),(51,0),
    (56,0),(61,24.1),(66,24.1),(71,0),(76,0),(81,28.5),(96,28.5),(101,12.5),
    (106,0),(111,0),(116,32.5),(121,0),(126,0),(131,32.2),(141,32.2),(146,0),
    (151,0),(156,35.8),(176,35.8),(181,27.6),(186,12.6),(191,0),(196,0),
    (201,35.6),(216,35.6),(221,0),(226,0),(231,38.4),(251,38.4),(256,29.8),
    (261,19.7),(266,0),(271,0),(276,40.3),(296,40.3),(301,32.1),(306,22.1),
    (311,0),(316,0),(321,41.2),(341,41.2),(346,33.0),(351,25.1),(356,0),
    (361,0),(366,41.8),(381,41.8),(386,31.4),(391,21.2),(396,0),(401,0),
    (406,44.1),(416,44.1),(421,32.9),(426,21.5),(431,0),(436,0),(441,45.5),
    (456,45.5),(461,34.7),(466,23.1),(471,0),(476,0),(481,47.2),(496,47.2),
    (501,35.8),(506,24.3),(511,0),(516,0),(521,50.9),(531,50.9),(536,37.9),
    (541,26.3),(546,0),(551,0),(556,52.4),(571,52.4),(576,40.0),(581,29.1),
    (586,0),
    # === Phase 2: Medium (590-1022s, 市郊中速, avg 44.5 km/h, max 76.6) ===
    (590,0),(593,0),(600,49.0),(615,49.0),(620,38.5),(625,28.1),(630,0),
    (635,0),(642,52.1),(652,52.1),(657,41.3),(662,31.1),(667,0),(672,0),
    (679,55.4),(694,55.4),(699,44.0),(704,33.8),(709,0),(714,0),(721,58.6),
    (736,58.6),(741,46.0),(746,35.4),(751,0),(756,0),(763,61.0),(783,61.0),
    (788,48.5),(793,37.6),(798,0),(803,0),(810,63.5),(830,63.5),(835,50.1),
    (840,39.5),(845,0),(850,0),(857,65.4),(877,65.4),(882,52.3),(887,41.1),
    (892,0),(897,0),(904,67.0),(924,67.0),(929,52.9),(934,42.0),(939,0),
    (944,0),(951,68.8),(971,68.8),(976,54.2),(981,43.5),(986,0),(991,0),
    (998,70.3),(1018,70.3),(1022,0),
    # === Phase 3: High (1023-1477s, 高速, avg 60.7 km/h, max 97.4) ===
    (1023,0),(1026,0),(1035,75.0),(1055,75.0),(1060,60.1),(1065,48.1),
    (1070,36.0),(1075,0),(1080,0),(1089,71.0),(1109,71.0),(1114,56.2),
    (1119,44.8),(1124,33.2),(1129,0),(1134,0),(1143,77.5),(1163,77.5),
    (1168,61.0),(1173,49.0),(1178,36.8),(1183,0),(1188,0),(1197,83.0),
    (1217,83.0),(1222,65.8),(1227,53.1),(1232,40.1),(1237,0),(1242,0),
    (1251,88.5),(1271,88.5),(1276,69.9),(1281,56.8),(1286,43.2),(1291,0),
    (1296,0),(1305,92.0),(1325,92.0),(1330,73.3),(1335,59.0),(1340,45.2),
    (1345,0),(1350,0),(1359,95.5),(1379,95.5),(1384,76.0),(1389,61.2),
    (1394,46.8),(1399,0),(1404,0),(1413,97.0),(1433,97.0),(1438,77.0),
    (1443,62.3),(1448,48.0),(1453,0),(1458,0),(1467,97.4),(1477,97.4),
    # === Phase 4: Extra High (1478-1800s, 超高速, avg 94.1 km/h, max 131.3) ===
    (1478,97.4),(1481,0),(1484,0),(1494,104.0),(1514,104.0),(1519,83.0),
    (1524,67.2),(1529,51.1),(1534,0),(1537,0),(1547,110.5),(1566,110.5),
    (1571,88.5),(1576,71.2),(1581,53.8),(1586,0),(1589,0),(1599,118.0),
    (1617,118.0),(1622,94.5),(1627,76.3),(1632,57.8),(1637,0),(1640,0),
    (1650,124.0),(1670,124.0),(1675,99.2),(1680,80.3),(1685,61.5),(1690,0),
    (1693,0),(1703,129.5),(1723,129.5),(1728,103.5),(1733,83.6),(1738,63.5),
    (1743,0),(1746,0),(1756,131.3),(1776,131.3),(1781,105.0),(1786,85.0),
    (1791,65.2),(1796,45.0),(1800,0),
]
_WLTC_DURATION = 1800  # 秒


def get_wltc_profile():
    """从关键拐点线性插值生成 WLTC 1Hz 速度曲线 (km/h), 返回 list[float] len=1801"""
    profile = [0.0] * (_WLTC_DURATION + 1)
    idx = 0
    for i in range(len(_WLTC_WAYPOINTS) - 1):
        t0, v0 = _WLTC_WAYPOINTS[i]
        t1, v1 = _WLTC_WAYPOINTS[i + 1]
        duration = t1 - t0
        for dt in range(duration + 1):
            if idx <= _WLTC_DURATION:
                ratio = dt / duration if duration > 0 else 1.0
                profile[idx] = round(v0 + (v1 - v0) * ratio, 1)
                idx += 1
    return profile


def show_wltc_summary():
    """打印 WLTC 工况概要"""
    profile = get_wltc_profile()
    phases = [
        ("Phase 1 (Low)",  0, 589,  25.7, 56.5),
        ("Phase 2 (Medium)",  590, 1022, 44.5, 76.6),
        ("Phase 3 (High)",  1023, 1477, 60.7, 97.4),
        ("Phase 4 (Extra High)",  1478, 1800, 94.1, 131.3),
    ]
    print(f"\nWLTC Class 3 标准循环工况 (共 {_WLTC_DURATION}s, ~23.27km)")
    print(f"{'':<22} {'时间':>8} {'最高':>6} {'耗时':>6} {'距离':>8}")
    print("-" * 52)
    total_dist = 0
    for name, start, end, _, _ in phases:
        seg = profile[start:end + 1]
        max_v = max(seg)
        dist_km = sum(v / 3.6 for v in seg) / 1000  # 每1秒积分
        total_dist += dist_km
        print(f"  {name:<20} {start:>4}-{end:<4}s  {max_v:>5.0f}  {end-start:>4}s  {dist_km:>7.2f}km")
    print(f"  {'总计':<20} {'0-1800s':>9}  {max(profile):>5.0f}  1800s  {total_dist:>7.2f}km")
    return profile


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


def simulate_wltc(vehicle, dt=0.2):
    """
    运行 WLTC Class 3 完整循环（1800 秒）并对比瞬态 vs 稳态油耗。

    因周期长达 1800s，每 30 秒打印一次状态快照，
    并对加速/巡航/减速/怠速阶段的燃油分配做分析。
    """

    def format_phase_desc(start_s, end_s, profile):
        if start_s >= len(profile):
            return "", 0
        seg = profile[start_s:min(end_s + 1, len(profile))]
        avg_v = sum(seg) / len(seg) if seg else 0
        max_v = max(seg) if seg else 0
        labels = [(589,"Low"),(1022,"Med"),(1477,"Hi"),(1800,"ExHi")]
        phase_name = next((n for t,n in labels if end_s <= t), "")
        return f"{phase_name}", max_v

    wltc = get_wltc_profile()
    total_steps = int(_WLTC_DURATION / dt)
    print_interval = 30  # 每 30 秒打印

    speed = 0.0
    distance = 0.0
    total_fuel_L = 0.0
    gear = 0
    engine_rpm = vehicle.idle_rpm

    # 分段统计
    phase_fuel = {"Low": 0.0, "Med": 0.0, "Hi": 0.0, "ExHi": 0.0}
    phase_dist = {"Low": 0.0, "Med": 0.0, "Hi": 0.0, "ExHi": 0.0}
    accel_fuel = cruise_fuel = decel_fuel = idle_fuel = 0.0

    print(f"\n{'='*100}")
    print(f"  WLTC Class 3 瞬态仿真 — {vehicle.name} — 1800s 标准循环")
    print(f"{'='*100}")
    print(f"{'时间':>6}  {'目标':>5}  {'实际':>5}  {'油门':>5}  {'档位':>3}  "
          f"{'转速':>6}  {'BSFC':>5}  {'瞬时油耗':>8}  {'累计':>7}  {'阶段'}")
    print(f"{'s':>6}  {'km/h':>5}  {'km/h':>5}  {'%':>5}  {'':>3}  "
          f"{'rpm':>6}  {'g/kWh':>5}  {'L/100km':>8}  {'L':>7}")
    print("-" * 100)

    last_print = -print_interval
    throttle = 0.0
    brake = 0.0
    last_accel = 0.0

    for step in range(total_steps):
        sim_time = step * dt
        t_idx = int(sim_time)
        if t_idx >= len(wltc):
            break
        target_kmh = wltc[t_idx]
        target_speed = target_kmh / 3.6

        # ---- 驾驶员模型 ----
        speed_error = target_speed - speed
        if speed_error > 0.1:
            throttle = min(1.0, 0.15 * speed_error + 0.05)
            brake = 0.0
        elif speed_error < -0.1:
            throttle = 0.0
            brake = min(1.0, -0.2 * speed_error)
        else:
            if target_speed < 0.5 and speed < 0.5:
                throttle = 0.0
                brake = 0.3 if speed > 0.05 else 0.0
            else:
                resistance = calc_resistance(vehicle, max(speed, 0.1))
                cruise_tq = resistance * vehicle.wheel_radius
                g = vehicle.select_gear(speed * 3.6)
                if g > 0:
                    ratio = vehicle.gear_ratios[g - 1] * vehicle.final_drive
                    tq = cruise_tq / (ratio * vehicle.trans_efficiency)
                    throttle = min(1.0, tq / vehicle.max_torque + 0.02)
                else:
                    throttle = 0.02
                brake = 0.0

        # ---- 车辆动力学 ----
        if throttle > 0.05 and speed < 1:
            gear = 1
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
            if brake > 0:
                wheel_force -= brake * vehicle.mass * 9.8 * 0.8
            net_force = wheel_force - resistance
            acceleration = net_force / vehicle.mass
        else:
            engine_rpm = vehicle.idle_rpm
            acceleration = 0
            if brake > 0:
                acceleration = -brake * 9.8 * 0.8

        speed = max(0, speed + acceleration * dt)
        distance += speed * dt

        # ---- 瞬态油耗 ----
        inst_l100 = 0
        bsfc = 0
        if gear > 0 and throttle > 0.01:
            load_ratio = min(1.0, engine_torque / vehicle.max_torque)
            bsfc = _interpolate_bsfc(engine_rpm, max(0.01, load_ratio), vehicle.fuel_type)
            if acceleration > 0.1:
                bsfc *= 1.0 + min(0.35, acceleration * 0.5)
            power_kw = engine_torque * engine_rpm * 2 * math.pi / 60 / 1000
            fuel_rate = bsfc * power_kw / 3600 / vehicle.fuel_density
            total_fuel_L += fuel_rate * dt
            if speed > 0.1:
                inst_l100 = fuel_rate * (360000 / (speed * 3.6))

            # 工况分类统计
            if acceleration > 0.2:
                accel_fuel += fuel_rate * dt
            elif abs(speed_error) < 0.3:
                cruise_fuel += fuel_rate * dt
            else:
                decel_fuel += fuel_rate * dt  # 轻微减速但仍在供油
        else:
            if engine_rpm > vehicle.idle_rpm + 300 and throttle < 0.01 and speed > 1:
                bsfc = 0
                fuel_rate = 0.0
            else:
                bsfc = _interpolate_bsfc(vehicle.idle_rpm, 0.05, vehicle.fuel_type)
                idle_power = vehicle.idle_rpm * vehicle.max_torque * 0.05 * 2 * math.pi / 60 / 1000
                fuel_rate = bsfc * idle_power / 3600 / vehicle.fuel_density
                total_fuel_L += fuel_rate * dt
                idle_fuel += fuel_rate * dt
                inst_l100 = 99.9 if speed < 0.5 else fuel_rate * (360000 / (speed * 3.6))

        # 按阶段累计
        if t_idx < 590:
            phase_fuel["Low"] += fuel_rate * dt
            phase_dist["Low"] += speed * dt
        elif t_idx < 1023:
            phase_fuel["Med"] += fuel_rate * dt
            phase_dist["Med"] += speed * dt
        elif t_idx < 1478:
            phase_fuel["Hi"] += fuel_rate * dt
            phase_dist["Hi"] += speed * dt
        else:
            phase_fuel["ExHi"] += fuel_rate * dt
            phase_dist["ExHi"] += speed * dt

        last_accel = acceleration

        # 每 30 秒打印
        if sim_time - last_print >= print_interval:
            phase_label, _ = format_phase_desc(t_idx - 1, t_idx, wltc)
            print(f"{sim_time:5.0f}s  {target_kmh:4.0f}   {speed*3.6:4.0f}   "
                  f"{throttle*100:4.0f}%  {gear:>2}档  "
                  f"{engine_rpm:5.0f}  {bsfc:4.0f}  "
                  f"{inst_l100:7.1f}  {total_fuel_L:6.3f}  {phase_label}")
            last_print = sim_time

    # ---- 稳态估算（不经过 round，避免微距截断）----
    steady_total = 0
    for t in range(0, _WLTC_DURATION):
        v = wltc[t] if t < len(wltc) else 0
        if v > 0.5:
            l100 = _calc_l100_raw(vehicle, v)
            dist_km = v / 3600  # 1秒行驶的公里数
            steady_total += l100 * dist_km / 100

    avg_L100 = total_fuel_L / (distance / 100000) if distance > 0 else 0

    print(f"\n{'='*100}")
    print(f"  WLTC 仿真结果")
    print(f"{'='*100}")
    print(f"  总油耗: {total_fuel_L:.3f}L  |  总里程: {distance/1000:.2f}km  |  平均: {avg_L100:.1f} L/100km")
    if steady_total > 0:
        print(f"  稳态估算: {steady_total:.3f}L  |  瞬态比稳态多 {total_fuel_L-steady_total:.3f}L ({(total_fuel_L/steady_total-1)*100:+.0f}%)")
    else:
        print(f"  稳态估算: {steady_total:.3f}L")
    print(f"\n  各阶段油耗:")
    phase_names = [("Low (0-589s)", "Low"), ("Med (590-1022s)", "Med"),
                   ("Hi (1023-1477s)", "Hi"), ("ExHi (1478-1800s)", "ExHi")]
    for label, key in phase_names:
        d = phase_dist[key] / 1000
        l100 = phase_fuel[key] / (d / 100) if d > 0 else 0
        print(f"    {label:<18} {phase_fuel[key]:.3f}L  {d:.2f}km  {l100:.1f} L/100km")
    print(f"\n  工况分配: 加速 {accel_fuel:.3f}L | 巡航 {cruise_fuel:.3f}L | 减速 {decel_fuel:.3f}L | 怠速 {idle_fuel:.3f}L")
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

    # 练习 4：BSFC 万有特性热力图
    plot_bsfc_map()

    # 练习 4b：WLTC 标准循环瞬态仿真（耗时较长，注释掉按需运行）
    # show_wltc_summary()
    # simulate_wltc(car_sedan)

    # 练习 5：跟车模型（交通流理论核心）
    car_following_simulation()

    print("\n提示: 改参数试试 — 把路面摩擦系数从 0.7 改成 0.3（雨天）看制动距离变化")
