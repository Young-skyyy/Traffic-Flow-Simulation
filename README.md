# 咸丰县智慧文旅平台

基于 Python Flask + MySQL 的智慧文旅后端系统，为咸丰县文旅局提供景区管理、活动发布、用户预约等 API 接口。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Flask (Python) |
| 数据库 | MySQL 8.4 |
| 数据生成 | Python 脚本批量造数 |
| 数据格式 | RESTful JSON API |

## 项目结构

```
trae_projects/
├── app.py                  # Flask API 主程序（6 个接口）
├── gen_scenic_data.py      # 景区测试数据生成器
├── test_db.py              # MySQL 连接测试
├── traffic_data.csv        # 交通流量 CSV 数据
├── xianfeng_scenic.csv     # 咸丰县 15 个景区数据（CSV）
├── sql_demo.sql            # SQL 学习演示脚本
├── traffic_flow.py         # 交通流量计算器
└── README.md
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/scenic` | 景区列表，支持 `?category=` `?keyword=` |
| GET | `/api/scenic/<id>` | 景区详情 + 关联活动 |
| GET | `/api/activity` | 活动列表，支持 `?scenic_id=` `?type=` |
| POST | `/api/booking` | 提交预约 |
| GET | `/api/booking` | 预约查询 |
| GET | `/api/stats` | 平台统计看板 |

## 数据库

- 数据库名：`tourism_db`
- 景区表 `scenic_spot`：15 个咸丰县真实景点（坪坝营、黄金洞、唐崖土司城等）
- 活动表 `activity`：49 场文旅活动
- 预约表 `booking`：200 条用户预约

## 快速开始

```bash
# 1. 安装依赖
pip install flask mysql-connector-python

# 2. 生成测试数据（可选）
python gen_scenic_data.py

# 3. 启动服务
python app.py

# 4. 浏览器访问
http://localhost:5000/api/scenic
```
