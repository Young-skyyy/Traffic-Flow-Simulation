# -*- coding: utf-8 -*-
"""
SQL 综合学习演示脚本
涵盖 DDL、DML、DQL、聚合函数、JOIN、子查询、窗口函数、索引、视图、事务等核心用法。
每一步都配有中文批注，帮助理解 SQL 的各种用法。
"""

import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "006527young",
}

# ============================================================
# 工具函数：执行 SQL 并打印结果
# ============================================================


def execute(cursor, sql, description=""):
    """执行一条 SQL 语句，不返回结果集（CREATE / INSERT / UPDATE / DELETE 等）。"""
    if description:
        print(f"\n{'─'*60}")
        print(f"【{description}】")
        print(f"SQL: {sql.strip()}")
    cursor.execute(sql)


def query(cursor, sql, description="", limit=20):
    """执行查询 SQL 并打印结果集。"""
    if description:
        print(f"\n{'─'*60}")
        print(f"【{description}】")
        print(f"SQL: {sql.strip()}")
    cursor.execute(sql)
    rows = cursor.fetchmany(limit)
    if rows:
        cols = [desc[0] for desc in cursor.description]
        print(f"列: {cols}")
        for row in rows:
            print(f"  {row}")
        remaining = cursor.fetchall()
        if remaining:
            print(f"  ... 还有 {len(remaining)} 行未显示")
    else:
        print("  (无结果)")


# ============================================================
# 主流程
# ============================================================

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# ────────────────────────────────
# 第一部分：DDL - 数据定义语言
# ────────────────────────────────

# 1.1 创建数据库
# CREATE DATABASE：用于创建新数据库。IF NOT EXISTS 可避免重复创建报错。
execute(cursor, "CREATE DATABASE IF NOT EXISTS traffic_db "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci",
        "1.1 CREATE DATABASE - 创建数据库，指定字符集为 utf8mb4 以支持中文")

# 1.2 切换到该数据库
# USE：切换当前会话的默认数据库。
execute(cursor, "USE traffic_db",
        "1.2 USE - 切换到指定数据库")

# 1.3 删除旧表（如果存在）
# DROP TABLE：删除表及其全部数据。IF EXISTS 避免表不存在时报错。
execute(cursor, "DROP TABLE IF EXISTS traffic_records",
        "1.3 DROP TABLE IF EXISTS - 删除旧表，确保环境干净")

# 1.4 创建表
# 常见数据类型：INT 整数、VARCHAR(n) 变长字符串、DECIMAL(p,s) 定点小数、
# DATETIME 日期时间、TEXT 长文本。
# PRIMARY KEY：主键约束，唯一标识每一行，自动 NOT NULL + UNIQUE。
# NOT NULL：非空约束，该列不允许为空值。
# DEFAULT：设置列的默认值。
# COMMENT：添加列注释，便于理解。
execute(cursor, """
CREATE TABLE traffic_records (
    id           INT AUTO_INCREMENT PRIMARY KEY  COMMENT '自增主键，唯一标识每条记录',
    timestamp    DATETIME       NOT NULL         COMMENT '数据采集时间',
    road_name    VARCHAR(50)    NOT NULL         COMMENT '道路名称',
    district     VARCHAR(50)    DEFAULT '包河区'  COMMENT '所属行政区，默认包河区',
    vehicle_count INT           NOT NULL         COMMENT '车流量（辆/小时）',
    avg_speed    DECIMAL(5,1)   NOT NULL         COMMENT '平均车速（km/h）',
    congestion_index DECIMAL(3,2)                COMMENT '拥堵指数（0-1之间，越大越堵）',
    weather      VARCHAR(20)    DEFAULT '晴'     COMMENT '天气状况',
    is_holiday   TINYINT        DEFAULT 0        COMMENT '是否节假日（0=否，1=是）'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='交通流量记录表'
""", "1.4 CREATE TABLE - 创建交通流量记录表，含多种约束和注释")

# 1.5 查看表结构
# DESCRIBE / SHOW COLUMNS：查看表的列定义、数据类型、约束等信息。
query(cursor, "DESCRIBE traffic_records",
      "1.5 DESCRIBE - 查看表结构")

# 1.6 ALTER TABLE - 修改表结构
# ADD COLUMN：新增列。
execute(cursor, "ALTER TABLE traffic_records ADD COLUMN remark VARCHAR(200) DEFAULT NULL COMMENT '备注信息'",
        "1.6a ALTER TABLE ADD COLUMN - 新增列 remark")
# MODIFY COLUMN：修改列的数据类型或约束。
execute(cursor, "ALTER TABLE traffic_records MODIFY COLUMN remark TEXT",
        "1.6b ALTER TABLE MODIFY COLUMN - 修改 remark 列类型为 TEXT")
# DROP COLUMN：删除列（MySQL 8.0+ 支持）。
execute(cursor, "ALTER TABLE traffic_records DROP COLUMN remark",
        "1.6c ALTER TABLE DROP COLUMN - 删除 remark 列")

# ────────────────────────────────
# 第二部分：DML - 数据操作语言
# ────────────────────────────────

# 2.1 INSERT INTO ... VALUES - 单行插入
# 最基本的插入语句，列名和值一一对应。
execute(cursor, """
INSERT INTO traffic_records (timestamp, road_name, district, vehicle_count, avg_speed, congestion_index, weather, is_holiday)
VALUES ('2026-07-27 07:00:00', '屯溪路', '包河区', 1200, 45.0, 0.3, '晴', 0)
""", "2.1 INSERT INTO - 插入单行数据（指定所有列）")

# 2.2 INSERT INTO - 批量插入（省略自增主键 id）
# 一次 INSERT 可插入多行，用逗号分隔，效率远高于逐行插入。
execute(cursor, """
INSERT INTO traffic_records (timestamp, road_name, district, vehicle_count, avg_speed, congestion_index, weather, is_holiday)
VALUES
    ('2026-07-27 07:00:00', '徽州大道', '包河区', 1500, 30.0, 0.7, '阴', 0),
    ('2026-07-27 08:00:00', '屯溪路',   '包河区', 1800, 35.0, 0.5, '晴', 0),
    ('2026-07-27 08:00:00', '徽州大道', '包河区', 2100, 20.0, 0.9, '阴', 0),
    ('2026-07-27 09:00:00', '屯溪路',   '包河区',  900, 50.0, 0.2, '晴', 0),
    ('2026-07-27 09:00:00', '徽州大道', '包河区', 1100, 40.0, 0.4, '阴', 0)
""", "2.2 INSERT INTO - 批量插入多行数据")

# 2.3 INSERT INTO - 利用默认值插入
# 未指定的列会使用 DEFAULT 值或 NULL。这里 district 和 weather 会用默认值。
execute(cursor, """
INSERT INTO traffic_records (timestamp, road_name, vehicle_count, avg_speed, congestion_index)
VALUES ('2026-07-27 10:00:00', '南一环', 850, 52.0, 0.15)
""", "2.3 INSERT INTO - 省略有默认值的列（district 默认 '包河区'，weather 默认 '晴'）")

# 2.4 补充更多数据，让后续查询示例更丰富
execute(cursor, """
INSERT INTO traffic_records (timestamp, road_name, district, vehicle_count, avg_speed, congestion_index, weather, is_holiday)
VALUES
    ('2026-07-27 10:00:00', '屯溪路',   '包河区',  950, 48.0, 0.25, '晴', 0),
    ('2026-07-27 10:00:00', '徽州大道', '包河区', 1300, 38.0, 0.45, '阴', 0),
    ('2026-07-27 11:00:00', '屯溪路',   '包河区', 1000, 46.0, 0.28, '晴', 0),
    ('2026-07-27 11:00:00', '徽州大道', '包河区', 1250, 42.0, 0.38, '多云', 0),
    ('2026-07-27 12:00:00', '屯溪路',   '包河区',  800, 55.0, 0.10, '晴', 0),
    ('2026-07-27 12:00:00', '徽州大道', '包河区', 1050, 45.0, 0.30, '晴', 0),
    ('2026-07-27 17:00:00', '屯溪路',   '包河区', 2200, 18.0, 0.85, '晴', 0),
    ('2026-07-27 17:00:00', '徽州大道', '包河区', 2500, 12.0, 0.95, '小雨', 0),
    ('2026-07-27 18:00:00', '屯溪路',   '包河区', 2400, 15.0, 0.90, '晴', 0),
    ('2026-07-27 18:00:00', '徽州大道', '包河区', 2700, 10.0, 0.98, '小雨', 0),
    -- 添加其他行政区的数据，为后续 JOIN 演示做准备
    ('2026-07-27 08:00:00', '长江中路', '庐阳区', 1600, 28.0, 0.60, '晴', 0),
    ('2026-07-27 08:00:00', '黄山路',   '蜀山区', 1400, 32.0, 0.50, '晴', 0),
    ('2026-07-27 18:00:00', '长江中路', '庐阳区', 2300, 14.0, 0.88, '阴', 0),
    ('2026-07-27 18:00:00', '黄山路',   '蜀山区', 2000, 18.0, 0.78, '小雨', 0)
""", "2.4 INSERT INTO - 补充更多数据（多行政区、多时段）")

# 2.5 UPDATE - 修改数据
# UPDATE ... SET ... WHERE：更新符合条件的行。
# 注意：不带 WHERE 会更新全表！WHERE 条件非常重要。
execute(cursor, """
UPDATE traffic_records
SET weather = '多云转晴', congestion_index = 0.22
WHERE road_name = '屯溪路' AND timestamp = '2026-07-27 09:00:00'
""", "2.5 UPDATE - 更新屯溪路 9 点的天气和拥堵指数（带 WHERE 精准定位）")

# 2.6 UPDATE - 多列同时更新 + 表达式
# SET 中可以使用表达式，例如把拥堵指数大于 0.9 的标记为节假日。
execute(cursor, """
UPDATE traffic_records
SET is_holiday = 1,
    congestion_index = congestion_index * 0.95
WHERE congestion_index >= 0.9
""", "2.6 UPDATE - 将拥堵指数 >= 0.9 的记录标记为节假日，并微调指数（表达式更新）")

# 2.7 DELETE - 删除数据
# DELETE FROM ... WHERE：删除符合条件的行。
# 同样，不带 WHERE 会删除全表数据！
execute(cursor, """
DELETE FROM traffic_records
WHERE vehicle_count < 800 AND road_name = '南一环'
""", "2.7 DELETE - 删除南一环车流量 < 800 的记录")

# 2.8 TRUNCATE vs DELETE
# TRUNCATE：清空全表，不可回滚，速度快（本质是 DDL）。这里不执行，仅说明。
print("""
┌─────────────────────────────────────────────────────────────┐
│ 【2.8 TRUNCATE vs DELETE 说明】                             │
│ TRUNCATE TABLE table_name;  -- 清空全表，不可回滚，自增归零 │
│ DELETE FROM table_name;      -- 逐行删除，可回滚，可加WHERE │
│ 日常删数据用 DELETE + WHERE；清空全表重建用 TRUNCATE。       │
└─────────────────────────────────────────────────────────────┘""")

# 提交所有 DML 操作
conn.commit()

# ────────────────────────────────
# 第三部分：DQL - 数据查询语言（基础）
# ────────────────────────────────

# 3.1 SELECT * - 查看全表
# * 代表所有列。生产环境建议明确列出需要的列，减少数据传输。
query(cursor, "SELECT * FROM traffic_records",
      "3.1 SELECT * - 查看全表所有数据")

# 3.2 SELECT 指定列
# 明确列出列名，比 SELECT * 更高效、更清晰。
query(cursor, "SELECT timestamp, road_name, vehicle_count, avg_speed FROM traffic_records",
      "3.2 SELECT 指定列 - 只查询需要的列，减少开销")

# 3.3 WHERE - 条件过滤
# 常用比较运算符：= < > <= >= <> !=
query(cursor, """
SELECT timestamp, road_name, vehicle_count, avg_speed
FROM traffic_records
WHERE vehicle_count > 2000
""", "3.3 WHERE - 查询车流量 > 2000 的记录")

# 3.4 AND / OR / NOT - 组合条件
# AND：同时满足；OR：满足其一；NOT：取反。
query(cursor, """
SELECT timestamp, road_name, vehicle_count, congestion_index, weather
FROM traffic_records
WHERE road_name = '屯溪路' AND congestion_index > 0.5
""", "3.4 WHERE AND - 屯溪路且拥堵指数 > 0.5 的记录")

query(cursor, """
SELECT timestamp, road_name, weather
FROM traffic_records
WHERE weather = '小雨' OR weather = '阴'
""", "3.4 WHERE OR - 天气为小雨或阴天的记录")

# 3.5 BETWEEN - 范围查询
# BETWEEN a AND b 等价于 >= a AND <= b，包含两端。
query(cursor, """
SELECT timestamp, road_name, avg_speed
FROM traffic_records
WHERE avg_speed BETWEEN 30 AND 50
""", "3.5 BETWEEN - 平均车速在 30 到 50 km/h 之间的记录")

# 3.6 IN / NOT IN - 集合查询
# 判断某列的值是否在指定集合中。
query(cursor, """
SELECT timestamp, road_name, district
FROM traffic_records
WHERE district IN ('庐阳区', '蜀山区')
""", "3.6 IN - 查询庐阳区和蜀山区的记录")

# 3.7 LIKE - 模糊查询
# % 匹配任意多个字符；_ 匹配单个字符。
query(cursor, """
SELECT road_name, district
FROM traffic_records
WHERE road_name LIKE '%大道'
""", "3.7 LIKE - 查询以 '大道' 结尾的道路名")

# 3.8 IS NULL / IS NOT NULL
# 不能用 = NULL，必须用 IS NULL。
query(cursor, """
SELECT timestamp, road_name, congestion_index
FROM traffic_records
WHERE congestion_index IS NOT NULL
""", "3.8 IS NOT NULL - 查询拥堵指数不为空的记录")

# ────────────────────────────────
# 第四部分：排序、分页、去重
# ────────────────────────────────

# 4.1 ORDER BY - 排序
# ASC 升序（默认）、DESC 降序。可按多列排序。
query(cursor, """
SELECT timestamp, road_name, vehicle_count, congestion_index
FROM traffic_records
ORDER BY congestion_index DESC, vehicle_count ASC
""", "4.1 ORDER BY - 按拥堵指数降序，拥堵相同时按车流量升序")

# 4.2 LIMIT + OFFSET - 分页
# LIMIT n：返回前 n 行。
# OFFSET m：跳过前 m 行（常用于分页：第 N 页 = LIMIT page_size OFFSET (N-1)*page_size）。
query(cursor, """
SELECT timestamp, road_name, vehicle_count
FROM traffic_records
ORDER BY vehicle_count DESC
LIMIT 3
""", "4.2a LIMIT - 返回车流量最高的前 3 条记录")

query(cursor, """
SELECT timestamp, road_name, vehicle_count
FROM traffic_records
ORDER BY vehicle_count DESC
LIMIT 3 OFFSET 3
""", "4.2b LIMIT OFFSET - 跳过前3条，取第4-6条（第二页数据）")

# 4.3 DISTINCT - 去重
# 返回唯一值组合。
query(cursor, """
SELECT DISTINCT district FROM traffic_records
""", "4.3a DISTINCT - 查询所有不重复的行政区")

query(cursor, """
SELECT DISTINCT road_name, district FROM traffic_records
""", "4.3b DISTINCT 多列 - 查询 (道路, 行政区) 的唯一组合")

# ────────────────────────────────
# 第五部分：聚合函数 + GROUP BY + HAVING
# ────────────────────────────────

# 5.1 COUNT / SUM / AVG / MAX / MIN
# 聚合函数将多行汇总为一个值。
query(cursor, """
SELECT
    COUNT(*)        AS 总记录数,
    COUNT(DISTINCT road_name) AS 道路数量,
    SUM(vehicle_count) AS 总车流量,
    AVG(avg_speed)     AS 平均车速,
    MAX(vehicle_count) AS 最高车流量,
    MIN(vehicle_count) AS 最低车流量,
    ROUND(AVG(congestion_index), 2) AS 平均拥堵指数
FROM traffic_records
""", "5.1 聚合函数 - COUNT/SUM/AVG/MAX/MIN 汇总统计")

# 5.2 GROUP BY - 分组统计
# 按指定列分组后，每组独立执行聚合函数。
# 这是数据分析最常用的模式：先分组，再聚合。
query(cursor, """
SELECT
    road_name                     AS 道路名称,
    COUNT(*)                      AS 记录数,
    AVG(vehicle_count)            AS 平均车流量,
    ROUND(AVG(avg_speed), 1)      AS 平均车速,
    ROUND(AVG(congestion_index), 2) AS 平均拥堵指数
FROM traffic_records
GROUP BY road_name
ORDER BY 平均拥堵指数 DESC
""", "5.2 GROUP BY - 按道路分组统计各项平均值")

# 5.3 多列 GROUP BY
query(cursor, """
SELECT
    road_name,
    weather,
    COUNT(*)          AS 记录数,
    AVG(vehicle_count) AS 平均车流量
FROM traffic_records
GROUP BY road_name, weather
ORDER BY road_name, weather
""", "5.3 GROUP BY 多列 - 按道路+天气分组统计")

# 5.4 HAVING - 分组后过滤
# WHERE 过滤行 → GROUP BY 分组 → HAVING 过滤分组 → ORDER BY 排序。
# HAVING 用于对聚合结果做条件过滤（WHERE 做不到）。
query(cursor, """
SELECT
    road_name,
    COUNT(*)            AS 记录数,
    AVG(vehicle_count)  AS 平均车流量
FROM traffic_records
GROUP BY road_name
HAVING AVG(vehicle_count) > 1200
ORDER BY 平均车流量 DESC
""", "5.4 HAVING - 筛选平均车流量 > 1200 的道路（分组后的过滤）")

# 5.5 GROUP BY + 时间维度（按小时聚合）
# 用 DATE_FORMAT 或 HOUR() 函数提取时间维度。
query(cursor, """
SELECT
    HOUR(timestamp)      AS 小时,
    COUNT(*)             AS 记录数,
    AVG(vehicle_count)   AS 平均车流量,
    ROUND(AVG(avg_speed), 1) AS 平均车速
FROM traffic_records
GROUP BY HOUR(timestamp)
ORDER BY 小时
""", "5.5 GROUP BY 时间维度 - 按小时分组统计流量变化趋势")

# ────────────────────────────────
# 第六部分：字符串、日期、数值函数
# ────────────────────────────────

# 6.1 字符串函数：CONCAT、LENGTH、UPPER/LOWER、SUBSTRING
query(cursor, """
SELECT
    road_name,
    CONCAT(road_name, '-', district)   AS 完整路径,       -- 字符串拼接
    CHAR_LENGTH(road_name)             AS 名称字符数,      -- 字符数（中文友好）
    UPPER(weather)                     AS 天气大写         -- 转大写
FROM traffic_records
LIMIT 5
""", "6.1 字符串函数 - CONCAT/CHAR_LENGTH/UPPER 等")

# 6.2 日期时间函数
query(cursor, """
SELECT
    timestamp,
    DATE(timestamp)         AS 日期,
    TIME(timestamp)         AS 时间,
    HOUR(timestamp)         AS 小时,
    DAYOFWEEK(timestamp)    AS 星期几,      -- 1=周日
    DATE_FORMAT(timestamp, '%Y年%m月%d日 %H时') AS 格式化时间
FROM traffic_records
LIMIT 5
""", "6.2 日期时间函数 - DATE/TIME/HOUR/DATE_FORMAT")

# 6.3 CASE WHEN - 条件判断
# 类似编程中的 if-else，在 SQL 中做条件分类非常实用。
query(cursor, """
SELECT
    timestamp,
    road_name,
    vehicle_count,
    CASE
        WHEN vehicle_count < 1000 THEN '畅通'
        WHEN vehicle_count < 1500 THEN '轻度拥堵'
        WHEN vehicle_count < 2000 THEN '中度拥堵'
        ELSE '严重拥堵'
    END AS 拥堵等级
FROM traffic_records
ORDER BY vehicle_count DESC
""", "6.3 CASE WHEN - 根据车流量划分拥堵等级")

# ────────────────────────────────
# 第七部分：子查询（Subquery）
# ────────────────────────────────

# 7.1 标量子查询 - 子查询返回单个值
# 可用在 SELECT、WHERE、HAVING 中。
query(cursor, """
SELECT timestamp, road_name, vehicle_count
FROM traffic_records
WHERE vehicle_count > (SELECT AVG(vehicle_count) FROM traffic_records)
ORDER BY vehicle_count DESC
""", "7.1 标量子查询 - 查询车流量高于总体平均值的记录")

# 7.2 IN 子查询 - 子查询返回一列
query(cursor, """
SELECT timestamp, road_name, district, vehicle_count
FROM traffic_records
WHERE district IN (
    SELECT DISTINCT district FROM traffic_records WHERE road_name LIKE '%大道'
)
ORDER BY vehicle_count DESC
""", "7.2 IN 子查询 - 查询那些包含'大道'道路的行政区所有记录")

# 7.3 EXISTS 子查询
# EXISTS 检查子查询是否有返回行，比 IN 在某些场景下性能更好。
query(cursor, """
SELECT road_name, district, COUNT(*) AS cnt
FROM traffic_records t1
WHERE EXISTS (
    SELECT 1 FROM traffic_records t2
    WHERE t2.road_name = t1.road_name AND t2.vehicle_count > 2000
)
GROUP BY road_name, district
""", "7.3 EXISTS 子查询 - 查询有过车流量 > 2000 的道路")

# 7.4 派生表子查询 - FROM 子句中的子查询
query(cursor, """
SELECT road_name, 平均拥堵
FROM (
    SELECT road_name, ROUND(AVG(congestion_index), 2) AS 平均拥堵
    FROM traffic_records
    GROUP BY road_name
) AS road_avg
WHERE 平均拥堵 > 0.5
ORDER BY 平均拥堵 DESC
""", "7.4 派生表子查询 - 在 FROM 中嵌套子查询，筛选平均拥堵 > 0.5 的道路")

# ────────────────────────────────
# 第八部分：JOIN - 表连接
# ────────────────────────────────

# 先创建一张辅助表做 JOIN 演示
execute(cursor, "DROP TABLE IF EXISTS district_info",
        "8.0a 准备 JOIN 演示 - 删除旧表")
execute(cursor, """
CREATE TABLE district_info (
    district     VARCHAR(50) PRIMARY KEY,
    area_km2     DECIMAL(8,2) COMMENT '面积（平方公里）',
    population   INT          COMMENT '常住人口（万人）',
    road_count   INT          COMMENT '主干道数量'
) COMMENT='行政区信息表'
""", "8.0b 创建行政区信息表 district_info")
execute(cursor, """
INSERT INTO district_info VALUES
('包河区', 340.00, 122, 15),
('庐阳区', 139.32,  70, 10),
('蜀山区', 663.00, 108, 18),
('瑶海区', 247.00,  86, 12)
""", "8.0c 插入行政区信息数据")
conn.commit()

# 8.1 INNER JOIN - 内连接
# 只返回两表匹配的行（交集）。
query(cursor, """
SELECT
    t.timestamp,
    t.road_name,
    t.district,
    t.vehicle_count,
    d.area_km2,
    d.population
FROM traffic_records t
INNER JOIN district_info d ON t.district = d.district
ORDER BY t.vehicle_count DESC
LIMIT 8
""", "8.1 INNER JOIN - 内连接：只保留两表都匹配的行")

# 8.2 LEFT JOIN - 左外连接
# 返回左表全部行 + 右表匹配的行（不匹配则右表列为 NULL）。
query(cursor, """
SELECT
    d.district,
    d.area_km2,
    d.population,
    COALESCE(t.road_name, '无数据') AS road_name
FROM district_info d
LEFT JOIN traffic_records t ON d.district = t.district
GROUP BY d.district, d.area_km2, d.population, t.road_name
""", "8.2 LEFT JOIN - 左连接：保留左表全部（含瑶海区，无交通数据也显示）")

# 8.3 多表 JOIN
# 可以级联连接多张表。
execute(cursor, "DROP TABLE IF EXISTS road_type",
        "8.3a 准备三表 JOIN - 创建道路类型表")
execute(cursor, """
CREATE TABLE road_type (
    road_name  VARCHAR(50) PRIMARY KEY,
    road_level VARCHAR(20) COMMENT '道路等级：主干道/次干道/快速路'
)
""", "8.3b 创建道路类型表")
execute(cursor, """
INSERT INTO road_type VALUES
('屯溪路', '主干道'),
('徽州大道', '主干道'),
('长江中路', '主干道'),
('黄山路', '快速路')
""", "8.3c 插入道路类型数据")
conn.commit()

query(cursor, """
SELECT
    t.timestamp,
    t.road_name,
    rt.road_level,
    d.district,
    d.population,
    t.vehicle_count,
    t.congestion_index
FROM traffic_records t
INNER JOIN district_info d ON t.district = d.district
INNER JOIN road_type    rt ON t.road_name = rt.road_name
ORDER BY t.vehicle_count DESC
LIMIT 8
""", "8.3 三表 JOIN - traffic + district + road_type 三表联查")

# ────────────────────────────────
# 第九部分：窗口函数（Window Functions）
# ────────────────────────────────

# 窗口函数 = 在不折叠行的情况下做聚合/排名计算。
# 语法：函数() OVER (PARTITION BY 分组 ORDER BY 排序)

# 9.1 ROW_NUMBER / RANK / DENSE_RANK - 排名
query(cursor, """
SELECT
    road_name,
    vehicle_count,
    ROW_NUMBER()   OVER (ORDER BY vehicle_count DESC) AS row_num,   -- 唯一序号
    RANK()         OVER (ORDER BY vehicle_count DESC) AS rank_num,  -- 并列占位
    DENSE_RANK()   OVER (ORDER BY vehicle_count DESC) AS dense_num  -- 并列不占位
FROM traffic_records
ORDER BY vehicle_count DESC
""", "9.1 排名函数 - ROW_NUMBER/RANK/DENSE_RANK 的区别")

# 9.2 PARTITION BY - 分组内排名
query(cursor, """
SELECT
    road_name,
    timestamp,
    vehicle_count,
    ROW_NUMBER() OVER (PARTITION BY road_name ORDER BY vehicle_count DESC) AS 流量排名
FROM traffic_records
ORDER BY road_name, 流量排名
""", "9.2 PARTITION BY - 按道路分组，每组内按车流量排名")

# 9.3 LAG / LEAD - 前后行比较
# LAG(n)：取前第 n 行；LEAD(n)：取后第 n 行。用于计算环比变化。
query(cursor, """
SELECT
    timestamp,
    road_name,
    vehicle_count,
    LAG(vehicle_count)  OVER (PARTITION BY road_name ORDER BY timestamp) AS 上一时段流量,
    LEAD(vehicle_count) OVER (PARTITION BY road_name ORDER BY timestamp) AS 下一时段流量
FROM traffic_records
WHERE road_name = '屯溪路'
ORDER BY timestamp
""", "9.3 LAG/LEAD - 查询屯溪路前后时段的流量变化")

# 9.4 移动平均 / 累积求和
query(cursor, """
SELECT
    timestamp,
    road_name,
    vehicle_count,
    ROUND(AVG(vehicle_count) OVER (PARTITION BY road_name ORDER BY timestamp
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS 近3时段移动平均
FROM traffic_records
WHERE road_name = '徽州大道'
ORDER BY timestamp
""", "9.4 移动平均 - 徽州大道近3个时段的滑动平均流量")

# ────────────────────────────────
# 第十部分：UNION / UNION ALL - 结果集合并
# ────────────────────────────────

# UNION：合并并去重；UNION ALL：合并不去重（更快）。
query(cursor, """
SELECT road_name, vehicle_count, '早高峰' AS period
FROM traffic_records
WHERE HOUR(timestamp) BETWEEN 7 AND 9
UNION ALL
SELECT road_name, vehicle_count, '晚高峰' AS period
FROM traffic_records
WHERE HOUR(timestamp) BETWEEN 17 AND 19
ORDER BY period, vehicle_count DESC
""", "10. UNION ALL - 合并早高峰和晚高峰的数据（不去重）")

# ────────────────────────────────
# 第十一部分：索引（Index）
# ────────────────────────────────

# 11.1 创建索引
# 索引加速查询，但会降低写入速度。常用在 WHERE / JOIN / ORDER BY 列上。
execute(cursor, "CREATE INDEX idx_road_name ON traffic_records(road_name)",
        "11.1 CREATE INDEX - 在 road_name 上创建普通索引")
execute(cursor, "CREATE INDEX idx_timestamp ON traffic_records(timestamp)",
        "11.1b CREATE INDEX - 在 timestamp 上创建索引")

# 11.2 复合索引
# 多列组合索引，遵循最左前缀原则。
execute(cursor, "CREATE INDEX idx_road_time ON traffic_records(road_name, timestamp)",
        "11.2 复合索引 - 在 (road_name, timestamp) 上创建组合索引")

# 11.3 查看索引
query(cursor, "SHOW INDEX FROM traffic_records",
      "11.3 SHOW INDEX - 查看表中的所有索引")

# 11.4 删除索引
execute(cursor, "DROP INDEX idx_road_time ON traffic_records",
        "11.4 DROP INDEX - 删除不再需要的索引")

# ────────────────────────────────
# 第十二部分：视图（View）
# ────────────────────────────────

# 12.1 创建视图
# 视图 = 保存的查询，像一个虚拟表。简化复杂查询，增强安全性（隐藏敏感列）。
execute(cursor, """
CREATE OR REPLACE VIEW v_peak_summary AS
SELECT
    road_name,
    CASE WHEN HOUR(timestamp) BETWEEN 7 AND 9  THEN '早高峰'
         WHEN HOUR(timestamp) BETWEEN 17 AND 19 THEN '晚高峰'
         ELSE '平峰'
    END AS period,
    AVG(vehicle_count)    AS avg_vehicles,
    ROUND(AVG(avg_speed), 1) AS avg_speed,
    ROUND(AVG(congestion_index), 2) AS avg_congestion
FROM traffic_records
GROUP BY road_name, period
""", "12.1 CREATE VIEW - 创建高峰时段汇总视图")

# 12.2 像查表一样查视图
query(cursor, "SELECT * FROM v_peak_summary ORDER BY road_name, period",
      "12.2 查询视图 - 像普通表一样使用视图")

# ────────────────────────────────
# 第十三部分：事务（Transaction）
# ────────────────────────────────

# 事务四大特性（ACID）：原子性、一致性、隔离性、持久性。
print("""
┌─────────────────────────────────────────────────────────────┐
│ 【13. 事务（Transaction）演示】                              │
│ START TRANSACTION → 执行一组 DML → COMMIT（生效）或         │
│ ROLLBACK（回滚）。事务确保一组操作要么全成功，要么全失败。   │
└─────────────────────────────────────────────────────────────┘""")

try:
    cursor.execute("START TRANSACTION")
    cursor.execute("""
        INSERT INTO traffic_records (timestamp, road_name, district, vehicle_count, avg_speed, congestion_index)
        VALUES ('2026-07-27 20:00:00', '测试路', '瑶海区', 500, 60.0, 0.05)
    """)
    print("  事务中：插入了一条测试记录（id 尚未最终提交）")
    # 验证当前事务中可以看到
    cursor.execute("SELECT id, road_name, vehicle_count FROM traffic_records WHERE road_name = '测试路'")
    row = cursor.fetchone()
    print(f"  事务内可查到: {row}")
    # 故意回滚，演示撤销操作
    conn.rollback()
    print("  执行 ROLLBACK - 已撤销插入")
    # 确认回滚后记录消失
    cursor.execute("SELECT id FROM traffic_records WHERE road_name = '测试路'")
    after_rollback = cursor.fetchone()
    print(f"  ROLLBACK 后查询: {after_rollback}（应为 None，说明回滚成功）")
except Exception as e:
    conn.rollback()
    print(f"  事务出错，已回滚: {e}")

# ────────────────────────────────
# 第十四部分：存储过程与函数（简要演示）
# ────────────────────────────────

# 14.1 创建存储函数
execute(cursor, """
DROP FUNCTION IF EXISTS get_congestion_level
""", "14.1a 删除旧函数（如有）")
execute(cursor, """
CREATE FUNCTION get_congestion_level(idx DECIMAL(3,2))
RETURNS VARCHAR(20)
DETERMINISTIC
RETURN CASE
    WHEN idx < 0.3  THEN '畅通'
    WHEN idx < 0.6  THEN '轻度拥堵'
    WHEN idx < 0.8  THEN '中度拥堵'
    ELSE '严重拥堵'
END
""", "14.1b 创建函数 get_congestion_level - 根据指数返回拥堵等级")

query(cursor, """
SELECT
    timestamp,
    road_name,
    congestion_index,
    get_congestion_level(congestion_index) AS 拥堵等级
FROM traffic_records
ORDER BY congestion_index DESC
LIMIT 8
""", "14.1c 调用函数 - 使用自定义函数判断拥堵等级")

# ────────────────────────────────
# 第十五部分：EXPLAIN - 执行计划分析
# ────────────────────────────────

# EXPLAIN 显示 MySQL 如何执行查询，用于性能调优。
query(cursor, """
EXPLAIN SELECT t.road_name, t.vehicle_count, d.population
FROM traffic_records t
INNER JOIN district_info d ON t.district = d.district
WHERE t.vehicle_count > 1500
""", "15. EXPLAIN - 查看查询执行计划（关注 type/rows/key 列）")

# ────────────────────────────────
# 第十六部分：CTE - 公用表表达式（MySQL 8.0+）
# ────────────────────────────────

# WITH ... AS 定义临时结果集，让复杂查询更清晰。
query(cursor, """
WITH road_stats AS (
    SELECT road_name, AVG(vehicle_count) AS avg_veh, AVG(congestion_index) AS avg_cidx
    FROM traffic_records
    GROUP BY road_name
)
SELECT *, RANK() OVER (ORDER BY avg_cidx DESC) AS 拥堵排名
FROM road_stats
ORDER BY 拥堵排名
""", "16. CTE (WITH) - 用 CTE 简化复杂查询，统计各道路拥堵排名")

# ────────────────────────────────
# 第十七部分：常用 SQL 技巧总结
# ────────────────────────────────
print("""
╔══════════════════════════════════════════════════════════════╗
║                    SQL 核心知识总结                           ║
╠══════════════════════════════════════════════════════════════╣
║  DDL  : CREATE / ALTER / DROP / TRUNCATE                    ║
║  DML  : INSERT / UPDATE / DELETE                            ║
║  DQL  : SELECT + WHERE/ORDER BY/LIMIT/DISTINCT              ║
║  聚合 : COUNT/SUM/AVG/MAX/MIN + GROUP BY + HAVING           ║
║  函数 : 字符串/日期/CASE WHEN/窗口函数                       ║
║  子查询: 标量/IN/EXISTS/派生表                               ║
║  JOIN : INNER/LEFT/RIGHT/多表联查                           ║
║  窗口 : ROW_NUMBER/RANK/LAG/LEAD + PARTITION BY             ║
║  索引 : CREATE/DROP INDEX（加速查询）                       ║
║  视图 : CREATE VIEW（虚拟表）                               ║
║  事务 : START TRANSACTION → COMMIT / ROLLBACK               ║
║  其他 : UNION/CTE/EXPLAIN/函数/存储过程                      ║
║                                                              ║
║  SQL 书写顺序:                                               ║
║  SELECT → FROM → JOIN → WHERE → GROUP BY → HAVING           ║
║  → ORDER BY → LIMIT                                         ║
║                                                              ║
║  SQL 执行顺序:                                               ║
║  FROM → JOIN → WHERE → GROUP BY → HAVING                    ║
║  → SELECT → ORDER BY → LIMIT                                ║
╚══════════════════════════════════════════════════════════════╝
""")

# ────────────────────────────────
# 清理
# ────────────────────────────────

cursor.close()
conn.close()
print("数据库连接已关闭。学习演示完成！")
