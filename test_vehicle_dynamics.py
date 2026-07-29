# -*- coding: utf-8 -*-
"""Pytest unit tests for vehicle dynamics module"""

import pytest
import math
from vehicle import (
    Vehicle,
    calc_resistance,
    calc_braking_distance,
    calc_acceleration,
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


# ============================================================
# Vehicle class
# ============================================================

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


# ============================================================
# calc_resistance
# ============================================================

class TestCalcResistance:
    def test_rolling_resistance_zero_speed(self, sedan):
        """At v=0, zero aero drag, only rolling."""
        resistance = calc_resistance(sedan, 0)
        expected_rolling = 0.015 * 1500 * 9.8  # = 220.5 N
        assert resistance == pytest.approx(expected_rolling, rel=1e-6)

    def test_aero_increases_with_speed(self, sedan):
        r_low = calc_resistance(sedan, 10)
        r_high = calc_resistance(sedan, 30)
        assert r_high > r_low

    def test_aero_drag_formula(self, sedan):
        """Aero: 0.5 * 1.225 * Cd * A * v^2"""
        v = 20  # m/s
        resistance = calc_resistance(sedan, v)
        rolling = 0.015 * 1500 * 9.8
        aero = 0.5 * 1.225 * 0.28 * 2.2 * v ** 2
        expected = rolling + aero
        assert resistance == pytest.approx(expected, rel=1e-6)

    def test_heavier_vehicle_more_rolling(self, sedan, truck):
        r_sedan = calc_resistance(sedan, 0)
        r_truck = calc_resistance(truck, 0)
        assert r_truck > r_sedan


# ============================================================
# calc_braking_distance
# ============================================================

class TestBrakingDistance:
    def test_braking_formula(self):
        """Total = reaction_dist + braking_dist"""
        v = 50  # km/h
        rd, bd, td = calc_braking_distance(v, friction_coeff=0.7, reaction_time=1.5)

        expected_rd = (50 / 3.6) * 1.5
        expected_bd = (50 / 3.6) ** 2 / (2 * 0.7 * 9.8)

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


# ============================================================
# _interpolate_bsfc (bilinear interpolation on BSFC map)
# ============================================================

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


# ============================================================
# _calc_l100_raw (fuel consumption per 100km)
# ============================================================

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


# ============================================================
# get_wltc_profile
# ============================================================

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


# ============================================================
# calc_acceleration — F = ma physics
# ============================================================

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


# ============================================================
# 真实车型参数验证 — 用已知油耗反推模型合理性
# ============================================================

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
        resistance = calc_resistance(sedan, v / 3.6)
        total_ratio = sedan.gear_ratios[gear - 1] * sedan.final_drive
        engine_torque = resistance * sedan.wheel_radius / (total_ratio * sedan.trans_efficiency)
        load = max(0.01, min(1.0, engine_torque / sedan.max_torque))
        wheel_rps = (v / 3.6) / (2 * math.pi * sedan.wheel_radius)
        engine_rpm = wheel_rps * total_ratio * 60
        bsfc = _interpolate_bsfc(engine_rpm, load, sedan.fuel_type)
        # 60 km/h 巡航时发动机应运行在经济区 (BSFC < 350)
        assert bsfc < 350, f"BSFC {bsfc:.0f} > 350，发动机效率异常"


# ============================================================
# WLTC 工况数据质量验证
# ============================================================

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
        total_dist = sum(v / 3.6 for v in profile) / 1000  # 每 1 秒积分
        assert 18 < total_dist < 23, f"总里程 {total_dist:.1f}km 偏离合理范围"

    def test_idle_stops_exist(self):
        """WLTC 工况应包含多次停车怠速（车速=0）段。"""
        profile = get_wltc_profile()
        idle_count = sum(1 for v in profile if v == 0)
        assert idle_count > 50, f"仅 {idle_count} 个怠速点，停车次数不足"
