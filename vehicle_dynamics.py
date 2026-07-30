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

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════╗
║         车辆动力学仿真                         ║
║         Python + 物理建模                     ║
╚══════════════════════════════════════════════╝
    """)

    # 纵向动力学
    simulate_acceleration(car_sedan, target_speed_kmh=100)
    show_braking_table()
    show_fuel_table()
    car_following_simulation()
    show_power_breakdown(car_sedan, speed_kmh=100, grade_percent=5)
    show_power_breakdown(car_suv, speed_kmh=100, grade_percent=5)
    show_power_breakdown(car_truck, speed_kmh=80, grade_percent=3)

    # 横向动力学
    show_lateral_analysis(car_sedan)
    show_steady_cornering_table(car_sedan)
    show_step_steer_response(car_sedan, vx_kmh=80, steer_deg=3)

    # 可视化汇总
    plot_dashboard(car_sedan)

    # [可选] WLTC 标准循环瞬态仿真（1800s，耗时较长）
    # show_wltc_summary()
    # simulate_wltc(car_sedan)

    print()
