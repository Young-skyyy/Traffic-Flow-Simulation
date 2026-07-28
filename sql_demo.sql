-- ============================================================
-- SQL 综合学习演示脚本（纯 SQL 版）
-- 可直接在 MySQL Workbench / IDEA 数据库工具 / mysql CLI 中执行
-- 覆盖 DDL / DML / DQL / 聚合 / JOIN / 子查询 / 窗口函数 / 索引 / 视图 / 事务 等
-- ============================================================

-- ============================================================
-- 第一部分：DDL - 数据定义语言（定义结构）
-- ============================================================

-- 1.1 创建数据库
-- CREATE DATABASE：创建数据库。IF NOT EXISTS 避免重复创建时报错。
-- CHARACTER SET utf8mb4：支持中文和 Emoji。
CREATE DATABASE IF NOT EXISTS traffic_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 1.2 使用数据库
USE traffic_db;

-- 1.3 删除旧表（确保演示环境干净）
-- DROP TABLE IF EXISTS：表存在才删除，避免报错。
DROP TABLE IF EXISTS traffic_records;

-- 1.4 创建表
-- 常见数据类型：
--   INT             整数
--   VARCHAR(n)      变长字符串（最多 n 个字符）
--   DECIMAL(p,s)    精确小数（总共 p 位，小数 s 位）
--   DATETIME        日期时间
--   TINYINT         小整数（0-255）
-- 约束：
--   PRIMARY KEY     主键，唯一 + 非空
--   AUTO_INCREMENT  自增
--   NOT NULL        非空
--   DEFAULT         默认值
--   COMMENT         注释
CREATE TABLE traffic_records (
    id               INT AUTO_INCREMENT PRIMARY KEY  COMMENT '自增主键',
    timestamp        DATETIME       NOT NULL         COMMENT '采集时间',
    road_name        VARCHAR(50)    NOT NULL         COMMENT '道路名称',
    district         VARCHAR(50)    DEFAULT '包河区'  COMMENT '行政区',
    vehicle_count    INT            NOT NULL         COMMENT '车流量（辆/小时）',
    avg_speed        DECIMAL(5,1)   NOT NULL         COMMENT '平均车速（km/h）',
    congestion_index DECIMAL(3,2)                    COMMENT '拥堵指数（0-1）',
    weather          VARCHAR(20)    DEFAULT '晴'     COMMENT '天气',
    is_holiday       TINYINT        DEFAULT 0        COMMENT '是否节假日 0=否 1=是'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='交通流量记录表';

-- 1.5 查看表结构
DESCRIBE traffic_records;

-- 1.6 修改表结构 ALTER TABLE
-- ADD COLUMN：新增一列
ALTER TABLE traffic_records ADD COLUMN remark VARCHAR(200) COMMENT '备注';
-- MODIFY COLUMN：修改列类型
ALTER TABLE traffic_records MODIFY COLUMN remark TEXT;
-- DROP COLUMN：删除一列
ALTER TABLE traffic_records DROP COLUMN remark;


-- ============================================================
-- 第二部分：DML - 数据操作语言（增删改）
-- ============================================================

-- 2.1 INSERT INTO - 单行插入
INSERT INTO traffic_records
    (timestamp, road_name, district, vehicle_count, avg_speed, congestion_index, weather, is_holiday)
VALUES
    ('2026-07-27 07:00:00', '屯溪路', '包河区', 1200, 45.0, 0.3, '晴', 0);

-- 2.2 INSERT INTO - 批量插入（逗号分隔，效率远高于逐行插入）
INSERT INTO traffic_records
    (timestamp, road_name, district, vehicle_count, avg_speed, congestion_index, weather, is_holiday)
VALUES
    ('2026-07-27 07:00:00', '徽州大道', '包河区', 1500, 30.0, 0.7, '阴', 0),
    ('2026-07-27 08:00:00', '屯溪路',   '包河区', 1800, 35.0, 0.5, '晴', 0),
    ('2026-07-27 08:00:00', '徽州大道', '包河区', 2100, 20.0, 0.9, '阴', 0),
    ('2026-07-27 09:00:00', '屯溪路',   '包河区',  900, 50.0, 0.2, '晴', 0),
    ('2026-07-27 09:00:00', '徽州大道', '包河区', 1100, 40.0, 0.4, '阴', 0);

-- 2.3 INSERT - 利用默认值（district 默认 '包河区'，weather 默认 '晴'）
INSERT INTO traffic_records (timestamp, road_name, vehicle_count, avg_speed, congestion_index)
VALUES ('2026-07-27 10:00:00', '南一环', 850, 52.0, 0.15);

-- 2.4 补充更多数据（为后续复杂查询做准备）
INSERT INTO traffic_records
    (timestamp, road_name, district, vehicle_count, avg_speed, congestion_index, weather, is_holiday)
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
    -- 其他行政区（为 JOIN 做准备）
    ('2026-07-27 08:00:00', '长江中路', '庐阳区', 1600, 28.0, 0.60, '晴', 0),
    ('2026-07-27 08:00:00', '黄山路',   '蜀山区', 1400, 32.0, 0.50, '晴', 0),
    ('2026-07-27 18:00:00', '长江中路', '庐阳区', 2300, 14.0, 0.88, '阴', 0),
    ('2026-07-27 18:00:00', '黄山路',   '蜀山区', 2000, 18.0, 0.78, '小雨', 0);

-- 2.5 UPDATE - 修改数据（带 WHERE 只更新指定行；不带 WHERE 会更新全表！）
UPDATE traffic_records
SET weather = '多云转晴', congestion_index = 0.22
WHERE road_name = '屯溪路' AND timestamp = '2026-07-27 09:00:00';

-- 2.6 UPDATE - 表达式更新（SET 中可使用运算）
UPDATE traffic_records
SET is_holiday = 1,
    congestion_index = congestion_index * 0.95
WHERE congestion_index >= 0.9;

-- 2.7 DELETE - 删除数据（带 WHERE 只删指定行；不带 WHERE 清空全表！）
DELETE FROM traffic_records
WHERE vehicle_count < 800 AND road_name = '南一环';

-- 2.8 TRUNCATE vs DELETE 说明
-- TRUNCATE TABLE traffic_records;   -- 清空全表，不可回滚，自增计数器归零
-- DELETE FROM traffic_records;      -- 逐行删除，可回滚（事务中），可加 WHERE


-- ============================================================
-- 第三部分：DQL - 数据查询语言（查）
-- ============================================================

-- 3.1 SELECT * / SELECT 指定列
SELECT * FROM traffic_records;
SELECT timestamp, road_name, vehicle_count, avg_speed FROM traffic_records;

-- 3.2 WHERE / AND / OR / BETWEEN / IN / LIKE / IS NULL
SELECT * FROM traffic_records WHERE vehicle_count > 2000;
SELECT * FROM traffic_records WHERE road_name = '屯溪路' AND congestion_index > 0.5;
SELECT * FROM traffic_records WHERE weather = '小雨' OR weather = '阴';
SELECT * FROM traffic_records WHERE avg_speed BETWEEN 30 AND 50;
SELECT * FROM traffic_records WHERE district IN ('庐阳区', '蜀山区');
SELECT * FROM traffic_records WHERE road_name LIKE '%大道';
SELECT * FROM traffic_records WHERE congestion_index IS NOT NULL;


-- ============================================================
-- 第四部分：排序、分页、去重
-- ============================================================

-- ORDER BY DESC（降序）/ ASC（升序，默认）
SELECT * FROM traffic_records ORDER BY congestion_index DESC, vehicle_count ASC;

-- LIMIT / OFFSET 分页
SELECT * FROM traffic_records ORDER BY vehicle_count DESC LIMIT 3;
SELECT * FROM traffic_records ORDER BY vehicle_count DESC LIMIT 3 OFFSET 3;

-- DISTINCT 去重
SELECT DISTINCT district FROM traffic_records;
SELECT DISTINCT road_name, district FROM traffic_records;


-- ============================================================
-- 第五部分：聚合函数 + GROUP BY + HAVING
-- ============================================================

-- COUNT / SUM / AVG / MAX / MIN
SELECT COUNT(*) AS 总记录数, SUM(vehicle_count) AS 总车流量,
       AVG(avg_speed) AS 平均车速, MAX(vehicle_count) AS 最高, MIN(vehicle_count) AS 最低
FROM traffic_records;

-- GROUP BY 分组统计
SELECT road_name, COUNT(*) AS 记录数, AVG(vehicle_count) AS 平均车流量,
       ROUND(AVG(avg_speed), 1) AS 平均车速, ROUND(AVG(congestion_index), 2) AS 平均拥堵
FROM traffic_records
GROUP BY road_name
ORDER BY 平均拥堵 DESC;

-- 多列 GROUP BY
SELECT road_name, weather, COUNT(*) AS 记录数, AVG(vehicle_count) AS 平均车流量
FROM traffic_records GROUP BY road_name, weather;

-- HAVING 分组后过滤（WHERE 做不到，因为 WHERE 在 GROUP BY 前执行）
SELECT road_name, COUNT(*) AS 记录数, AVG(vehicle_count) AS 平均车流量
FROM traffic_records
GROUP BY road_name
HAVING AVG(vehicle_count) > 1200;

-- 按小时聚合
SELECT HOUR(timestamp) AS 小时, COUNT(*) AS 记录数, AVG(vehicle_count) AS 平均车流量
FROM traffic_records GROUP BY HOUR(timestamp) ORDER BY 小时;


-- ============================================================
-- 第六部分：字符串、日期、条件函数
-- ============================================================

-- 字符串函数：CONCAT / CHAR_LENGTH / UPPER
SELECT road_name, CONCAT(road_name, '-', district) AS 完整路径, CHAR_LENGTH(road_name) AS 字符数
FROM traffic_records;

-- 日期函数：DATE / TIME / HOUR / DATE_FORMAT
SELECT timestamp, DATE(timestamp) AS 日期, TIME(timestamp) AS 时间,
       HOUR(timestamp) AS 小时, DATE_FORMAT(timestamp, '%Y年%m月%d日 %H时') AS 格式化
FROM traffic_records;

-- CASE WHEN 条件判断（SQL 中的 if-else）
SELECT timestamp, road_name, vehicle_count,
       CASE WHEN vehicle_count < 1000 THEN '畅通'
            WHEN vehicle_count < 1500 THEN '轻度拥堵'
            WHEN vehicle_count < 2000 THEN '中度拥堵'
            ELSE '严重拥堵' END AS 拥堵等级
FROM traffic_records ORDER BY vehicle_count DESC;


-- ============================================================
-- 第七部分：子查询（Subquery）
-- ============================================================

-- 标量子查询：返回单个值
SELECT * FROM traffic_records
WHERE vehicle_count > (SELECT AVG(vehicle_count) FROM traffic_records);

-- IN 子查询：返回一列
SELECT * FROM traffic_records
WHERE district IN (SELECT DISTINCT district FROM traffic_records WHERE road_name LIKE '%大道');

-- EXISTS 子查询：检查是否存在
SELECT road_name, district, COUNT(*) AS cnt FROM traffic_records t1
WHERE EXISTS (SELECT 1 FROM traffic_records t2 WHERE t2.road_name = t1.road_name AND t2.vehicle_count > 2000)
GROUP BY road_name, district;

-- 派生表子查询：FROM 中的子查询（必须给别名）
SELECT road_name, 平均拥堵 FROM (
    SELECT road_name, ROUND(AVG(congestion_index), 2) AS 平均拥堵
    FROM traffic_records GROUP BY road_name
) AS road_avg WHERE 平均拥堵 > 0.5 ORDER BY 平均拥堵 DESC;


-- ============================================================
-- 第八部分：JOIN - 表连接
-- ============================================================

DROP TABLE IF EXISTS district_info;
CREATE TABLE district_info (
    district   VARCHAR(50) PRIMARY KEY,
    area_km2   DECIMAL(8,2),
    population INT,
    road_count INT
);
INSERT INTO district_info VALUES
('包河区', 340.00, 122, 15), ('庐阳区', 139.32, 70, 10),
('蜀山区', 663.00, 108, 18), ('瑶海区', 247.00, 86, 12);

-- INNER JOIN：只返回两表都匹配的行
SELECT t.road_name, t.district, t.vehicle_count, d.area_km2, d.population
FROM traffic_records t INNER JOIN district_info d ON t.district = d.district;

-- LEFT JOIN：保留左表全部，右表无匹配为 NULL
SELECT d.district, d.population, IFNULL(t.road_name, '无数据') AS road_name
FROM district_info d LEFT JOIN traffic_records t ON d.district = t.district;

-- 三表 JOIN
DROP TABLE IF EXISTS road_type;
CREATE TABLE road_type (road_name VARCHAR(50) PRIMARY KEY, road_level VARCHAR(20));
INSERT INTO road_type VALUES ('屯溪路','主干道'),('徽州大道','主干道'),('长江中路','主干道'),('黄山路','快速路');

SELECT t.road_name, rt.road_level, d.district, t.vehicle_count
FROM traffic_records t
INNER JOIN district_info d ON t.district = d.district
INNER JOIN road_type rt ON t.road_name = rt.road_name
ORDER BY t.vehicle_count DESC;


-- ============================================================
-- 第九部分：窗口函数（MySQL 8.0+）
-- ============================================================

-- ROW_NUMBER / RANK / DENSE_RANK 排名
SELECT road_name, vehicle_count,
       ROW_NUMBER() OVER (ORDER BY vehicle_count DESC) AS row_num,
       RANK()       OVER (ORDER BY vehicle_count DESC) AS rank_num,
       DENSE_RANK() OVER (ORDER BY vehicle_count DESC) AS dense_num
FROM traffic_records;

-- PARTITION BY 分组内排名
SELECT road_name, timestamp, vehicle_count,
       ROW_NUMBER() OVER (PARTITION BY road_name ORDER BY vehicle_count DESC) AS 组内排名
FROM traffic_records;

-- LAG / LEAD 前后行比较
SELECT timestamp, road_name, vehicle_count,
       LAG(vehicle_count)  OVER (PARTITION BY road_name ORDER BY timestamp) AS 上一时段,
       LEAD(vehicle_count) OVER (PARTITION BY road_name ORDER BY timestamp) AS 下一时段
FROM traffic_records WHERE road_name = '屯溪路';

-- 移动平均（近 3 时段滑动窗口）
SELECT timestamp, road_name, vehicle_count,
       ROUND(AVG(vehicle_count) OVER (PARTITION BY road_name ORDER BY timestamp
             ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS 近3时段均值
FROM traffic_records WHERE road_name = '徽州大道';


-- ============================================================
-- 第十部分：UNION 合并结果集
-- ============================================================

SELECT road_name, vehicle_count, '早高峰' AS period
FROM traffic_records WHERE HOUR(timestamp) BETWEEN 7 AND 9
UNION ALL
SELECT road_name, vehicle_count, '晚高峰' AS period
FROM traffic_records WHERE HOUR(timestamp) BETWEEN 17 AND 19
ORDER BY period, vehicle_count DESC;


-- ============================================================
-- 第十一部分：索引
-- ============================================================

CREATE INDEX idx_road_name ON traffic_records(road_name);
CREATE INDEX idx_timestamp ON traffic_records(timestamp);
CREATE INDEX idx_road_time ON traffic_records(road_name, timestamp);  -- 复合索引
SHOW INDEX FROM traffic_records;
DROP INDEX idx_road_time ON traffic_records;


-- ============================================================
-- 第十二部分：视图
-- ============================================================

CREATE OR REPLACE VIEW v_peak_summary AS
SELECT road_name,
       CASE WHEN HOUR(timestamp) BETWEEN 7 AND 9  THEN '早高峰'
            WHEN HOUR(timestamp) BETWEEN 17 AND 19 THEN '晚高峰' ELSE '平峰' END AS period,
       AVG(vehicle_count) AS avg_veh, ROUND(AVG(avg_speed), 1) AS avg_spd,
       ROUND(AVG(congestion_index), 2) AS avg_cidx
FROM traffic_records GROUP BY road_name, period;

SELECT * FROM v_peak_summary ORDER BY road_name, period;


-- ============================================================
-- 第十三部分：事务（ROLLBACK 回滚演示）
-- ============================================================

START TRANSACTION;
INSERT INTO traffic_records (timestamp, road_name, district, vehicle_count, avg_speed, congestion_index)
VALUES ('2026-07-27 20:00:00', '测试路', '瑶海区', 500, 60.0, 0.05);
SELECT * FROM traffic_records WHERE road_name = '测试路';  -- 事务内能看到
ROLLBACK;  -- 撤销！
SELECT * FROM traffic_records WHERE road_name = '测试路';  -- 已消失


-- ============================================================
-- 第十四部分：自定义函数
-- ============================================================

DROP FUNCTION IF EXISTS get_congestion_level;
DELIMITER $$
CREATE FUNCTION get_congestion_level(idx DECIMAL(3,2))
RETURNS VARCHAR(20) DETERMINISTIC
BEGIN
    RETURN CASE WHEN idx < 0.3 THEN '畅通' WHEN idx < 0.6 THEN '轻度拥堵'
                WHEN idx < 0.8 THEN '中度拥堵' ELSE '严重拥堵' END;
END$$
DELIMITER ;

SELECT timestamp, road_name, congestion_index, get_congestion_level(congestion_index) AS 拥堵等级
FROM traffic_records ORDER BY congestion_index DESC;


-- ============================================================
-- 第十五部分：EXPLAIN 执行计划
-- ============================================================

EXPLAIN SELECT t.road_name, t.vehicle_count, d.population
FROM traffic_records t INNER JOIN district_info d ON t.district = d.district
WHERE t.vehicle_count > 1500;


-- ============================================================
-- 第十六部分：CTE 公用表表达式
-- ============================================================

WITH road_stats AS (
    SELECT road_name, AVG(vehicle_count) AS avg_veh, AVG(congestion_index) AS avg_cidx
    FROM traffic_records GROUP BY road_name
)
SELECT *, RANK() OVER (ORDER BY avg_cidx DESC) AS 拥堵排名 FROM road_stats ORDER BY 拥堵排名;


-- ============================================================
-- SQL 书写顺序：SELECT → FROM → JOIN → WHERE → GROUP BY → HAVING → ORDER BY → LIMIT
-- SQL 执行顺序：FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
-- ============================================================
