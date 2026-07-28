# -*- coding: utf-8 -*-
"""
咸丰县智慧文旅平台 - 后端 API
提供景区查询、活动浏览、预约提交等接口
运行: python app.py
"""

from flask import Flask, jsonify, request
import mysql.connector

app = Flask(__name__)

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "921129YYmnqnb",
    "database": "tourism_db",
    "charset": "utf8mb4",
}

# ============================================================
# 景区相关接口
# ============================================================


@app.route("/api/scenic", methods=["GET"])
def get_scenic_spots():
    """获取所有景区列表，支持按分类筛选"""
    category = request.args.get("category")  # ?category=自然风光
    keyword = request.args.get("keyword")    # ?keyword=咸丰

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    sql = "SELECT id, name, category, district, latitude, longitude, description, ticket_price, rating, visitor_count FROM scenic_spot WHERE 1=1"
    params = []

    if category:
        sql += " AND category = %s"
        params.append(category)
    if keyword:
        sql += " AND (name LIKE %s OR description LIKE %s)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    sql += " ORDER BY rating DESC"

    cursor.execute(sql, params)
    spots = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"code": 200, "total": len(spots), "data": spots})


@app.route("/api/scenic/<int:spot_id>", methods=["GET"])
def get_scenic_detail(spot_id):
    """获取单个景区详情"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM scenic_spot WHERE id = %s", (spot_id,))
    spot = cursor.fetchone()

    if not spot:
        cursor.close()
        conn.close()
        return jsonify({"code": 404, "message": "景区不存在"}), 404

    # 查关联活动
    cursor.execute(
        "SELECT id, title, type, start_time, end_time, max_people, status FROM activity WHERE scenic_id = %s ORDER BY start_time",
        (spot_id,),
    )
    activities = cursor.fetchall()

    spot["activities"] = activities

    cursor.close()
    conn.close()

    return jsonify({"code": 200, "data": spot})


# ============================================================
# 活动相关接口
# ============================================================


@app.route("/api/activity", methods=["GET"])
def get_activities():
    """获取活动列表，支持按类型/景区筛选"""
    scenic_id = request.args.get("scenic_id")
    act_type = request.args.get("type")

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT a.id, a.title, a.type, a.start_time, a.end_time, a.max_people, a.status,
               s.name AS scenic_name, s.category AS scenic_category
        FROM activity a
        LEFT JOIN scenic_spot s ON a.scenic_id = s.id
        WHERE 1=1
    """
    params = []

    if scenic_id:
        sql += " AND a.scenic_id = %s"
        params.append(scenic_id)
    if act_type:
        sql += " AND a.type = %s"
        params.append(act_type)

    sql += " ORDER BY a.start_time"
    cursor.execute(sql, params)
    activities = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"code": 200, "total": len(activities), "data": activities})


# ============================================================
# 预约相关接口
# ============================================================


@app.route("/api/booking", methods=["POST"])
def create_booking():
    """提交预约"""
    data = request.get_json()

    # 必填字段校验
    required = ["activity_id", "user_name", "user_phone", "people_num", "visit_date"]
    for field in required:
        if field not in data or not data[field]:
            return jsonify({"code": 400, "message": f"缺少必填字段: {field}"}), 400

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO booking (activity_id, user_name, user_phone, people_num, visit_date) VALUES (%s, %s, %s, %s, %s)",
        (data["activity_id"], data["user_name"], data["user_phone"], data["people_num"], data["visit_date"]),
    )
    conn.commit()
    booking_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return jsonify({"code": 200, "message": "预约成功", "booking_id": booking_id})


@app.route("/api/booking", methods=["GET"])
def get_bookings():
    """查询预约列表"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT b.id, b.user_name, b.user_phone, b.people_num, b.visit_date, b.status,
               a.title AS activity_title
        FROM booking b
        LEFT JOIN activity a ON b.activity_id = a.id
        ORDER BY b.created_at DESC
        LIMIT 50
    """)
    bookings = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"code": 200, "total": len(bookings), "data": bookings})


# ============================================================
# 统计接口
# ============================================================


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """获取平台统计数据（给大屏展示用）"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM scenic_spot")
    scenic_count = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM activity")
    activity_count = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM booking")
    booking_count = cursor.fetchone()["total"]

    cursor.execute("SELECT category, COUNT(*) AS cnt FROM scenic_spot GROUP BY category ORDER BY cnt DESC")
    categories = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        "code": 200,
        "data": {
            "scenic_count": scenic_count,
            "activity_count": activity_count,
            "booking_count": booking_count,
            "categories": categories,
        },
    })


# ============================================================
# 启动
# ============================================================
if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════╗
║   咸丰县智慧文旅平台 API 已启动              ║
╠═══════════════════════════════════════════╣
║  景区列表:  http://localhost:5000/api/scenic           ║
║  景区详情:  http://localhost:5000/api/scenic/1         ║
║  活动列表:  http://localhost:5000/api/activity          ║
║  提交预约:  POST http://localhost:5000/api/booking      ║
║  预约查询:  http://localhost:5000/api/booking           ║
║  统计看板:  http://localhost:5000/api/stats             ║
╚═══════════════════════════════════════════╝
    """)
    app.run(debug=True, host="0.0.0.0", port=5000)
