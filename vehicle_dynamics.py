# -*- coding: utf-8 -*-
"""
车辆动力学基础仿真
从 traffic_flow.py 扩展 —— 把"车流量"升级为"一辆车怎么跑"
涉及：加速度、制动距离、油耗、跟车模型
"""

from vehicle import (
    Vehicle,
    car_sedan,
    car_suv,
    car_truck,
    calc_resistance,
    calc_acceleration,
    simulate_acceleration,
    calc_braking_distance,
    show_braking_table,
    car_following_simulation,
)
from bsfc import (
    calc_fuel_consumption,
    show_fuel_table,
)
from wltc import (
    get_wltc_profile,
    show_wltc_summary,
    simulate_transient_cycle,
    simulate_wltc,
)
from plotting import plot_bsfc_map


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
