# -*- coding: utf-8 -*-
"""
车辆动力学仿真
纵向：加速、制动、油耗、功率分解（爬坡/风阻/比功率）
横向：自行车模型、不足转向、稳态/瞬态转向

所有显示逻辑集中在此文件，库函数只负责计算并返回结构化数据。
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
    calc_braking_table,
    car_following_simulation,
    calc_grade_power,
    calc_power_to_weight,
    calc_aero_drag_power,
    calc_power_breakdown,
    rolling_coeff_dynamic,
)
from lateral_dynamics import (
    calc_understeer_gradient,
    calc_steady_state_cornering,
    calc_characteristic_speed,
    calc_critical_speed,
    analyze_lateral,
    calc_steady_cornering_table,
    calc_step_steer_response,
)
from bsfc import (
    calc_fuel_consumption,
    calc_fuel_table,
)
from wltc import (
    get_wltc_profile,
    get_wltc_summary,
    simulate_transient_cycle,
    simulate_wltc,
)
from plotting import plot_bsfc_map
from plot_dashboard import plot_dashboard


# ============================================================
#  显示辅助函数 —— 从库函数获取结构化数据，格式化打印到终端
# ============================================================

def display_acceleration(result):
    """打印加速仿真结果"""
    print(f"\n{'='*50}")
    print(f"  加速到 {result['speed_kmh'][-1]:.0f} km/h")
    print(f"{'='*50}")
    print(f"{'时间(s)':>8}  {'速度(km/h)':>10}  {'加速度(m/s²)':>12}  {'距离(m)':>8}")
    print("-" * 50)
    # 每秒取一个点打印
    for i in range(0, len(result["time"]), 10):  # dt=0.1, 每10步 = 1秒
        t = result["time"][i]
        v = result["speed_kmh"][i]
        a = result["acc_ms2"][i]
        d = result["distance_m"][i]
        print(f"{t:8.1f}  {v:10.1f}  {a:12.3f}  {d:8.1f}")
    print(f"\n结果: {result['elapsed_s']:.1f} 秒跑完 {result['total_dist_m']:.0f} 米")


def display_braking_table(data):
    """打印制动距离对照表"""
    print(f"\n{'='*60}")
    print("制动距离对照表（干燥沥青路面，反应时间 1.5s）")
    print(f"{'='*60}")
    print(f"{'车速(km/h)':>10}  {'反应距离(m)':>12}  {'制动距离(m)':>12}  {'总距离(m)':>10}")
    print("-" * 60)
    for row in data:
        print(f"{row['speed_kmh']:10.0f}  {row['reaction_dist_m']:12.1f}  "
              f"{row['braking_dist_m']:12.1f}  {row['total_dist_m']:10.1f}")


def display_fuel_table(data):
    """打印油耗分析表"""
    print(f"\n{'='*95}")
    print("  百公里油耗分析（BSFC 万有特性模型）")
    print(f"{'='*95}")
    print(f"{'车型':>10}  {'车速':>5}  {'档位':>4}  {'转速':>7}  {'负荷':>6}  {'BSFC':>6}  {'油耗':>6}")
    print("-" * 95)
    last_car = None
    for row in data:
        if row["car_name"] != last_car and last_car is not None:
            print("-" * 95)
        last_car = row["car_name"]
        gear_str = f"{row['gear']}档" if row['gear'] > 0 else "空档"
        print(f"{row['car_name']:>10}  {row['speed_kmh']:>4}km  {gear_str:>4}  "
              f"{row['rpm']:>5.0f}rpm  {row['load_pct']:>4.0%}  "
              f"{row['bsfc_gkwh']:>4.0f}g   {row['l100km']:>5.1f}L")
    print("-" * 95)


def display_car_following(data):
    """打印跟车模型仿真结果"""
    print(f"\n{'='*60}")
    print(f"跟车模型仿真（前车60km/h, 后车70km/h, 初始间距30m）")
    print(f"{'='*60}")
    print(f"{'时间(s)':>8}  {'间距(m)':>8}  {'后车速度':>8}  {'状态':>10}")
    print("-" * 50)
    for i in range(len(data["time"])):
        print(f"{data['time'][i]:8.0f}  {data['gap_m'][i]:8.1f}  "
              f"{data['follower_kmh'][i]:8.1f}  {data['status'][i]:>10}")
        if data["gap_m"][i] <= 0:
            print(f"\n!!! 碰撞发生 !!! 时间: {data['time'][i]:.0f}s")
            break


def display_power_breakdown(data):
    """打印功率分解"""
    print(f"\n{'='*60}")
    print(f"{data['vehicle_name']} 功率分解 @ {data['speed_kmh']}km/h, 坡度 {data['grade_percent']}%")
    print(f"{'='*60}")
    print(f"  发动机最大功率:  {data['engine_max_power_w']/1000:8.1f} kW")
    print(f"  比功率:          {data['power_to_weight_wpk']:8.1f} W/kg ({data['power_to_weight_kpt']:.1f} kW/ton)")
    print(f"{'-'*40}")
    print(f"  滚动阻力功率(常量 μ=0.015):  {data['rolling_power_const_w']/1000:8.2f} kW")
    print(f"  滚动阻力功率(动态 SAE J2263): {data['rolling_power_dyn_w']/1000:8.2f} kW")
    print(f"  风阻功率:                     {data['aero_power_w']/1000:8.2f} kW")
    print(f"  爬坡功率:                     {data['grade_power_w']/1000:8.2f} kW")
    print(f"{'-'*40}")
    print(f"  需求总功率(常量):  {data['total_power_const_w']/1000:8.2f} kW")
    print(f"  需求总功率(动态):  {data['total_power_dyn_w']/1000:8.2f} kW")
    print(f"  功率利用率:        {data['power_utilization_pct']:8.1f} %")


def display_lateral_analysis(data):
    """打印横向动力学分析"""
    print(f"\n{'='*60}")
    print(f"{data['vehicle_name']}  横向动力学分析")
    print(f"{'='*60}")
    print(f"  轴距:             {data['wheelbase_m']:.2f} m")
    print(f"  质心-前轴:        {data['cg_to_front_m']:.2f} m ({data['cg_front_pct']:.0f}%)")
    print(f"  质心-后轴:        {data['cg_to_rear_m']:.2f} m ({data['cg_rear_pct']:.0f}%)")
    print(f"  前轴侧偏刚度:     {data['cornering_stiffness_f']:.0f} N/rad")
    print(f"  后轴侧偏刚度:     {data['cornering_stiffness_r']:.0f} N/rad")
    print(f"  横摆惯量 Iz:      {data['yaw_inertia']:.0f} kg·m²")
    print(f"{'-'*40}")
    print(f"  不足转向梯度 Kus: {data['kus_deg_per_g']:+.3f} deg/g  →  {data['steer_type']}")
    kus_deg = data["kus_deg_per_g"]
    if kus_deg > 0:
        print(f"  特征车速:         {data['characteristic_speed_kmh']:.1f} km/h（横摆增益峰值点）")
    elif kus_deg < 0:
        print(f"  临界车速:         {data['critical_speed_kmh']:.1f} km/h（超过即失稳！）")


def display_steady_cornering_table(data, vehicle_name):
    """打印稳态转向响应对比表"""
    print(f"\n{'='*75}")
    print(f"{vehicle_name}  稳态转向响应（方向盘转角 3°）")
    print(f"{'='*75}")
    print(f"{'车速':>6}  {'横摆角速度':>10}  {'侧向加速度':>10}  {'转弯半径':>10}  {'不足转向梯度':>12}")
    print(f"{'km/h':>6}  {'deg/s':>10}  {'g':>10}  {'m':>10}  {'deg/g':>12}")
    print("-" * 75)
    for row in data:
        print(f"{row['speed_kmh']:6.0f}  {row['yaw_rate_deg_s']:10.2f}  "
              f"{row['lateral_acc_g']:10.3f}  "
              f"{row['turn_radius_m']:10.1f}  "
              f"{row['kus_deg_per_g']:+12.3f}")


def display_step_steer_response(data, vehicle_name, vx_kmh, steer_deg):
    """打印阶跃转向瞬态响应"""
    history = data["history"]
    print(f"\n{'='*70}")
    print(f"{vehicle_name}  阶跃转向瞬态响应（{vx_kmh}km/h, 方向盘{steer_deg}°）")
    print(f"{'='*70}")
    print(f"{'时间(s)':>8}  {'vy(m/s)':>10}  {'r(deg/s)':>10}  {'ay(g)':>8}")
    print("-" * 50)
    for i in range(0, len(history), 100):  # dt=0.01, 每100步 = 1秒
        t, vy, _, r_deg, ay_g = history[i]
        print(f"{t:8.1f}  {vy:10.3f}  {r_deg:10.2f}  {ay_g:8.3f}")
    print(f"\n  稳态理论值:  r={data['steady_yaw_rate']:.2f} deg/s,  "
          f"ay={data['steady_lateral_acc']:.3f} g")
    print(f"  仿真终值:    r={data['final_yaw_rate']:.2f} deg/s,  "
          f"ay={data['final_lateral_acc']:.3f} g")


# ============================================================
#  主入口
# ============================================================

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════╗
║         车辆动力学仿真                         ║
║         Python + 物理建模                     ║
╚══════════════════════════════════════════════╝
    """)

    # ---- 纵向动力学 ----
    acc_result = simulate_acceleration(car_sedan, target_speed_kmh=100)
    display_acceleration(acc_result)

    braking_data = calc_braking_table()
    display_braking_table(braking_data)

    fuel_data = calc_fuel_table()
    display_fuel_table(fuel_data)

    cf_result = car_following_simulation()
    display_car_following(cf_result)

    for car, speed, grade in [
        (car_sedan, 100, 5),
        (car_suv, 100, 5),
        (car_truck, 80, 3),
    ]:
        pb_data = calc_power_breakdown(car, speed_kmh=speed, grade_percent=grade)
        display_power_breakdown(pb_data)

    # ---- 横向动力学 ----
    lat_data = analyze_lateral(car_sedan)
    display_lateral_analysis(lat_data)

    cornering_data = calc_steady_cornering_table(car_sedan)
    display_steady_cornering_table(cornering_data, car_sedan.name)

    steer_data = calc_step_steer_response(car_sedan, vx_kmh=80, steer_deg=3)
    display_step_steer_response(steer_data, car_sedan.name, vx_kmh=80, steer_deg=3)

    # ---- 可视化汇总 ----
    plot_dashboard(car_sedan)

    # [可选] WLTC 标准循环瞬态仿真（1800s，耗时较长）
    # wltc_summary = get_wltc_summary()
    # simulate_wltc(car_sedan, verbose=True)

    print()
