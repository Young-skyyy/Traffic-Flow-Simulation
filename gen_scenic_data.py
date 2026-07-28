# -*- coding: utf-8 -*-
"""
景区测试数据生成器
用于文旅小程序后端开发——批量生成景区、活动、用户预约数据并写入 MySQL
"""

import mysql.connector
import random
from datetime import datetime, timedelta

from config import DB_CONFIG, DB_TOURISM

# ============================================================
# 1. 景区种子数据（名称、分类、坐标都是真实的咸丰县景点）
# ============================================================
SCENIC_SPOTS = [
    {"name": "坪坝营景区", "category": "自然风光", "lat": 29.6700, "lng": 109.1500,
     "desc": "国家4A级景区，北纬30°原始森林群落，森林覆盖率96%，夏季均温19℃，被誉为鄂西林海天然氧吧。", "city": "咸丰县", "district": "坪坝营镇"},
    {"name": "唐崖河·黄金洞景区", "category": "地质奇观", "lat": 29.8000, "lng": 109.0300,
     "desc": "国家4A级景区，1.5亿年七层溶洞大厦，世界最大地下钙化池，配套地心漂流和茶海羌寨。", "city": "咸丰县", "district": "黄金洞乡"},
    {"name": "唐崖土司城遗址", "category": "世界文化遗产", "lat": 29.7000, "lng": 109.0000,
     "desc": "2015年入选世界文化遗产名录，元至正十五年起覃氏土司世袭381年，保存最完整的土司城址。", "city": "咸丰县", "district": "唐崖镇"},
    {"name": "忠堡大捷纪念园", "category": "红色旅游", "lat": 29.7200, "lng": 109.2800,
     "desc": "国家3A级景区，纪念1935年贺龙任弼时率领红二六军团取得忠堡大捷，全国爱国主义教育基地。", "city": "咸丰县", "district": "忠堡镇"},
    {"name": "龙潭司村", "category": "红色旅游", "lat": 29.8100, "lng": 109.1800,
     "desc": "恩施地区第一个地级党组织诞生地，贺龙元帅战斗过的革命老区，谱写了五个第一的辉煌篇章。", "city": "咸丰县", "district": "清坪镇"},
    {"name": "马倌屯村", "category": "乡村旅游", "lat": 29.6900, "lng": 109.1700,
     "desc": "湖北旅游名村、中国少数民族特色村寨，集四季采摘、农耕体验、萌宠乐园、露营基地于一体。", "city": "咸丰县", "district": "忠堡镇"},
    {"name": "二仙岩湿地保护区", "category": "自然风光", "lat": 29.9500, "lng": 108.9500,
     "desc": "省级湿地自然保护区，地球同纬度罕见的泥炭藓沼泽湿地，被誉为物种基因库，拥有1606种植物。", "city": "咸丰县", "district": "活龙坪乡"},
    {"name": "川洞田园", "category": "自然风光", "lat": 29.6500, "lng": 109.1200,
     "desc": "巨型天然穿洞景观，紫薇长龙花海，栈道依山而建，集洞穴探秘与田园观光于一体。", "city": "咸丰县", "district": "曲江镇"},
    {"name": "绿沃园生态农庄", "category": "乡村旅游", "lat": 29.6800, "lng": 109.1400,
     "desc": "占地3000余亩的生态农庄，种植近20种鲜花四季可赏，配套农家乐、儿童游乐场、婚纱摄影基地。", "city": "咸丰县", "district": "高乐山镇"},
    {"name": "严家祠堂", "category": "历史文化", "lat": 29.7200, "lng": 109.0100,
     "desc": "距唐崖土司城遗址10公里，砖木结构四合院，雕梁画栋的马头墙建筑，土家族宗祠文化代表。", "city": "咸丰县", "district": "唐崖镇"},
    {"name": "麻柳溪羌寨", "category": "民俗文化", "lat": 29.8200, "lng": 109.0200,
     "desc": "黄金洞景区内的羌族村寨，茶园环绕，吊脚楼依山而建，被誉为中国中部最后的香格里拉。", "city": "咸丰县", "district": "黄金洞乡"},
    {"name": "咸丰县民族博物馆", "category": "文博场馆", "lat": 29.6700, "lng": 109.1500,
     "desc": "展示土家族苗族历史文化的综合性博物馆，涵盖摆手舞、南剧、土家织锦等非物质文化遗产。", "city": "咸丰县", "district": "高乐山镇"},
    {"name": "曲江茶海", "category": "乡村旅游", "lat": 29.6400, "lng": 109.1600,
     "desc": "万亩生态茶园，盛产富硒白茶和藤茶，可体验采茶制茶工艺，品土家油茶汤。", "city": "咸丰县", "district": "曲江镇"},
    {"name": "小南海地震遗址", "category": "地质奇观", "lat": 29.6000, "lng": 108.8000,
     "desc": "1856年地震形成的堰塞湖，保存完好的地震遗址景观，湖水清澈四周青山环抱。", "city": "咸丰县", "district": "大路坝区"},
    {"name": "朝阳画廊", "category": "自然风光", "lat": 29.6600, "lng": 109.3000,
     "desc": "唐崖河下游峡谷风光带，乘船游览两岸青山翠竹，土家吊脚楼点缀其间，摄影写生胜地。", "city": "咸丰县", "district": "朝阳寺镇"},
]

# ============================================================
# 2. 活动模板（政府文旅常见的活动类型）
# ============================================================
EVENT_TEMPLATES = [
    {"type": "文化节", "templates": [
        "{city}市第{n}届文化艺术节",
        "{city}非遗文化展示周",
        "\"{season}\"主题文化嘉年华",
        "{district}区民俗文化节",
        "{city}国际文化交流周",
    ]},
    {"type": "展览", "templates": [
        "\"翰墨{season}\"书画艺术展",
        "{city}历史文物精品展",
        "当代艺术邀请展——{season}篇",
        "{city}摄影大赛优秀作品展",
    ]},
    {"type": "演出", "templates": [
        "大型实景演出《梦回{spot}》",
        "{season}音乐会——民族管弦乐专场",
        "黄梅戏经典剧目《{spot}》展演",
        "{city}市民合唱节",
    ]},
    {"type": "体验活动", "templates": [
        "{spot}亲子研学一日游",
        "\"寻味{spot}\"美食体验活动",
        "{spot}汉服游园会",
        "\"手作{season}\"传统工艺体验营",
    ]},
    {"type": "节庆", "templates": [
        "{city}春节庙会",
        "{spot}元宵灯会",
        "{spot}中秋赏月诗会",
        "\"{season}之约\"{spot}花朝节",
    ]},
    {"type": "民俗体验", "templates": [
        "\"风情{spot}\"土家摆手舞大赛",
        "{spot}苗族银饰制作体验",
        "土家女儿会——{spot}相亲节",
        "{spot}牛王节祭祀大典",
        "\"寻味{spot}\"土家美食节",
    ]},
]

SEASONS = ["春", "夏", "秋", "冬"]
EVENT_EXTRA = ["土家摆手舞", "苗族银饰", "硒茶", "吊脚楼", "风雨桥", "西兰卡普",
               "恩施玉露", "油茶汤", "合渣", "社饭", "女儿会", "牛王节"]

# ============================================================
# 3. 建表 + 生成数据 + 写入
# ============================================================


def setup_tables(cursor):
    """创建景区、活动、预约三张表"""
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_TOURISM} "
                   "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.execute(f"USE {DB_TOURISM}")

    # 先删子表再删父表，避免外键约束报错
    cursor.execute("DROP TABLE IF EXISTS booking")
    cursor.execute("DROP TABLE IF EXISTS activity")
    cursor.execute("DROP TABLE IF EXISTS scenic_spot")

    # 景区表
    cursor.execute("""
        CREATE TABLE scenic_spot (
            id          INT AUTO_INCREMENT PRIMARY KEY COMMENT '景区ID',
            name        VARCHAR(100) NOT NULL        COMMENT '景区名称',
            category    VARCHAR(50)  NOT NULL        COMMENT '景区分类',
            city        VARCHAR(50)  DEFAULT '咸丰县' COMMENT '所在城市/县',
            district    VARCHAR(50)                   COMMENT '所在区县',
            latitude    DECIMAL(9,6)                  COMMENT '纬度',
            longitude   DECIMAL(9,6)                  COMMENT '经度',
            description TEXT                          COMMENT '景区简介',
            ticket_price DECIMAL(8,2) DEFAULT 0       COMMENT '门票价格（元）',
            opening_time VARCHAR(50)  DEFAULT '08:30' COMMENT '开放时间',
            closing_time VARCHAR(50)  DEFAULT '17:00' COMMENT '关闭时间',
            rating       DECIMAL(2,1) DEFAULT 4.0     COMMENT '评分（1-5）',
            visitor_count INT DEFAULT 0               COMMENT '累计访问量',
            status       TINYINT   DEFAULT 1          COMMENT '状态 1=开放 0=关闭',
            created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='景区信息表'
    """)

    # 活动表
    cursor.execute("""
        CREATE TABLE activity (
            id          INT AUTO_INCREMENT PRIMARY KEY COMMENT '活动ID',
            scenic_id   INT                           COMMENT '关联景区ID',
            title       VARCHAR(200) NOT NULL         COMMENT '活动标题',
            type        VARCHAR(50)  NOT NULL         COMMENT '活动类型',
            start_time  DATETIME    NOT NULL          COMMENT '开始时间',
            end_time    DATETIME    NOT NULL          COMMENT '结束时间',
            max_people  INT         DEFAULT 500       COMMENT '人数上限',
            description TEXT                           COMMENT '活动描述',
            status      TINYINT     DEFAULT 1          COMMENT '状态 1=进行中 0=已结束 2=未开始',
            created_at  DATETIME   DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (scenic_id) REFERENCES scenic_spot(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文旅活动表'
    """)

    # 用户预约表
    cursor.execute("""
        CREATE TABLE booking (
            id          INT AUTO_INCREMENT PRIMARY KEY COMMENT '预约ID',
            activity_id INT            NOT NULL        COMMENT '关联活动ID',
            user_name   VARCHAR(50)    NOT NULL        COMMENT '预约人姓名',
            user_phone  VARCHAR(20)    NOT NULL        COMMENT '预约人手机号',
            people_num  INT            DEFAULT 1       COMMENT '预约人数',
            visit_date  DATE           NOT NULL        COMMENT '参观日期',
            status      TINYINT        DEFAULT 0       COMMENT '0=待核销 1=已核销 2=已取消',
            created_at  DATETIME      DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (activity_id) REFERENCES activity(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='预约信息表'
    """)
    print("三张表创建完成: scenic_spot / activity / booking")


def generate_scenic_data(cursor):
    """生成 15 个景区数据"""
    records = []
    for spot in SCENIC_SPOTS:
        price = random.choice([0, 0, 0, 20, 30, 40, 50, 60, 80, 100, 120, 150])
        rating = round(random.uniform(3.5, 5.0), 1)
        visitors = random.randint(5000, 500000)
        records.append((
            spot["name"], spot["category"], spot["city"], spot["district"],
            spot["lat"], spot["lng"], spot["desc"], price,
            "08:00" if spot["category"] == "城市公园" else "08:30",
            "17:30" if spot["category"] == "城市公园" else "17:00",
            rating, visitors
        ))

    cursor.executemany("""
        INSERT INTO scenic_spot (name, category, city, district,
            latitude, longitude, description, ticket_price,
            opening_time, closing_time, rating, visitor_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, records)
    print(f"景区数据: {cursor.rowcount} 条")


def generate_activity_data(cursor):
    """为每个景区生成 2-4 个活动"""
    cursor.execute("SELECT id, name, category, city, district FROM scenic_spot")
    spots = cursor.fetchall()

    now = datetime.now()
    activity_records = []
    for spot_id, name, category, city, district in spots:
        # 每个景区随机 2-4 个活动
        for _ in range(random.randint(2, 4)):
            cat = random.choice(EVENT_TEMPLATES)
            templates = cat["templates"]
            tmpl = random.choice(templates)
            title = tmpl.format(
                n=random.randint(2, 8),
                season=random.choice(SEASONS),
                city=city,
                district=district,
                spot=name,
            )
            # 活动时间：未来 1-60 天内随机
            days_offset = random.randint(1, 60)
            start = now + timedelta(days=days_offset, hours=random.randint(8, 10))
            end = start + timedelta(days=random.choice([1, 3, 5, 7, 14]))
            status = 2 if days_offset > 7 else (1 if start <= now <= end else 0)
            activity_records.append((
                spot_id, title, cat["type"], start, end,
                random.choice([100, 200, 300, 500, 800, 1000]),
                f"{title}——活动详情请关注官方公众号或拨打咨询电话。"
            ))

    cursor.executemany("""
        INSERT INTO activity (scenic_id, title, type, start_time, end_time, max_people, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, activity_records)
    print(f"活动数据: {cursor.rowcount} 条")


def generate_booking_data(cursor):
    """生成 200 条用户预约记录"""
    cursor.execute("SELECT id, max_people FROM activity")
    activities = cursor.fetchall()

    surnames = ["王", "李", "张", "刘", "陈", "杨", "黄", "赵", "周", "吴",
                "徐", "孙", "马", "朱", "胡", "林", "郭", "何", "高", "罗"]
    given_names = ["伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "军", "洋",
                   "勇", "艳", "杰", "娟", "涛", "明", "超", "秀英", "华", "鑫"]

    booking_records = []
    for _ in range(200):
        act_id, max_p = random.choice(activities)
        name = random.choice(surnames) + random.choice(given_names)
        phone = f"1{random.randint(30,99)}{random.randint(10000000,99999999)}"
        people = random.randint(1, 5)
        visit_date = datetime.now() + timedelta(days=random.randint(0, 30))
        status = random.choices([0, 1, 2], weights=[6, 3, 1])[0]  # 60%待核销 30%已核销 10%已取消
        booking_records.append((act_id, name, phone, people,
                                visit_date.strftime("%Y-%m-%d"), status))

    cursor.executemany("""
        INSERT INTO booking (activity_id, user_name, user_phone, people_num, visit_date, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, booking_records)
    print(f"预约数据: {cursor.rowcount} 条")


def show_summary(cursor):
    """打印数据概览"""
    print("\n" + "=" * 60)
    print("                    数据概览")
    print("=" * 60)

    cursor.execute("SELECT COUNT(*) FROM scenic_spot")
    print(f"景区总数:   {cursor.fetchone()[0]}")

    cursor.execute("SELECT category, COUNT(*) FROM scenic_spot GROUP BY category")
    print("景区分类:")
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]}个")

    cursor.execute("SELECT COUNT(*), type FROM activity GROUP BY type")
    print("\n活动统计:")
    for row in cursor.fetchall():
        print(f"    {row[1]}: {row[0]}场")

    cursor.execute("SELECT COUNT(*) FROM booking")
    total_b = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM booking WHERE status = 0")
    pending = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM booking WHERE status = 1")
    checked = cursor.fetchone()[0]
    print(f"\n预约总数: {total_b}")
    print(f"    待核销: {pending} | 已核销: {checked} | 已取消: {total_b - pending - checked}")

    print("\n热门景区 TOP5 (按访问量):")
    cursor.execute("SELECT name, visitor_count, rating FROM scenic_spot "
                   "ORDER BY visitor_count DESC LIMIT 5")
    for row in cursor.fetchall():
        print(f"    {row[0]}  |  {row[1]:,}人次  |  评分{row[2]}")


# ============================================================
# 主流程
# ============================================================
if __name__ == "__main__":
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    setup_tables(cursor)
    generate_scenic_data(cursor)
    generate_activity_data(cursor)
    conn.commit()
    generate_booking_data(cursor)
    conn.commit()
    show_summary(cursor)

    cursor.close()
    conn.close()
    print(f"\n数据已写入数据库: {DB_TOURISM}")
    print(f"  景区表 scenic_spot: {cursor.rowcount} 条")
    print(f"快速查询:")
    print(f"  mysql> USE {DB_TOURISM};")
    print(f"  mysql> SELECT * FROM scenic_spot;")
    print(f"  mysql> SELECT * FROM activity;")
    print(f"  mysql> SELECT * FROM booking;")
