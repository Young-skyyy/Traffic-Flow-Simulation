# -*- coding: utf-8 -*-
"""
交通流量简易计算器
根据平均车速和车辆平均间距，计算一条车道每小时理论上能通行的车辆数。
"""

def calculate_traffic_flow(speed_kmh: float, spacing_m: float, vehicle_length_m: float = 5.0) -> float:
    """
    计算单车道每小时理论通行车辆数。

    原理说明：
    交通流量 = 车速 / (车辆长度 + 车辆间距)  → 每秒通过的车辆数
    再乘以 3600 秒，得到每小时通行的车辆数。

    参数：
        speed_kmh:  平均车速（公里/小时）
        spacing_m:  车辆之间的平均间距（米），指前车尾部到后车头部的距离
        vehicle_length_m: 车辆平均长度（米），默认为 5.0 米（普通小汽车长度）

    返回：
        每小时理论通行车辆数（辆/小时）
    """
    # 将车速从 km/h 转换为 m/s（除以 3.6）
    speed_ms = speed_kmh / 3.6

    # 每辆车在车道上占用的总长度 = 车长 + 车间距
    total_length_per_vehicle = vehicle_length_m + spacing_m

    # 每秒通过车辆数 = 车速(m/s) / 每车占用总长度(m)
    vehicles_per_second = speed_ms / total_length_per_vehicle

    # 每小时通过车辆数 = 每秒通过数 × 3600
    vehicles_per_hour = vehicles_per_second * 3600

    return vehicles_per_hour


def print_result(vehicles_per_hour: float, speed_kmh: float, spacing_m: float, vehicle_length_m: float):
    """格式化输出计算结果。"""
    result = f"""
{'='*50}
           交通流量计算结果
{'='*50}

  输入参数：
    平均车速        : {speed_kmh:.1f} km/h
    车辆平均间距    : {spacing_m:.1f} m
    车辆平均长度    : {vehicle_length_m:.1f} m

  计算结果：
    每小时理论通行车辆数 : {vehicles_per_hour:,.0f} 辆/小时
    折合每分钟            : {vehicles_per_hour / 60:,.0f} 辆/分钟
{'='*50}
"""
    print(result)


def main():
    """主程序入口。"""
    print("\n欢迎使用交通流量简易计算器！\n")

    # 预设一组典型场景进行演示
    print("\n【演示】以下展示几种典型交通场景的通行能力：\n")

    # 场景1：高速公路畅通 —— 车速快、间距大
    flow1 = calculate_traffic_flow(speed_kmh=100, spacing_m=50)
    print_result(flow1, 100, 50, 5.0)
    print("  场景说明：高速公路畅通状态，车速100km/h，保持50米安全间距")

    # 场景2：城市快速路 —— 中等车速和间距
    flow2 = calculate_traffic_flow(speed_kmh=60, spacing_m=25)
    print_result(flow2, 60, 25, 5.0)
    print("  场景说明：城市快速路，车速60km/h，间距约25米")

    # 场景3：城市拥堵 —— 低速、间距小
    flow3 = calculate_traffic_flow(speed_kmh=20, spacing_m=8)
    print_result(flow3, 20, 8, 5.0)
    print("  场景说明：城市拥堵路段，车速仅20km/h，车距很小")

    # 场景4：极端理论最大化 —— 最大密度
    flow4 = calculate_traffic_flow(speed_kmh=30, spacing_m=2)
    print_result(flow4, 30, 2, 5.0)
    print("  场景说明：理论上极高密度状态（不考虑安全因素）")

    print("\n结论：交通流量并不随车速线性增长；在合理范围内，适度保持较高车速和较小间距能提升通行效率，")
    print("但过高的车速会迫使驾驶员拉大安全间距，反而可能降低实际通行能力。\n")


if __name__ == "__main__":
    main()
