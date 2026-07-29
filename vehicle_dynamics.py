# -*- coding: utf-8 -*-
"""
车辆动力学仿真
纵向：加速、制动、油耗、功率分解（爬坡/风阻/比功率）
横向：自行车模型、不足转向、稳态/瞬态转向
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
    calc_grade_power,
    calc_power_to_weight,
    calc_aero_drag_power,
    show_power_breakdown,
    rolling_coeff_dynamic,
)
from lateral_dynamics import (
    calc_understeer_gradient,
    calc_steady_state_cornering,
    calc_characteristic_speed,
    calc_critical_speed,
    show_lateral_analysis,
    show_steady_cornering_table,
    show_step_steer_response,
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
from plot_dashboard import plot_dashboard


# ============================================================
# 主程序
# ============================================================
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════╗
║         车辆动力学仿真                         ║
║         Python + 物理建模                     ║
╚══════════════════════════════════════════════╝
    """)

    # ========================
    # 纵向动力学
    # ========================

    # 1. 加速仿真：轿车 0→100 km/h
    simulate_acceleration(car_sedan, target_speed_kmh=100)

    # 2. 制动距离对照表
    show_braking_table()

    # 3. 油耗对比：三车型（轿车/SUV/卡车）BSFC 模型
    show_fuel_table()

    # 4. 跟车模型：前车匀速、后车减速避免碰撞
    car_following_simulation()

    # 5. 功率分解：爬坡功率 / 比功率 / 风阻功率
    show_power_breakdown(car_sedan, speed_kmh=100, grade_percent=5)
    show_power_breakdown(car_suv, speed_kmh=100, grade_percent=5)
    show_power_breakdown(car_truck, speed_kmh=80, grade_percent=3)

    # ========================
    # 横向动力学
    # ========================

    # 6. 不足转向分析：Kus 梯度 + 特征/临界车速
    show_lateral_analysis(car_sedan)

    # 7. 稳态转向：横摆角速度 / 侧向加速度 / 转弯半径 vs 车速
    show_steady_cornering_table(car_sedan)

    # 8. 阶跃转向瞬态响应：突然打方向后横摆收敛过程
    show_step_steer_response(car_sedan, vx_kmh=80, steer_deg=3)

    # ========================
    # 可视化汇总
    # ========================

    # 9. 四合一仪表盘：BSFC + 稳态转向 + 转弯半径 + 阶跃瞬态
    plot_dashboard(car_sedan)

    # [可选] WLTC 标准循环瞬态仿真（1800s，耗时较长）
    # show_wltc_summary()
    # simulate_wltc(car_sedan)

    print()
