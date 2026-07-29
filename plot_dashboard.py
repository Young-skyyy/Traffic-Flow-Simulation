# -*- coding: utf-8 -*-
"""
面试展示仪表盘 —— BSFC 万有特性 + 横向动力学 四合一图
一张图展示：发动机效率、稳态转向、转弯半径、瞬态横摆响应
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import RectBivariateSpline

from bsfc import _BSFC_RPM_GRID, _BSFC_LOAD_GRID, _BSFC_GASOLINE
from vehicle import car_sedan
from lateral_dynamics import (
    calc_steady_state_cornering,
    simulate_step_steer,
)


def plot_dashboard(vehicle=None, save_path=None):
    """
    四合一仪表盘图：

    左上 ─ BSFC 万有特性 Map（发动机效率）
    右上 ─ 稳态转向响应（横摆角速度 + 侧向加速度 vs 车速）
    左下 ─ 转弯半径 vs 车速（不足转向可视化）
    右下 ─ 阶跃转向瞬态响应（横摆角速度随时间收敛）

    面试时可以逐张讲解：
      1. 你怎么从车速推到发动机工况点（BSFC 图上描点）
      2. 方向盘转角不变，车速越高转弯半径怎么变（不足转向）
      3. 突然打方向，车子多少秒"跟上"（瞬态响应）
    """
    if vehicle is None:
        vehicle = car_sedan

    # 中文字体
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig = plt.figure(figsize=(16, 11))
    fig.suptitle(f"{vehicle.name} — 动力总成 & 横向动力学 综合分析",
                 fontsize=16, fontweight="bold", y=0.98)

    # ==========================================
    # 左上：BSFC 万有特性 Map
    # ==========================================
    ax1 = fig.add_subplot(2, 2, 1)
    _draw_bsfc_panel(ax1)

    # ==========================================
    # 右上：稳态转向响应（双 Y 轴）
    # ==========================================
    ax2 = fig.add_subplot(2, 2, 2)
    _draw_steady_cornering_panel(ax2, vehicle)

    # ==========================================
    # 左下：转弯半径 vs 车速
    # ==========================================
    ax3 = fig.add_subplot(2, 2, 3)
    _draw_turn_radius_panel(ax3, vehicle)

    # ==========================================
    # 右下：阶跃转向瞬态响应
    # ==========================================
    ax4 = fig.add_subplot(2, 2, 4)
    _draw_step_steer_panel(ax4, vehicle)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    if save_path is None:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = f"dashboard_{timestamp}.png"

    plt.savefig(save_path, dpi=150)
    print(f"[仪表盘已保存] {save_path}")
    plt.close()


def _draw_bsfc_panel(ax):
    """左上：BSFC 万有特性等高线图"""
    rpm = np.array(_BSFC_RPM_GRID)
    load = np.array(_BSFC_LOAD_GRID) * 100
    bsfc_data = np.array(_BSFC_GASOLINE)

    spline = RectBivariateSpline(load, rpm, bsfc_data, kx=3, ky=3)
    rpm_fine = np.linspace(rpm[0], rpm[-1], 200)
    load_fine = np.linspace(load[0], load[-1], 150)
    R_fine, L_fine = np.meshgrid(rpm_fine, load_fine)
    bsfc_fine = spline(load_fine, rpm_fine)

    levels = [220, 240, 260, 280, 300, 330, 360, 400, 450, 500]
    cs = ax.contourf(R_fine, L_fine, bsfc_fine, levels=levels, cmap="RdYlGn_r", alpha=0.85)
    ax.contour(R_fine, L_fine, bsfc_fine, levels=levels, colors="black", linewidths=0.3)

    # 三个典型工况点
    points = [
        (800, 5, "怠速", "red"),
        (2500, 75, "经济巡航", "darkgreen"),
        (5500, 90, "全油门", "darkred"),
    ]
    for r, l, label, color in points:
        ax.plot(r, l, "o", color=color, markersize=10, markeredgecolor="white", markeredgewidth=1.5)
        ax.annotate(label, (r + 100, l + 3), fontsize=8, color=color, fontweight="bold")

    ax.set_xlabel("发动机转速 (RPM)")
    ax.set_ylabel("扭矩负荷比 (%)")
    ax.set_title("BSFC 万有特性 Map", fontweight="bold")
    fig = ax.figure
    fig.colorbar(cs, ax=ax, label="BSFC (g/kWh)", shrink=0.8)


def _draw_steady_cornering_panel(ax, vehicle):
    """右上：稳态转向响应 双Y轴（横摆角速度 + 侧向加速度 vs 车速）"""
    speeds = np.linspace(10, 150, 30)
    yaw_rates = []
    lateral_accs = []

    for v in speeds:
        r = calc_steady_state_cornering(vehicle, v, steer_angle_deg=3)
        yaw_rates.append(r["yaw_rate_deg_s"])
        lateral_accs.append(r["lateral_acc_g"])

    color1 = "#2c7bb6"
    color2 = "#d7191c"

    ax2_twin = ax.twinx()

    line1, = ax.plot(speeds, yaw_rates, color=color1, linewidth=2, label="横摆角速度")
    line2, = ax2_twin.plot(speeds, lateral_accs, color=color2, linewidth=2, linestyle="--", label="侧向加速度")

    ax.set_xlabel("车速 (km/h)")
    ax.set_ylabel("横摆角速度 (deg/s)", color=color1)
    ax2_twin.set_ylabel("侧向加速度 (g)", color=color2)
    ax.tick_params(axis="y", labelcolor=color1)
    ax2_twin.tick_params(axis="y", labelcolor=color2)

    # 图例
    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    ax.legend(lines, labels, loc="upper left", fontsize=8)

    ax.set_title("稳态转向响应 (方向盘 3°)", fontweight="bold")
    ax.grid(True, alpha=0.3)


def _draw_turn_radius_panel(ax, vehicle):
    """左下：转弯半径 vs 车速（展示不足转向特征）"""
    speeds = np.linspace(10, 150, 30)
    radii = [calc_steady_state_cornering(vehicle, v, steer_angle_deg=3)["turn_radius_m"]
             for v in speeds]

    ax.plot(speeds, radii, color="#1b7837", linewidth=2.5)
    ax.fill_between(speeds, radii, alpha=0.15, color="#1b7837")

    # 标注低速参考半径
    r_ref = radii[0]
    ax.axhline(y=r_ref, color="gray", linestyle=":", alpha=0.6)
    ax.annotate(f"低速半径 {r_ref:.0f}m", xy=(120, r_ref + 2),
                fontsize=8, color="gray")

    # 标注不足转向趋势
    ax.annotate("不足转向 → 高速时\n转弯半径显著增大",
                xy=(100, radii[20]), fontsize=9,
                color="#1b7837", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.8))

    ax.set_xlabel("车速 (km/h)")
    ax.set_ylabel("转弯半径 (m)")
    ax.set_title("转弯半径 vs 车速（不足转向特征）", fontweight="bold")
    ax.grid(True, alpha=0.3)


def _draw_step_steer_panel(ax, vehicle):
    """右下：阶跃转向瞬态响应（80km/h, 3°方向盘）"""
    history = simulate_step_steer(vehicle, vx_kmh=80, steer_angle_deg=3, duration_s=3)

    times = [h[0] for h in history]
    r_deg = [h[3] for h in history]

    # 稳态理论值
    result = calc_steady_state_cornering(vehicle, 80, 3)
    r_steady = result["yaw_rate_deg_s"]

    ax.plot(times, r_deg, color="#2c7bb6", linewidth=2)
    ax.axhline(y=r_steady, color="gray", linestyle="--", alpha=0.7)
    ax.annotate(f"稳态值 {r_steady:.1f} deg/s",
                xy=(2.0, r_steady + 0.5), fontsize=8, color="gray")

    # 标注上升时间（达到稳态 90%）
    target = 0.9 * r_steady
    rise_idx = next((i for i, r in enumerate(r_deg) if r >= target), None)
    if rise_idx:
        t_rise = times[rise_idx]
        ax.axvline(x=t_rise, color="#d7191c", linestyle=":", alpha=0.6)
        ax.annotate(f"90%上升\n{t_rise:.2f}s",
                    xy=(t_rise + 0.1, r_steady * 0.3),
                    fontsize=8, color="#d7191c")

    ax.set_xlabel("时间 (s)")
    ax.set_ylabel("横摆角速度 (deg/s)")
    ax.set_title("阶跃转向瞬态响应 (80km/h, 3°)", fontweight="bold")
    ax.grid(True, alpha=0.3)


if __name__ == "__main__":
    plot_dashboard()
