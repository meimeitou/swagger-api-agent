#!/usr/bin/env python3
"""
简化版Mock服务器 - 专门为example_openapi.yaml设计
不依赖openapi_parser，直接实现接口
"""

import json
import random
import argparse
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 虚拟数据存储
fake_data = {
    "users": [],
    "products": [],
    "orders": [],
    "counters": {
        "user_id": 1,
        "product_id": 1,
        "order_id": 1
    }
}

def init_fake_data():
    """初始化虚拟数据"""
    # 生成虚拟用户
    users_data = [
        {"name": "张三", "email": "zhangsan@example.com", "role": "admin"},
        {"name": "李四", "email": "lisi@example.com", "role": "user"},
        {"name": "王五", "email": "wangwu@example.com", "role": "user"},
        {"name": "赵六", "email": "zhaoliu@example.com", "role": "guest"},
        {"name": "孙七", "email": "sunqi@example.com", "role": "user"},
    ]
    
    for user_data in users_data:
        user = {
            "id": fake_data["counters"]["user_id"],
            "name": user_data["name"],
            "email": user_data["email"],
            "role": user_data["role"],
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat()
        }
        fake_data["users"].append(user)
        fake_data["counters"]["user_id"] += 1
    
    # 生成虚拟产品
    products_data = [
        {"name": "iPhone 15", "category": "electronics", "price": 5999.00, "description": "最新款iPhone"},
        {"name": "MacBook Pro", "category": "electronics", "price": 12999.00, "description": "专业笔记本电脑"},
        {"name": "AirPods Pro", "category": "electronics", "price": 1899.00, "description": "主动降噪耳机"},
        {"name": "咖啡机", "category": "home", "price": 899.00, "description": "自动咖啡机"},
        {"name": "跑步鞋", "category": "sports", "price": 599.00, "description": "专业跑步鞋"},
        {"name": "平板电脑", "category": "electronics", "price": 3299.00, "description": "轻薄平板"},
    ]
    
    for product_data in products_data:
        product = {
            "id": fake_data["counters"]["product_id"],
            **product_data
        }
        fake_data["products"].append(product)
        fake_data["counters"]["product_id"] += 1
    
    # 生成虚拟订单
    statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
    for i in range(8):
        user_id = random.choice(fake_data["users"])["id"]
        num_items = random.randint(1, 3)
        items = []
        total = 0
        
        for _ in range(num_items):
            product = random.choice(fake_data["products"])
            quantity = random.randint(1, 3)
            items.append({
                "productId": product["id"],
                "quantity": quantity,
                "price": product["price"]
            })
            total += product["price"] * quantity
        
        order = {
            "id": fake_data["counters"]["order_id"],
            "userId": user_id,
            "items": items,
            "total": round(total, 2),
            "status": random.choice(statuses),
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
        }
        fake_data["orders"].append(order)
        fake_data["counters"]["order_id"] += 1

# 用户接口
@app.route('/users', methods=['GET'])
def get_users():
    """获取用户列表"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    role = request.args.get('role')
    
    logger.info(f"GET /users - page: {page}, limit: {limit}, role: {role}")
    
    # 过滤用户
    filtered_users = fake_data["users"]
    if role:
        filtered_users = [u for u in filtered_users if u["role"] == role]
    
    # 分页
    start = (page - 1) * limit
    end = start + limit
    users_page = filtered_users[start:end]
    
    result = {
        "users": users_page,
        "total": len(filtered_users),
        "page": page,
        "limit": limit
    }
    
    return jsonify(result)

@app.route('/users', methods=['POST'])
def create_user():
    """创建用户"""
    user_data = request.get_json()
    logger.info(f"POST /users - data: {user_data}")
    
    # 验证必填字段
    if not user_data or 'name' not in user_data or 'email' not in user_data:
        return jsonify({"error": "name and email are required"}), 400
    
    # 检查邮箱是否已存在
    for user in fake_data["users"]:
        if user["email"] == user_data["email"]:
            return jsonify({"error": "Email already exists"}), 409
    
    # 创建新用户
    new_user = {
        "id": fake_data["counters"]["user_id"],
        "name": user_data["name"],
        "email": user_data["email"],
        "role": user_data.get("role", "user"),
        "created_at": datetime.now().isoformat()
    }
    
    fake_data["users"].append(new_user)
    fake_data["counters"]["user_id"] += 1
    
    return jsonify(new_user), 201

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    """获取指定用户"""
    logger.info(f"GET /users/{user_id}")
    
    for user in fake_data["users"]:
        if user["id"] == user_id:
            return jsonify(user)
    
    return jsonify({"error": "User not found"}), 404

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """更新用户信息"""
    user_data = request.get_json()
    logger.info(f"PUT /users/{user_id} - data: {user_data}")
    
    for user in fake_data["users"]:
        if user["id"] == user_id:
            # 检查邮箱重复（如果要更新邮箱）
            if "email" in user_data and user_data["email"] != user["email"]:
                for other_user in fake_data["users"]:
                    if other_user["id"] != user_id and other_user["email"] == user_data["email"]:
                        return jsonify({"error": "Email already exists"}), 409
            
            # 更新字段
            if "name" in user_data:
                user["name"] = user_data["name"]
            if "email" in user_data:
                user["email"] = user_data["email"]
            if "role" in user_data:
                user["role"] = user_data["role"]
            
            return jsonify(user)
    
    return jsonify({"error": "User not found"}), 404

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """删除用户"""
    logger.info(f"DELETE /users/{user_id}")
    
    for i, user in enumerate(fake_data["users"]):
        if user["id"] == user_id:
            del fake_data["users"][i]
            return '', 204
    
    return jsonify({"error": "User not found"}), 404

# 产品接口
@app.route('/products', methods=['GET'])
def get_products():
    """获取产品列表"""
    category = request.args.get('category')
    search = request.args.get('search')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    logger.info(f"GET /products - category: {category}, search: {search}, min_price: {min_price}, max_price: {max_price}")
    
    # 过滤产品
    filtered_products = fake_data["products"]
    
    if category:
        filtered_products = [p for p in filtered_products if p["category"] == category]
    
    if search:
        search_lower = search.lower()
        filtered_products = [p for p in filtered_products 
                           if search_lower in p["name"].lower() or 
                              search_lower in p["description"].lower()]
    
    if min_price is not None:
        filtered_products = [p for p in filtered_products if p["price"] >= min_price]
    
    if max_price is not None:
        filtered_products = [p for p in filtered_products if p["price"] <= max_price]
    
    return jsonify(filtered_products)

# 订单接口
@app.route('/orders', methods=['POST'])
def create_order():
    """创建订单"""
    order_data = request.get_json()
    logger.info(f"POST /orders - data: {order_data}")
    
    # 验证必填字段
    if not order_data or 'userId' not in order_data or 'items' not in order_data:
        return jsonify({"error": "userId and items are required"}), 400
    
    # 验证用户是否存在
    user_exists = any(u["id"] == order_data["userId"] for u in fake_data["users"])
    if not user_exists:
        return jsonify({"error": "User not found"}), 404
    
    # 验证并计算订单总价
    total = 0
    validated_items = []
    
    for item in order_data["items"]:
        if "productId" not in item or "quantity" not in item:
            return jsonify({"error": "Each item must have productId and quantity"}), 400
        
        # 查找产品
        product = next((p for p in fake_data["products"] if p["id"] == item["productId"]), None)
        if not product:
            return jsonify({"error": f"Product {item['productId']} not found"}), 404
        
        if item["quantity"] < 1:
            return jsonify({"error": "Quantity must be at least 1"}), 400
        
        validated_item = {
            "productId": item["productId"],
            "quantity": item["quantity"],
            "price": product["price"]
        }
        validated_items.append(validated_item)
        total += product["price"] * item["quantity"]
    
    # 创建新订单
    new_order = {
        "id": fake_data["counters"]["order_id"],
        "userId": order_data["userId"],
        "items": validated_items,
        "total": round(total, 2),
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    fake_data["orders"].append(new_order)
    fake_data["counters"]["order_id"] += 1
    
    return jsonify(new_order), 201

# 辅助接口
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "Mock server is running",
        "data_summary": {
            "users": len(fake_data["users"]),
            "products": len(fake_data["products"]),
            "orders": len(fake_data["orders"])
        }
    })

@app.route('/reset', methods=['POST'])
def reset_data():
    """重置数据"""
    logger.info("POST /reset - Resetting all data")
    
    fake_data["users"].clear()
    fake_data["products"].clear()
    fake_data["orders"].clear()
    fake_data["counters"] = {"user_id": 1, "product_id": 1, "order_id": 1}
    
    init_fake_data()
    
    return jsonify({
        "message": "Data reset successfully",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/data', methods=['GET'])
def get_all_data():
    """获取所有数据（调试用）"""
    return jsonify(fake_data)

@app.route('/', methods=['GET'])
def root():
    """根路径 - API说明"""
    return jsonify({
        "name": "OpenAPI Mock Server",
        "version": "1.0.0",
        "description": "基于example_openapi.yaml的Mock服务",
        "endpoints": {
            "users": {
                "GET /users": "获取用户列表（支持分页和角色筛选）",
                "POST /users": "创建新用户",
                "GET /users/{id}": "获取指定用户",
                "PUT /users/{id}": "更新用户信息",
                "DELETE /users/{id}": "删除用户"
            },
            "products": {
                "GET /products": "获取产品列表（支持分类、搜索、价格筛选）"
            },
            "orders": {
                "POST /orders": "创建订单"
            },
            "utilities": {
                "GET /health": "健康检查",
                "POST /reset": "重置所有数据",
                "GET /data": "获取所有数据（调试用）"
            }
        },
        "documentation": "请参考example_openapi.yaml文件"
    })

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='简化版OpenAPI Mock Server')
    parser.add_argument('--host', default='127.0.0.1', help='服务器主机地址')
    parser.add_argument('--port', '-p', type=int, default=8080, help='服务器端口')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    args = parser.parse_args()
    
    # 初始化虚拟数据
    init_fake_data()
    
    print(f"""
🚀 Mock服务器启动成功！

📍 服务地址: http://{args.host}:{args.port}
🔍 健康检查: http://{args.host}:{args.port}/health
📋 API说明: http://{args.host}:{args.port}/
🔄 重置数据: POST http://{args.host}:{args.port}/reset

📚 可用的接口:
┌─────────────────────────────────────────────────────────────┐
│ 用户管理                                                      │
├─────────────────────────────────────────────────────────────┤
│ GET    /users              - 获取用户列表                      │
│ POST   /users              - 创建用户                        │
│ GET    /users/{{id}}         - 获取指定用户                    │
│ PUT    /users/{{id}}         - 更新用户信息                    │
│ DELETE /users/{{id}}         - 删除用户                       │
├─────────────────────────────────────────────────────────────┤
│ 产品管理                                                      │
├─────────────────────────────────────────────────────────────┤
│ GET    /products           - 获取产品列表                      │
├─────────────────────────────────────────────────────────────┤
│ 订单管理                                                      │
├─────────────────────────────────────────────────────────────┤
│ POST   /orders             - 创建订单                        │
├─────────────────────────────────────────────────────────────┤
│ 工具接口                                                      │
├─────────────────────────────────────────────────────────────┤
│ GET    /health             - 健康检查                        │
│ POST   /reset              - 重置数据                        │
│ GET    /data               - 查看所有数据                      │
└─────────────────────────────────────────────────────────────┘

💡 使用示例:
   curl http://{args.host}:{args.port}/users
   curl -X POST http://{args.host}:{args.port}/users -H "Content-Type: application/json" -d '{{"name":"测试用户","email":"test@example.com"}}'
        """)
    
    try:
        app.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")

if __name__ == '__main__':
    main()
