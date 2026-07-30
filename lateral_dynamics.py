# -*- coding: utf-8 -*-
"""
横向动力学 —— 自行车模型（Bicycle Model）
从直线运动扩展到平面转向：侧偏角、横摆角速度、不足/过度转向
"""

import math


def calc_slip_angles(vehicle, vx_ms, vy_ms, yaw_rate, steer_angle_rad):
    """前后轮侧偏角 αf = (vy+a·r)/vx - δ, αr = (vy-b·r)/vx (rad)"""
    a = vehicle.cg_to_front
    b = vehicle.cg_to_rear
    alpha_f = (vy_ms + a * yaw_rate) / vx_ms - steer_angle_rad
    alpha_r = (vy_ms - b * yaw_rate) / vx_ms
    return alpha_f, alpha_r


def calc_cornering_forces(vehicle, alpha_f, alpha_r):
    """线性轮胎模型: Fy = -C × α (N)"""
    Fyf = -vehicle.cornering_stiffness_f * alpha_f
    Fyr = -vehicle.cornering_stiffness_r * alpha_r
    return Fyf, Fyr


def calc_understeer_gradient(vehicle):
    """不足转向梯度 Kus = Wf/Cf - Wr/Cr (rad/g, deg/g)"""
    m = vehicle.mass
    a = vehicle.cg_to_front
    b = vehicle.cg_to_rear
    L = vehicle.wheelbase
    Cf = vehicle.cornering_stiffness_f
    Cr = vehicle.cornering_stiffness_r

    Wf = m * 9.8 * b / L   # 前轴载荷（N）
    Wr = m * 9.8 * a / L   # 后轴载荷（N）

    kus_rad_per_g = Wf / Cf - Wr / Cr          # rad/g
    kus_deg_per_g = kus_rad_per_g * 180 / math.pi  # deg/g
    return kus_rad_per_g, kus_deg_per_g


def calc_characteristic_speed(vehicle):
    """计算不足转向特征车速（km/h），仅对不足转向有效"""
    _, kus_deg = calc_understeer_gradient(vehicle)
    if kus_deg <= 0:
        return float("inf")
    L = vehicle.wheelbase
    # v_char = sqrt(g·L / Kus)  where Kus in rad/g
    kus_rad, _ = calc_understeer_gradient(vehicle)
    v_char_ms = math.sqrt(9.8 * L / kus_rad)
    return v_char_ms * 3.6


def calc_critical_speed(vehicle):
    """计算过度转向临界车速（km/h），仅对过度转向有效

    超过此车速，车辆将失稳（横摆角速度趋于无穷）
    """
    _, kus_deg = calc_understeer_gradient(vehicle)
    if kus_deg >= 0:
        return float("inf")
    L = vehicle.wheelbase
    kus_rad, _ = calc_understeer_gradient(vehicle)
    v_crit_ms = math.sqrt(-9.8 * L / kus_rad)
    return v_crit_ms * 3.6


def calc_steady_state_cornering(vehicle, vx_kmh, steer_angle_deg):
    """稳态转向响应（定圆/定速）"""
    vx = vx_kmh / 3.6
    delta = math.radians(steer_angle_deg)
    L = vehicle.wheelbase
    kus_rad, kus_deg = calc_understeer_gradient(vehicle)

    # 稳态横摆角速度
    r = vx / (L + kus_rad * vx ** 2 / 9.8) * delta  # rad/s

    # 侧向加速度
    ay = vx * r  # m/s²

    # 转弯半径
    curvature = r / vx  # 1/m
    radius = 1 / curvature if curvature > 1e-9 else float("inf")

    return {
        "speed_kmh": vx_kmh,
        "steer_deg": steer_angle_deg,
        "yaw_rate_deg_s": math.degrees(r),
        "lateral_acc_g": ay / 9.8,
        "turn_radius_m": radius,
        "kus_deg_per_g": kus_deg,
    }


def simulate_step_steer(vehicle, vx_kmh, steer_angle_deg, duration_s=5, dt=0.01):
    """阶跃转向瞬态响应：给定车速和方向盘转角，仿真横摆响应

    使用 2-DOF 线性自行车模型，欧拉积分
    状态变量: [vy, r]（侧向速度、横摆角速度）
    """
    vx = vx_kmh / 3.6
    delta = math.radians(steer_angle_deg)
    m = vehicle.mass
    Iz = vehicle.yaw_inertia
    a = vehicle.cg_to_front
    b = vehicle.cg_to_rear
    Cf = vehicle.cornering_stiffness_f
    Cr = vehicle.cornering_stiffness_r

    # 初始状态
    vy = 0.0
    r = 0.0

    history = []
    t = 0.0
    while t <= duration_s:
        # 前后轮侧偏角
        alpha_f = (vy + a * r) / vx - delta if vx > 0 else 0
        alpha_r = (vy - b * r) / vx if vx > 0 else 0

        # 侧向力
        Fyf = -Cf * alpha_f
        Fyr = -Cr * alpha_r

        # 状态方程
        dvy = (Fyf + Fyr) / m - vx * r
        dr = (a * Fyf - b * Fyr) / Iz

        history.append((t, vy, r, math.degrees(r), vx * r / 9.8))

        # 欧拉积分
        vy += dvy * dt
        r += dr * dt
        t += dt

    return history


def _classify_steer(kus_deg_per_g):
    """按不足转向梯度分类"""
    if kus_deg_per_g > 0.5:
        return "不足转向（稳定）"
    elif kus_deg_per_g < -0.5:
        return "过度转向（不稳定）"
    else:
        return "中性转向"


def show_lateral_analysis(vehicle):
    """展示横向动力学综合分析"""
    kus_rad, kus_deg = calc_understeer_gradient(vehicle)
    steer_type = _classify_steer(kus_deg)
    v_char = calc_characteristic_speed(vehicle)
    v_crit = calc_critical_speed(vehicle)

    print(f"\n{'='*60}")
    print(f"{vehicle.name}  横向动力学分析")
    print(f"{'='*60}")
    print(f"  轴距:             {vehicle.wheelbase:.2f} m")
    print(f"  质心-前轴:        {vehicle.cg_to_front:.2f} m ({vehicle.cg_to_front/vehicle.wheelbase*100:.0f}%)")
    print(f"  质心-后轴:        {vehicle.cg_to_rear:.2f} m ({vehicle.cg_to_rear/vehicle.wheelbase*100:.0f}%)")
    print(f"  前轴侧偏刚度:     {vehicle.cornering_stiffness_f:.0f} N/rad")
    print(f"  后轴侧偏刚度:     {vehicle.cornering_stiffness_r:.0f} N/rad")
    print(f"  横摆惯量 Iz:      {vehicle.yaw_inertia:.0f} kg·m²")
    print(f"{'-'*40}")
    print(f"  不足转向梯度 Kus: {kus_deg:+.3f} deg/g  →  {steer_type}")
    if kus_deg > 0:
        print(f"  特征车速:         {v_char:.1f} km/h（横摆增益峰值点）")
    elif kus_deg < 0:
        print(f"  临界车速:         {v_crit:.1f} km/h（超过即失稳！）")


def show_steady_cornering_table(vehicle):
    """不同车速下稳态转向响应对比表"""
    print(f"\n{'='*75}")
    print(f"{vehicle.name}  稳态转向响应（方向盘转角 3°）")
    print(f"{'='*75}")
    print(f"{'车速':>6}  {'横摆角速度':>10}  {'侧向加速度':>10}  {'转弯半径':>10}  {'不足转向梯度':>12}")
    print(f"{'km/h':>6}  {'deg/s':>10}  {'g':>10}  {'m':>10}  {'deg/g':>12}")
    print("-" * 75)

    for v in [30, 60, 90, 120, 150]:
        result = calc_steady_state_cornering(vehicle, v, steer_angle_deg=3)
        print(f"{v:6.0f}  {result['yaw_rate_deg_s']:10.2f}  "
              f"{result['lateral_acc_g']:10.3f}  "
              f"{result['turn_radius_m']:10.1f}  "
              f"{result['kus_deg_per_g']:+12.3f}")


def show_step_steer_response(vehicle, vx_kmh=80, steer_deg=3):
    """阶跃转向瞬态响应"""
    history = simulate_step_steer(vehicle, vx_kmh, steer_deg, duration_s=3)

    print(f"\n{'='*70}")
    print(f"{vehicle.name}  阶跃转向瞬态响应（{vx_kmh}km/h, 方向盘{steer_deg}°）")
    print(f"{'='*70}")
    print(f"{'时间(s)':>8}  {'vy(m/s)':>10}  {'r(deg/s)':>10}  {'ay(g)':>8}")
    print("-" * 50)

    # 打印每秒的关键帧
    for i in range(0, len(history), 100):  # dt=0.01, 每100步 = 1秒
        t, vy, _, r_deg, ay_g = history[i]
        print(f"{t:8.1f}  {vy:10.3f}  {r_deg:10.2f}  {ay_g:8.3f}")

    # 稳态值
    result = calc_steady_state_cornering(vehicle, vx_kmh, steer_deg)
    final_t, final_vy, _, final_r, final_ay = history[-1]
    print(f"\n  稳态理论值:  r={result['yaw_rate_deg_s']:.2f} deg/s,  ay={result['lateral_acc_g']:.3f} g")
    print(f"  仿真终值:    r={final_r:.2f} deg/s,  ay={final_ay:.3f} g")
