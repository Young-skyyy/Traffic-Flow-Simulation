# -*- coding: utf-8 -*-
"""
BSFC 万有特性热力图绘制
"""

import matplotlib
matplotlib.use("Agg")  # 非交互式后端，避免弹窗报错
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import RectBivariateSpline

from bsfc import _BSFC_RPM_GRID, _BSFC_LOAD_GRID, _BSFC_GASOLINE


def plot_bsfc_map(save_path=None):
    """
    绘制汽油机 BSFC 万有特性等高线图。

    横轴: 发动机转速 (RPM)
    纵轴: 扭矩负荷比
    等高线: BSFC (g/kWh)，越低越省油

    - 中间 ~233 g/kWh 区域为最优区
    - 低速低负荷和高速满负荷区域油耗偏高
    """
    # 设置中文字体（Windows 用 SimHei / Microsoft YaHei）
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

    rpm = np.array(_BSFC_RPM_GRID)
    load = np.array(_BSFC_LOAD_GRID) * 100  # 转为百分比
    bsfc_data = np.array(_BSFC_GASOLINE)

    # 三次样条插值到 200×150 网格，使等高线光滑无棱角
    spline = RectBivariateSpline(load, rpm, bsfc_data, kx=3, ky=3)
    rpm_fine = np.linspace(rpm[0], rpm[-1], 200)
    load_fine = np.linspace(load[0], load[-1], 150)
    R_fine, L_fine = np.meshgrid(rpm_fine, load_fine)
    bsfc_fine = spline(load_fine, rpm_fine)

    fig, ax = plt.subplots(figsize=(10, 7))

    # 填充等高线
    levels = [220, 240, 260, 280, 300, 330, 360, 400, 450, 500]
    cs = ax.contourf(R_fine, L_fine, bsfc_fine, levels=levels, cmap="RdYlGn_r", alpha=0.85)
    cbar = fig.colorbar(cs, ax=ax, label="BSFC (g/kWh)", shrink=0.85)
    cbar.ax.tick_params(labelsize=9)

    # 标注线
    ax.contour(R_fine, L_fine, bsfc_fine, levels=levels, colors="black", linewidths=0.3)

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

    # 自动生成带时间戳的文件名
    if save_path is None:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = f"bsfc_map_{timestamp}.png"

    plt.savefig(save_path, dpi=150)
    print(f"[BSFC 热力图已保存] {save_path}")
    plt.close()
