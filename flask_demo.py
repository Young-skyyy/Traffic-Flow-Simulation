# -*- coding: utf-8 -*-
"""Flask 最简示例 — 从数据库取数据，转成 JSON 返回给浏览器"""

# 第 1 步：导入两个库
from flask import Flask
import mysql.connector

# 第 2 步：创建 Flask App
app = Flask(__name__)

# 第 3 步：定义接口 → 访问 http://localhost:5000/demo 就会触发这个函数
@app.route("/demo")
def demo():
    # 第 4 步：连接数据库
    conn = mysql.connector.connect(
        host="localhost", port=3306,
        user="root", password="006527young",
        database="tourism_db", charset="utf8mb4",
    )
    # 第 5 步：查数据
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, category FROM scenic_spot LIMIT 3")
    spots = cursor.fetchall()
    cursor.close()
    conn.close()

    # 第 6 步：返回 JSON
    return {"status": "ok", "count": len(spots), "data": spots}

# 第 7 步：启动
if __name__ == "__main__":
    print("打开浏览器访问 http://localhost:5000/demo")
    app.run(port=5000)
