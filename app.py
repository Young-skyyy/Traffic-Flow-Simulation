# -*- coding: utf-8 -*-
"""
咸丰县智慧文旅平台 - 后端 API
提供景区查询、活动浏览、预约提交等接口
运行: python app.py
"""

from flask import Flask, jsonify, request
import mysql.connector
from config import DB_CONFIG, DB_TOURISM, SERVER_HOST, SERVER_PORT, DEBUG

app = Flask(__name__)

DB_CONFIG["database"] = DB_TOURISM


# ============================================================
# 工具函数：获取数据库连接
# ============================================================


def get_db():
    """获取数据库连接，失败时统一返回错误"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as e:
        return None


def db_error_response():
    return jsonify({"code": 500, "message": "数据库连接失败，请稍后重试"}), 500


# ============================================================
# 全局错误处理
# ============================================================


@app.errorhandler(404)
def not_found(e):
    return jsonify({"code": 404, "message": "接口不存在"}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"code": 500, "message": "服务器内部错误"}), 500


@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"未捕获异常: {str(e)}")
    return jsonify({"code": 500, "message": "服务暂不可用"}), 500


# ============================================================
# 景区相关接口
# ============================================================


@app.route("/api/scenic", methods=["GET"])
def get_scenic_spots():
    """景区列表（仅返回摘要，不含长文本描述）"""
    category = request.args.get("category")
    keyword = request.args.get("keyword")

    conn = get_db()
    if not conn:
        return db_error_response()

    try:
        cursor = conn.cursor(dictionary=True)

        sql = """SELECT id, name, category, district, latitude, longitude,
                        ticket_price, rating, visitor_count
                 FROM scenic_spot WHERE 1=1"""
        params = []

        if category:
            sql += " AND category = %s"
            params.append(category)
        if keyword:
            sql += " AND (name LIKE %s OR district LIKE %s)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])

        sql += " ORDER BY rating DESC"
        cursor.execute(sql, params)
        spots = cursor.fetchall()

        return jsonify({"code": 200, "total": len(spots), "data": spots})

    except mysql.connector.Error as e:
        app.logger.error(f"景区列表查询失败: {e}")
        return jsonify({"code": 500, "message": "查询失败"}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/api/scenic/<int:spot_id>", methods=["GET"])
def get_scenic_detail(spot_id):
    """景区详情（含完整描述和关联活动）"""
    conn = get_db()
    if not conn:
        return db_error_response()

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM scenic_spot WHERE id = %s", (spot_id,))
        spot = cursor.fetchone()

        if not spot:
            return jsonify({"code": 404, "message": "景区不存在"}), 404

        cursor.execute(
            """SELECT id, title, type, start_time, end_time, max_people, status
               FROM activity WHERE scenic_id = %s ORDER BY start_time""",
            (spot_id,),
        )
        spot["activities"] = cursor.fetchall()

        return jsonify({"code": 200, "data": spot})

    except mysql.connector.Error as e:
        app.logger.error(f"景区详情查询失败: {e}")
        return jsonify({"code": 500, "message": "查询失败"}), 500
    finally:
        cursor.close()
        conn.close()


# ============================================================
# 活动相关接口
# ============================================================


@app.route("/api/activity", methods=["GET"])
def get_activities():
    """活动列表，支持按类型/景区筛选"""
    scenic_id = request.args.get("scenic_id")
    act_type = request.args.get("type")

    conn = get_db()
    if not conn:
        return db_error_response()

    try:
        cursor = conn.cursor(dictionary=True)

        sql = """
            SELECT a.id, a.title, a.type, a.start_time, a.end_time,
                   a.max_people, a.status, s.name AS scenic_name
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

        return jsonify({"code": 200, "total": len(activities), "data": activities})

    except mysql.connector.Error as e:
        app.logger.error(f"活动列表查询失败: {e}")
        return jsonify({"code": 500, "message": "查询失败"}), 500
    finally:
        cursor.close()
        conn.close()


# ============================================================
# 预约相关接口
# ============================================================


@app.route("/api/booking", methods=["POST"])
def create_booking():
    """提交预约"""
    data = request.get_json()

    required = ["activity_id", "user_name", "user_phone", "people_num", "visit_date"]
    for field in required:
        if field not in data or not data[field]:
            return jsonify({"code": 400, "message": f"缺少必填字段: {field}"}), 400

    conn = get_db()
    if not conn:
        return db_error_response()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO booking (activity_id, user_name, user_phone,
               people_num, visit_date) VALUES (%s, %s, %s, %s, %s)""",
            (data["activity_id"], data["user_name"], data["user_phone"],
             data["people_num"], data["visit_date"]),
        )
        conn.commit()
        booking_id = cursor.lastrowid

        return jsonify({"code": 200, "message": "预约成功", "booking_id": booking_id})

    except mysql.connector.Error as e:
        app.logger.error(f"预约提交失败: {e}")
        conn.rollback()
        return jsonify({"code": 500, "message": "预约失败，请稍后重试"}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/api/booking", methods=["GET"])
def get_bookings():
    """查询预约列表"""
    conn = get_db()
    if not conn:
        return db_error_response()

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.id, b.user_name, b.user_phone, b.people_num,
                   b.visit_date, b.status, a.title AS activity_title
            FROM booking b
            LEFT JOIN activity a ON b.activity_id = a.id
            ORDER BY b.created_at DESC LIMIT 50
        """)
        bookings = cursor.fetchall()

        return jsonify({"code": 200, "total": len(bookings), "data": bookings})

    except mysql.connector.Error as e:
        app.logger.error(f"预约查询失败: {e}")
        return jsonify({"code": 500, "message": "查询失败"}), 500
    finally:
        cursor.close()
        conn.close()


# ============================================================
# 统计接口
# ============================================================


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """平台统计看板"""
    conn = get_db()
    if not conn:
        return db_error_response()

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) AS total FROM scenic_spot")
        scenic_count = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM activity")
        activity_count = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM booking")
        booking_count = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT category, COUNT(*) AS cnt FROM scenic_spot "
            "GROUP BY category ORDER BY cnt DESC"
        )
        categories = cursor.fetchall()

        return jsonify({
            "code": 200,
            "data": {
                "scenic_count": scenic_count,
                "activity_count": activity_count,
                "booking_count": booking_count,
                "categories": categories,
            },
        })

    except mysql.connector.Error as e:
        app.logger.error(f"统计查询失败: {e}")
        return jsonify({"code": 500, "message": "查询失败"}), 500
    finally:
        cursor.close()
        conn.close()


# ============================================================
# 启动
# ============================================================
if __name__ == "__main__":
    print(f"""
╔═══════════════════════════════════════════╗
║   咸丰县智慧文旅平台 API 已启动            ║
╠═══════════════════════════════════════════╣
║  景区列表:  http://localhost:{SERVER_PORT}/api/scenic    ║
║  景区详情:  http://localhost:{SERVER_PORT}/api/scenic/1  ║
║  活动列表:  http://localhost:{SERVER_PORT}/api/activity   ║
║  预约提交:  POST http://localhost:{SERVER_PORT}/api/booking║
║  预约查询:  http://localhost:{SERVER_PORT}/api/booking    ║
║  统计看板:  http://localhost:{SERVER_PORT}/api/stats      ║
╚═══════════════════════════════════════════╝
    """)
    app.run(debug=DEBUG, host=SERVER_HOST, port=SERVER_PORT)
