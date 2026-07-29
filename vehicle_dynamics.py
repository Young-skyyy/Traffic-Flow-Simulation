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

    # 练习 1：看轿车加速到 100 km/h 的过程
    simulate_acceleration(car_sedan, target_speed_kmh=100)

    # 练习 2：制动距离表
    show_braking_table()

    # 练习 3：稳态油耗对比（BSFC 万有特性模型）
    show_fuel_table()

    # 练习 4：汇总仪表盘 —— BSFC 万有特性 + 横向动力学 四合一
    plot_dashboard(car_sedan)

    # 练习 4b：WLTC 标准循环瞬态仿真（耗时较长，注释掉按需运行）
    # show_wltc_summary()
    # simulate_wltc(car_sedan)

    # 练习 5：跟车模型
    car_following_simulation()

    # 练习 6：功率分解 —— 爬坡功率、比功率、风阻功率
    show_power_breakdown(car_sedan, speed_kmh=100, grade_percent=5)
    show_power_breakdown(car_suv, speed_kmh=100, grade_percent=5)
    show_power_breakdown(car_truck, speed_kmh=80, grade_percent=3)

    # 练习 7：横向动力学 —— 自行车模型、不足/过度转向
    show_lateral_analysis(car_sedan)
    show_steady_cornering_table(car_sedan)
    show_step_steer_response(car_sedan, vx_kmh=80, steer_deg=3)

    print("\n提示: 改参数试试 — 把路面摩擦系数从 0.7 改成 0.3（雨天）看制动距离变化")
