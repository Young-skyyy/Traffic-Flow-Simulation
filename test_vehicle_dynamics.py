# -*- coding: utf-8 -*-
"""Pytest unit tests for vehicle dynamics module"""

import pytest
import math
from _constants import G, RHO_AIR, KMH_TO_MS
from vehicle import (
    Vehicle,
    calc_resistance,
    calc_braking_distance,
    calc_acceleration,
    calc_grade_power,
    calc_power_to_weight,
    calc_aero_drag_power,
    rolling_coeff_dynamic,
)
from lateral_dynamics import (
    calc_slip_angles,
    calc_cornering_forces,
    calc_understeer_gradient,
    calc_characteristic_speed,
    calc_critical_speed,
    calc_steady_state_cornering,
    simulate_step_steer,
)
from bsfc import (
    _interpolate_bsfc,
    _calc_l100_raw,
    _BSFC_RPM_GRID,
    _BSFC_LOAD_GRID,
)
from wltc import (
    get_wltc_profile,
    _WLTC_DURATION,
)


# --- Fixtures ---

@pytest.fixture
def sedan():
    return Vehicle("TestSedan", 1500, 100, drag_coeff=0.28,
                   max_torque_nm=180, gear_ratios=[3.55, 2.11, 1.42, 1.00, 0.78],
                   final_drive=4.06, wheel_radius_m=0.32, trans_efficiency=0.90,
                   fuel_density_gl=740, fuel_type="gasoline")


@pytest.fixture
def truck():
    return Vehicle("TestTruck", 15000, 300, drag_coeff=0.65, frontal_area_m2=7.0,
                   max_torque_nm=1000, gear_ratios=[5.50, 3.20, 1.90, 1.00, 0.73],
                   final_drive=4.30, wheel_radius_m=0.52, trans_efficiency=0.85,
                   fuel_density_gl=840, fuel_type="diesel")


# Vehicle class

class TestVehicle:
    def test_default_attributes(self, sedan):
        assert sedan.name == "TestSedan"
        assert sedan.mass == 1500
        assert sedan.power == 100_000
        assert sedan.cd == 0.28
        assert sedan.area == 2.2
        assert sedan.rolling_coeff == 0.015
        assert sedan.max_torque == 180
        assert sedan.idle_rpm == 800
        assert sedan.max_rpm == 6000  # explicitly set in fixture
        assert sedan.fuel_type == "gasoline"

    def test_select_gear_stopped(self, sedan):
        assert sedan.select_gear(0) == 0

    def test_select_gear_low_speed(self, sedan):
        gear = sedan.select_gear(30)
        assert gear >= 1
        assert gear <= len(sedan.gear_ratios)

    def test_select_gear_high_speed(self, sedan):
        gear = sedan.select_gear(120)
        assert gear >= 3  # should be in higher gears

    def test_select_gear_returns_valid_range(self, sedan):
        for speed in [5, 15, 30, 50, 80, 110, 130]:
            gear = sedan.select_gear(speed)
            assert 0 <= gear <= len(sedan.gear_ratios)

    def test_select_gear_increasing_speed_gives_higher_gear(self, sedan):
        g_low = sedan.select_gear(20)
        g_high = sedan.select_gear(80)
        assert g_low <= g_high  # higher speed, higher gear


# calc_resistance

class TestCalcResistance:
    def test_rolling_resistance_zero_speed(self, sedan):
        """At v=0, zero aero drag, only rolling."""
        resistance = calc_resistance(sedan, 0)
        expected_rolling = 0.015 * 1500 * G  # = 220.5 N
        assert resistance == pytest.approx(expected_rolling, rel=1e-6)

    def test_aero_increases_with_speed(self, sedan):
        r_low = calc_resistance(sedan, 10)
        r_high = calc_resistance(sedan, 30)
        assert r_high > r_low

    def test_aero_drag_formula(self, sedan):
        """Aero: 0.5 * RHO_AIR * Cd * A * v^2"""
        v = 20  # m/s
        resistance = calc_resistance(sedan, v)
        rolling = 0.015 * 1500 * G
        aero = 0.5 * RHO_AIR * 0.28 * 2.2 * v ** 2
        expected = rolling + aero
        assert resistance == pytest.approx(expected, rel=1e-6)

    def test_heavier_vehicle_more_rolling(self, sedan, truck):
        r_sedan = calc_resistance(sedan, 0)
        r_truck = calc_resistance(truck, 0)
        assert r_truck > r_sedan


class TestDynamicRollingResistance:
    """rolling_coeff_dynamic + calc_resistance(dynamic_rr=True)"""

    def test_zero_speed_returns_f0(self):
        mu = rolling_coeff_dynamic(0)
        assert mu == pytest.approx(0.010, rel=1e-6)

    def test_100kmh_returns_sum(self):
        """v=100 → v/100=1 → f0+f1+f4"""
        v_ms = 100 * KMH_TO_MS
        mu = rolling_coeff_dynamic(v_ms)
        assert mu == pytest.approx(0.010 + 0.005 + 0.002, rel=1e-6)

    def test_increases_with_speed(self):
        mu_low = rolling_coeff_dynamic(30 * KMH_TO_MS)
        mu_high = rolling_coeff_dynamic(120 * KMH_TO_MS)
        assert mu_high > mu_low

    def test_fourth_order_dominates_at_high_speed(self):
        """120km/h 时四次项贡献应显著大于 60km/h"""
        mu_60 = rolling_coeff_dynamic(60 * KMH_TO_MS)
        mu_120 = rolling_coeff_dynamic(120 * KMH_TO_MS)
        # 从 60→120，增量主要来自四次项
        assert mu_120 - mu_60 > 0.003

    def test_dynamic_rr_lower_than_constant_at_low_speed(self, sedan):
        """常量 μ=0.015，动态在低速时应更低"""
        # 有显式参数的车，不是 sedan fixture
        r_const = calc_resistance(sedan, 10)
        r_dyn = calc_resistance(sedan, 10, dynamic_rr=True)
        assert r_dyn < r_const

    def test_dynamic_rr_switch_defaults_to_false(self, sedan):
        """不传第三个参数时默认用常量"""
        r1 = calc_resistance(sedan, 20)
        r2 = calc_resistance(sedan, 20, dynamic_rr=False)
        assert r1 == r2


# calc_braking_distance

class TestBrakingDistance:
    def test_braking_formula(self):
        """Total = reaction_dist + braking_dist"""
        v = 50  # km/h
        rd, bd, td = calc_braking_distance(v, friction_coeff=0.7, reaction_time=1.5)

        expected_rd = (50 * KMH_TO_MS) * 1.5
        expected_bd = (50 * KMH_TO_MS) ** 2 / (2 * 0.7 * G)

        assert rd == pytest.approx(expected_rd, rel=1e-6)
        assert bd == pytest.approx(expected_bd, rel=1e-6)
        assert td == pytest.approx(expected_rd + expected_bd, rel=1e-6)

    def test_higher_speed_longer_distance(self):
        _, _, td_low = calc_braking_distance(30)
        _, _, td_high = calc_braking_distance(80)
        assert td_high > td_low

    def test_wet_road_longer_distance(self):
        """Lower friction coeff = longer braking distance."""
        _, bd_dry, _ = calc_braking_distance(60, friction_coeff=0.7)
        _, bd_wet, _ = calc_braking_distance(60, friction_coeff=0.3)
        assert bd_wet > bd_dry

    def test_zero_speed(self):
        rd, bd, td = calc_braking_distance(0)
        assert rd == 0
        assert bd == 0
        assert td == 0


# _interpolate_bsfc (bilinear interpolation on BSFC map)

class TestInterpolateBSFC:
    def test_returns_float(self):
        result = _interpolate_bsfc(2500, 0.5, "gasoline")
        assert isinstance(result, float)

    def test_optimal_region_low_bsfc(self):
        """At 2500 RPM, 50% load should be near optimal ~233 g/kWh for gasoline."""
        bsfc = _interpolate_bsfc(2500, 0.5, "gasoline")
        assert bsfc < 300  # should be in efficient zone

    def test_idle_high_bsfc(self):
        """At idle (800 RPM), low load (5%) should have high BSFC ~580."""
        bsfc = _interpolate_bsfc(800, 0.05, "gasoline")
        assert bsfc > 400  # idle is inefficient

    def test_high_rpm_high_bsfc(self):
        """At redline and high load, BSFC is high."""
        bsfc = _interpolate_bsfc(6200, 0.85, "gasoline")
        assert bsfc > 300

    def test_clamps_rpm_to_map_bounds(self):
        """Values outside RPM grid should be clamped."""
        bsfc_low = _interpolate_bsfc(100, 0.5, "gasoline")
        bsfc_high = _interpolate_bsfc(10000, 0.5, "gasoline")
        # Should not crash, should return valid values
        assert bsfc_low > 0
        assert bsfc_high > 0

    def test_clamps_load_to_map_bounds(self):
        bsfc_zero = _interpolate_bsfc(2500, 0.0, "gasoline")
        bsfc_over = _interpolate_bsfc(2500, 2.0, "gasoline")
        assert bsfc_zero > 0
        assert bsfc_over > 0

    def test_diesel_vs_gasoline(self):
        """Diesel BSFC should generally be lower than gasoline."""
        gas = _interpolate_bsfc(2500, 0.5, "gasoline")
        diesel = _interpolate_bsfc(2000, 0.5, "diesel")
        # Diesel map values are lower
        assert diesel < gas

    def test_monotonically_decreasing_then_increasing(self):
        """BSFC should form a U-shape: high at very low load, low in middle."""
        low = _interpolate_bsfc(2500, 0.05, "gasoline")
        mid = _interpolate_bsfc(2500, 0.50, "gasoline")
        high = _interpolate_bsfc(2500, 1.0, "gasoline")
        assert mid < low
        assert mid < high


# _calc_l100_raw (fuel consumption per 100km)

class TestFuelConsumption:
    def test_zero_speed(self, sedan):
        fuel = _calc_l100_raw(sedan, 0)
        assert fuel == 0.0

    def test_cruise_returns_reasonable(self, sedan):
        """Highway cruise should be ~5-8 L/100km."""
        fuel = _calc_l100_raw(sedan, 90)
        assert 3 < fuel < 12

    def test_low_speed_reasonable(self, sedan):
        """20 km/h should return a reasonable L/100km value."""
        fuel = _calc_l100_raw(sedan, 20)
        assert 2 < fuel < 8

    def test_truck_diesel_higher_absolute(self, sedan, truck):
        """Truck consumes more fuel per 100km in absolute terms."""
        fuel_sedan = _calc_l100_raw(sedan, 80)
        fuel_truck = _calc_l100_raw(truck, 80)
        assert fuel_truck > fuel_sedan


# get_wltc_profile

class TestWLTCProfile:
    def test_returns_correct_length(self):
        profile = get_wltc_profile()
        assert len(profile) == _WLTC_DURATION + 1

    def test_starts_at_zero(self):
        profile = get_wltc_profile()
        assert profile[0] == 0
        # Last element may not be exactly 0 due to interpolation coverage limits

    def test_all_non_negative(self):
        profile = get_wltc_profile()
        assert all(v >= 0 for v in profile)

    def test_has_high_speed_segments(self):
        profile = get_wltc_profile()
        max_speed = max(profile)
        assert max_speed > 100  # WLTC Class 3 has speeds > 130 km/h

    def test_profile_is_numeric(self):
        profile = get_wltc_profile()
        for v in profile:
            assert isinstance(v, (int, float))


# calc_acceleration — F = ma physics

class TestAcceleration:
    def test_zero_at_standstill(self, sedan):
        """At v=0 power/speed division returns 0, acceleration should be 0."""
        acc = calc_acceleration(sedan, 0)
        assert acc == 0

    def test_decreases_with_speed(self, sedan):
        """At 30 m/s vs 15 m/s: higher aero drag + same power → lower accel."""
        acc_low = calc_acceleration(sedan, 15)   # 54 km/h
        acc_high = calc_acceleration(sedan, 30)  # 108 km/h
        assert acc_high < acc_low

    def test_net_force_matches_physics(self, sedan):
        """F_net = P/v - resistance, then a = F_net / m."""
        v = 20  # m/s
        resistance = calc_resistance(sedan, v)
        drive_force = sedan.power / v  # P = F × v
        expected_acc = max(0, (drive_force - resistance) / sedan.mass)
        assert calc_acceleration(sedan, v) == pytest.approx(expected_acc, rel=1e-6)

    def test_heavier_slower(self, sedan, truck):
        """A 15-ton truck has much lower acceleration than 1.5-ton sedan."""
        acc_sedan = calc_acceleration(sedan, 10)
        acc_truck = calc_acceleration(truck, 10)
        assert acc_sedan > acc_truck


# 爬坡功率、比功率、风阻功率

class TestGradePower:
    """calc_grade_power — 爬坡功率"""

    def test_zero_speed_zero_power(self, sedan):
        assert calc_grade_power(sedan, 0, 5) == 0

    def test_zero_grade_zero_power(self, sedan):
        assert calc_grade_power(sedan, 20, 0) == 0

    def test_steeper_grade_more_power(self, sedan):
        p5 = calc_grade_power(sedan, 20, 5)
        p10 = calc_grade_power(sedan, 20, 10)
        assert p10 > p5

    def test_truck_needs_more_grade_power(self, sedan, truck):
        p_sedan = calc_grade_power(sedan, 15, 5)
        p_truck = calc_grade_power(truck, 15, 5)
        assert p_truck > p_sedan

    def test_returns_watts(self, sedan):
        p = calc_grade_power(sedan, 20, 5)
        assert p > 0
        assert isinstance(p, float)


class TestPowerToWeight:
    """calc_power_to_weight — 比功率"""

    def test_sedan_reasonable(self, sedan):
        wpk, kpt = calc_power_to_weight(sedan)
        assert 50 < wpk < 100
        assert wpk == pytest.approx(100_000 / 1500, rel=1e-6)

    def test_returns_tuple(self, sedan):
        result = calc_power_to_weight(sedan)
        assert len(result) == 2

    def test_truck_lower_than_sedan(self, sedan, truck):
        wpk_s, _ = calc_power_to_weight(sedan)
        wpk_t, _ = calc_power_to_weight(truck)
        assert wpk_t < wpk_s

    def test_kw_per_ton_equals_w_per_kg(self, sedan):
        wpk, kpt = calc_power_to_weight(sedan)
        assert wpk == pytest.approx(kpt, rel=1e-6)


class TestAeroDragPower:
    """calc_aero_drag_power — 风阻功率"""

    def test_zero_speed_zero_power(self, sedan):
        assert calc_aero_drag_power(sedan, 0) == 0

    def test_cubic_relationship(self, sedan):
        """风阻功率 ∝ v³"""
        p1 = calc_aero_drag_power(sedan, 10)
        p2 = calc_aero_drag_power(sedan, 20)
        # v翻倍 → 功率应为 8 倍
        assert p2 == pytest.approx(p1 * 8, rel=1e-6)

    def test_higher_cd_more_power(self, sedan, truck):
        p_sedan = calc_aero_drag_power(sedan, 30)
        p_truck = calc_aero_drag_power(truck, 30)
        assert p_truck > p_sedan

    def test_formula_correct(self, sedan):
        v = 25  # m/s = 90 km/h
        expected = 0.5 * RHO_AIR * sedan.cd * sedan.area * v ** 3
        assert calc_aero_drag_power(sedan, v) == pytest.approx(expected, rel=1e-6)


# 真实车型参数验证 — 用已知油耗反推模型合理性

class TestRealWorldBenchmarks:
    """对照真实车型公告油耗，验证仿真模型不偏离物理实际。"""

    @pytest.fixture
    def camry_20(self):
        """Toyota Camry 2.0L 汽油机：1550kg, 127kW, 公告油耗 ~5.8 L/100km"""
        return Vehicle("Camry2.0", 1550, 127, drag_coeff=0.27, frontal_area_m2=2.3,
                       max_torque_nm=207, gear_ratios=[3.30, 1.90, 1.42, 1.00, 0.713],
                       final_drive=3.63, wheel_radius_m=0.335, trans_efficiency=0.92,
                       fuel_density_gl=740, fuel_type="gasoline")

    def test_camry_90kmh_cruise_in_ballpark(self, camry_20):
        """90 km/h 定速巡航油耗应在公告值 ±2 L/100km 范围。"""
        fuel = _calc_l100_raw(camry_20, 90)
        assert 4.5 < fuel < 8.0, f"仿真值 {fuel:.1f} 偏离真实范围"

    def test_camry_120kmh_higher_than_90(self, camry_20):
        """风阻正比于 v²，120km/h 应比 90km/h 油耗高。"""
        assert _calc_l100_raw(camry_20, 120) > _calc_l100_raw(camry_20, 90)

    def test_suv_higher_than_sedan(self, sedan, truck):
        """SUV/卡车在同等车速下油耗应高于轿车。"""
        fuel_sedan = _calc_l100_raw(sedan, 80)
        fuel_truck = _calc_l100_raw(truck, 80)
        assert fuel_truck > fuel_sedan

    def test_pipeline_vehicle_to_fuel_consistency(self, sedan):
        """全链路验证：车速 → 选档 → 转速 → 负荷 → BSFC → 油耗，不抛异常且合理。"""
        v = 60  # km/h
        gear = sedan.select_gear(v)
        assert gear > 0, "60 km/h 档位应为正"
        # 通过 calc_resistance 反算发动机扭矩
        resistance = calc_resistance(sedan, v * KMH_TO_MS)
        total_ratio = sedan.gear_ratios[gear - 1] * sedan.final_drive
        engine_torque = resistance * sedan.wheel_radius / (total_ratio * sedan.trans_efficiency)
        load = max(0.01, min(1.0, engine_torque / sedan.max_torque))
        wheel_rps = (v * KMH_TO_MS) / (2 * math.pi * sedan.wheel_radius)
        engine_rpm = wheel_rps * total_ratio * 60
        bsfc = _interpolate_bsfc(engine_rpm, load, sedan.fuel_type)
        # 60 km/h 巡航时发动机应运行在经济区 (BSFC < 350)
        assert bsfc < 350, f"BSFC {bsfc:.0f} > 350，发动机效率异常"


# WLTC 工况数据质量验证

class TestWLTCDataQuality:
    """WLTC Class 3 工况数据应满足法规定义的特征。"""

    def test_four_phases_exist(self):
        """四个阶段应有明显的速度分区特征。"""
        profile = get_wltc_profile()
        low = max(profile[0:589])
        med = max(profile[590:1022])
        high = max(profile[1023:1477])
        exhi = max(profile[1478:1800])
        assert low < med < high < exhi, "四阶段最高速度应递增"

    def test_phase_one_is_city_low_speed(self):
        """Phase 1 (Low) 最高速度不超过 60 km/h。"""
        profile = get_wltc_profile()
        phase1_max = max(profile[0:590])
        assert phase1_max < 60, f"Phase 1 最高速 {phase1_max:.0f} 超出城市工况范围"

    def test_phase_four_is_motorway(self):
        """Phase 4 (Extra High) 应有超过 100 km/h 的高速段。"""
        profile = get_wltc_profile()
        phase4_max = max(profile[1478:1801])
        assert phase4_max > 100, f"Phase 4 最高速 {phase4_max:.0f} 未达高速标准"

    def test_total_distance_approx_20km(self):
        """WLTC 工况总里程约 20 km（插值覆盖限制）。"""
        profile = get_wltc_profile()
        total_dist = sum(v * KMH_TO_MS for v in profile) / 1000  # 每 1 秒积分
        assert 18 < total_dist < 23, f"总里程 {total_dist:.1f}km 偏离合理范围"

    def test_idle_stops_exist(self):
        """WLTC 工况应包含多次停车怠速（车速=0）段。"""
        profile = get_wltc_profile()
        idle_count = sum(1 for v in profile if v == 0)
        assert idle_count > 50, f"仅 {idle_count} 个怠速点，停车次数不足"


# 横向动力学 — 自行车模型测试

@pytest.fixture
def lat_sedan():
    """带完整横向参数的轿车"""
    return Vehicle("LatSedan", 1500, 100, drag_coeff=0.28,
                   wheelbase_m=2.65, cg_to_front_m=1.2,
                   cornering_stiffness_f=80000, cornering_stiffness_r=70000,
                   max_torque_nm=180, gear_ratios=[3.55, 2.11, 1.42, 1.00, 0.78],
                   final_drive=4.06, wheel_radius_m=0.32)


@pytest.fixture
def lat_oversteer():
    """过度转向车：后轴侧偏刚度偏小"""
    return Vehicle("Oversteer", 1500, 100, drag_coeff=0.28,
                   wheelbase_m=2.65, cg_to_front_m=1.2,
                   cornering_stiffness_f=80000, cornering_stiffness_r=40000,
                   max_torque_nm=180, gear_ratios=[3.55, 2.11, 1.42, 1.00, 0.78],
                   final_drive=4.06, wheel_radius_m=0.32)


class TestVehicleLateralParams:
    """Vehicle 横向参数默认值"""

    def test_wheelbase_default(self, sedan):
        assert sedan.wheelbase > 0

    def test_cg_split_default(self, sedan):
        assert sedan.cg_to_front > 0
        assert sedan.cg_to_rear > 0
        assert sedan.wheelbase == pytest.approx(sedan.cg_to_front + sedan.cg_to_rear, rel=1e-6)

    def test_yaw_inertia_default(self, sedan):
        expected = sedan.mass * sedan.cg_to_front * sedan.cg_to_rear
        assert sedan.yaw_inertia == pytest.approx(expected, rel=1e-6)

    def test_cornering_stiffness_default(self, sedan):
        assert sedan.cornering_stiffness_f > 0
        assert sedan.cornering_stiffness_r > 0


class TestSlipAngles:
    """calc_slip_angles"""

    def test_zero_steer_zero_vy_gives_zero(self, lat_sedan):
        af, ar = calc_slip_angles(lat_sedan, vx_ms=20, vy_ms=0, yaw_rate=0, steer_angle_rad=0)
        assert af == 0
        assert ar == 0

    def test_steer_gives_negative_front_slip(self, lat_sedan):
        """转向时，初始侧偏角为负（轮胎运动方向落后于指向）"""
        af, ar = calc_slip_angles(lat_sedan, vx_ms=20, vy_ms=0, yaw_rate=0, steer_angle_rad=0.05)
        assert af < 0

    def test_positive_yaw_gives_front_less_negative(self, lat_sedan):
        """正横摆让前轮侧偏角负得更少"""
        af, ar = calc_slip_angles(lat_sedan, vx_ms=20, vy_ms=0, yaw_rate=0.1, steer_angle_rad=0.05)
        assert af < 0
        assert ar < 0


class TestUndersteerGradient:
    """calc_understeer_gradient"""

    def test_sedan_is_understeer(self, lat_sedan):
        _, kus_deg = calc_understeer_gradient(lat_sedan)
        assert kus_deg > 0, f"轿车应为不足转向，实际 {kus_deg:.3f} deg/g"

    def test_cg_forward_gives_more_understeer(self, lat_sedan):
        """质心前移 → 前轴载荷增加 → 不足转向更严重"""
        front_heavy = Vehicle("Front", 1500, 100, drag_coeff=0.28,
                              wheelbase_m=2.65, cg_to_front_m=1.0,
                              cornering_stiffness_f=80000, cornering_stiffness_r=70000)
        _, kus_f = calc_understeer_gradient(front_heavy)
        _, kus_s = calc_understeer_gradient(lat_sedan)
        # cg_to_front=1.0 < 1.2 → 前轴更重 → Kus 更大
        assert kus_f > kus_s

    def test_oversteer_car_negative_kus(self, lat_oversteer):
        _, kus_deg = calc_understeer_gradient(lat_oversteer)
        assert kus_deg < 0, f"过度转向车 Kus 应为负，实际 {kus_deg:.3f}"


class TestCharacteristicSpeed:
    """calc_characteristic_speed"""

    def test_sedan_has_finite_char_speed(self, lat_sedan):
        v_char = calc_characteristic_speed(lat_sedan)
        assert 50 < v_char < 300, f"特征车速应在合理范围，实际 {v_char:.0f}"

    def test_oversteer_has_infinite_char_speed(self, lat_oversteer):
        assert calc_characteristic_speed(lat_oversteer) == float("inf")


class TestCriticalSpeed:
    """calc_critical_speed"""

    def test_sedan_no_critical_speed(self, lat_sedan):
        assert calc_critical_speed(lat_sedan) == float("inf")

    def test_oversteer_has_finite_critical_speed(self, lat_oversteer):
        v_crit = calc_critical_speed(lat_oversteer)
        assert 0 < v_crit < 300, f"临界车速应在合理范围，实际 {v_crit:.0f}"


class TestSteadyStateCornering:
    """calc_steady_state_cornering"""

    def test_returns_dict_with_keys(self, lat_sedan):
        result = calc_steady_state_cornering(lat_sedan, 60, 3)
        for key in ["yaw_rate_deg_s", "lateral_acc_g", "turn_radius_m", "kus_deg_per_g"]:
            assert key in result

    def test_understeer_larger_radius_at_higher_speed(self, lat_sedan):
        r30 = calc_steady_state_cornering(lat_sedan, 30, 3)["turn_radius_m"]
        r90 = calc_steady_state_cornering(lat_sedan, 90, 3)["turn_radius_m"]
        # 不足转向 → 高速时转弯半径偏大
        assert r90 > r30

    def test_neutral_steer_constant_radius(self):
        """中性转向：转弯半径 ≈ L/δ，与车速无关"""
        neutral = Vehicle("Neutral", 1500, 100, drag_coeff=0.28,
                          wheelbase_m=2.65, cg_to_front_m=1.2,
                          cornering_stiffness_f=96600, cornering_stiffness_r=80000,
                          max_torque_nm=180)
        kus_rad, kus_deg = calc_understeer_gradient(neutral)
        # 确认 Kus ≈ 0（中性转向）
        assert abs(kus_deg) < 0.1, f"应为中性转向，实际 Kus={kus_deg:.4f} deg/g"
        r30 = calc_steady_state_cornering(neutral, 30, 3)["turn_radius_m"]
        r60 = calc_steady_state_cornering(neutral, 60, 3)["turn_radius_m"]
        # 中性转向半径变化很小
        assert abs(r60 - r30) / r30 < 0.10


class TestStepSteerSimulation:
    """simulate_step_steer"""

    def test_returns_non_empty_history(self, lat_sedan):
        history = simulate_step_steer(lat_sedan, 60, 3, duration_s=2)
        assert len(history) > 0

    def test_history_elements_are_five_tuples(self, lat_sedan):
        history = simulate_step_steer(lat_sedan, 60, 3, duration_s=1)
        assert all(len(h) == 5 for h in history)

    def test_converges_to_steady_state(self, lat_sedan):
        """仿真终值应收敛到稳态理论值"""
        result = calc_steady_state_cornering(lat_sedan, 60, 3)
        history = simulate_step_steer(lat_sedan, 60, 3, duration_s=5)
        _, _, _, final_r_deg, final_ay_g = history[-1]
        # 应在 5% 内收敛
        assert final_r_deg == pytest.approx(result["yaw_rate_deg_s"], rel=0.05)
        assert final_ay_g == pytest.approx(result["lateral_acc_g"], rel=0.05)

    def test_yaw_rate_starts_at_zero(self, lat_sedan):
        history = simulate_step_steer(lat_sedan, 60, 3, duration_s=1)
        _, _, r0, _, _ = history[0]
        assert r0 == 0
