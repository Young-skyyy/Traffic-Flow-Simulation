# -*- coding: utf-8 -*-
"""
横向动力学 —— 自行车模型（Bicycle Model）
从直线运动扩展到平面转向：侧偏角、横摆角速度、不足/过度转向
"""

from __future__ import annotations

import math

from _constants import G, KMH_TO_MS
from vehicle import Vehicle


def calc_slip_angles(vehicle: Vehicle, vx_ms: float, vy_ms: float,
                     yaw_rate: float, steer_angle_rad: float) -> tuple[float, float]:
    """前后轮侧偏角 αf = (vy+a·r)/vx - δ, αr = (vy-b·r)/vx (rad)"""
    a = vehicle.cg_to_front
    b = vehicle.cg_to_rear
    alpha_f = (vy_ms + a * yaw_rate) / vx_ms - steer_angle_rad
    alpha_r = (vy_ms - b * yaw_rate) / vx_ms
    return alpha_f, alpha_r


def calc_cornering_forces(vehicle: Vehicle, alpha_f: float,
                          alpha_r: float) -> tuple[float, float]:
    """线性轮胎模型: Fy = -C × α (N)"""
    Fyf = -vehicle.cornering_stiffness_f * alpha_f
    Fyr = -vehicle.cornering_stiffness_r * alpha_r
    return Fyf, Fyr


def calc_understeer_gradient(vehicle: Vehicle) -> tuple[float, float]:
    """不足转向梯度 Kus = Wf/Cf - Wr/Cr (rad/g, deg/g)"""
    m = vehicle.mass
    a = vehicle.cg_to_front
    b = vehicle.cg_to_rear
    L = vehicle.wheelbase
    Cf = vehicle.cornering_stiffness_f
    Cr = vehicle.cornering_stiffness_r

    Wf = m * G * b / L   # 前轴载荷（N）
    Wr = m * G * a / L   # 后轴载荷（N）

    kus_rad_per_g = Wf / Cf - Wr / Cr          # rad/g
    kus_deg_per_g = kus_rad_per_g * 180 / math.pi  # deg/g
    return kus_rad_per_g, kus_deg_per_g


def calc_characteristic_speed(vehicle: Vehicle) -> float:
    """计算不足转向特征车速（km/h），仅对不足转向有效"""
    _, kus_deg = calc_understeer_gradient(vehicle)
    if kus_deg <= 0:
        return float("inf")
    L = vehicle.wheelbase
    # v_char = sqrt(g·L / Kus)  where Kus in rad/g
    kus_rad, _ = calc_understeer_gradient(vehicle)
    v_char_ms = math.sqrt(G * L / kus_rad)
    return v_char_ms / KMH_TO_MS


def calc_critical_speed(vehicle: Vehicle) -> float:
    """计算过度转向临界车速（km/h），仅对过度转向有效

    超过此车速，车辆将失稳（横摆角速度趋于无穷）
    """
    _, kus_deg = calc_understeer_gradient(vehicle)
    if kus_deg >= 0:
        return float("inf")
    L = vehicle.wheelbase
    kus_rad, _ = calc_understeer_gradient(vehicle)
    v_crit_ms = math.sqrt(-G * L / kus_rad)
    return v_crit_ms / KMH_TO_MS


def calc_steady_state_cornering(vehicle: Vehicle, vx_kmh: float,
                                steer_angle_deg: float) -> dict:
    """稳态转向响应（定圆/定速）"""
    vx = vx_kmh * KMH_TO_MS
    delta = math.radians(steer_angle_deg)
    L = vehicle.wheelbase
    kus_rad, kus_deg = calc_understeer_gradient(vehicle)

    # 稳态横摆角速度
    r = vx / (L + kus_rad * vx ** 2 / G) * delta  # rad/s

    # 侧向加速度
    ay = vx * r  # m/s²

    # 转弯半径
    curvature = r / vx  # 1/m
    radius = 1 / curvature if curvature > 1e-9 else float("inf")

    return {
        "speed_kmh": vx_kmh,
        "steer_deg": steer_angle_deg,
        "yaw_rate_deg_s": math.degrees(r),
        "lateral_acc_g": ay / G,
        "turn_radius_m": radius,
        "kus_deg_per_g": kus_deg,
    }


def simulate_step_steer(vehicle: Vehicle, vx_kmh: float,
                        steer_angle_deg: float, duration_s: float = 5,
                        dt: float = 0.01) -> list[tuple[float, float, float, float, float]]:
    """阶跃转向瞬态响应：给定车速和方向盘转角，仿真横摆响应

    使用 2-DOF 线性自行车模型，欧拉积分
    状态变量: [vy, r]（侧向速度、横摆角速度）

    Returns:
        每个元素为 (t, vy, r_rad, r_deg, ay_g)
    """
    vx = vx_kmh * KMH_TO_MS
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

    history: list[tuple[float, float, float, float, float]] = []
    t = 0.0
    while t <= duration_s:
        # 前后轮侧偏角
        alpha_f = (vy + a * r) / vx - delta if vx > 0 else 0.0
        alpha_r = (vy - b * r) / vx if vx > 0 else 0.0

        # 侧向力
        Fyf = -Cf * alpha_f
        Fyr = -Cr * alpha_r

        # 状态方程
        dvy = (Fyf + Fyr) / m - vx * r
        dr = (a * Fyf - b * Fyr) / Iz

        history.append((t, vy, r, math.degrees(r), vx * r / G))

        # 欧拉积分
        vy += dvy * dt
        r += dr * dt
        t += dt

    return history


def _classify_steer(kus_deg_per_g: float) -> str:
    """按不足转向梯度分类"""
    if kus_deg_per_g > 0.5:
        return "不足转向（稳定）"
    elif kus_deg_per_g < -0.5:
        return "过度转向（不稳定）"
    else:
        return "中性转向"


def analyze_lateral(vehicle: Vehicle) -> dict:
    """横向动力学综合分析，返回结构化数据。"""
    kus_rad, kus_deg = calc_understeer_gradient(vehicle)
    steer_type = _classify_steer(kus_deg)
    v_char = calc_characteristic_speed(vehicle)
    v_crit = calc_critical_speed(vehicle)

    return {
        "vehicle_name": vehicle.name,
        "wheelbase_m": vehicle.wheelbase,
        "cg_to_front_m": vehicle.cg_to_front,
        "cg_to_rear_m": vehicle.cg_to_rear,
        "cg_front_pct": vehicle.cg_to_front / vehicle.wheelbase * 100,
        "cg_rear_pct": vehicle.cg_to_rear / vehicle.wheelbase * 100,
        "cornering_stiffness_f": vehicle.cornering_stiffness_f,
        "cornering_stiffness_r": vehicle.cornering_stiffness_r,
        "yaw_inertia": vehicle.yaw_inertia,
        "kus_rad_per_g": kus_rad,
        "kus_deg_per_g": kus_deg,
        "steer_type": steer_type,
        "characteristic_speed_kmh": v_char,
        "critical_speed_kmh": v_crit,
    }


def calc_steady_cornering_table(vehicle: Vehicle) -> list[dict]:
    """不同车速下稳态转向响应对比表，返回结构化数据。"""
    results: list[dict] = []
    for v in [30, 60, 90, 120, 150]:
        result = calc_steady_state_cornering(vehicle, v, steer_angle_deg=3)
        results.append(result)
    return results


def calc_step_steer_response(vehicle: Vehicle, vx_kmh: float = 80,
                             steer_deg: float = 3) -> dict:
    """阶跃转向瞬态响应，返回结构化数据。"""
    history = simulate_step_steer(vehicle, vx_kmh, steer_deg, duration_s=3)
    result = calc_steady_state_cornering(vehicle, vx_kmh, steer_deg)
    _, _, _, final_r, final_ay = history[-1]

    return {
        "history": history,
        "steady_yaw_rate": result["yaw_rate_deg_s"],
        "steady_lateral_acc": result["lateral_acc_g"],
        "final_yaw_rate": final_r,
        "final_lateral_acc": final_ay,
    }
