#!/usr/bin/env python3
"""
Mock服务器 - 基于OpenAPI规范自动生成mock响应
"""

import json
import random
import yaml
import sys
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
import argparse
import logging

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.swagger_api_agent.openapi_parser import OpenAPIParser

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockDataGenerator:
    """Mock数据生成器"""
    
    def __init__(self):
        self.fake_users = []
        self.fake_products = []
        self.fake_orders = []
        self.user_id_counter = 1
        self.product_id_counter = 1
        self.order_id_counter = 1
        self._init_fake_data()
    
    def _init_fake_data(self):
        """初始化虚拟数据"""
        # 生成虚拟用户
        names = ["张三", "李四", "王五", "赵六", "孙七", "周八", "吴九", "郑十"]
        roles = ["admin", "user", "guest"]
        
        for i, name in enumerate(names):
            user = {
                "id": self.user_id_counter,
                "name": name,
                "email": f"{name.replace('张', 'zhang').replace('李', 'li').replace('王', 'wang').replace('赵', 'zhao').replace('孙', 'sun').replace('周', 'zhou').replace('吴', 'wu').replace('郑', 'zheng')}{i+1}@example.com",
                "role": random.choice(roles),
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat()
            }
            self.fake_users.append(user)
            self.user_id_counter += 1
        
        # 生成虚拟产品
        products_data = [
            {"name": "智能手机", "category": "electronics", "price": 2999.99, "description": "最新款智能手机"},
            {"name": "笔记本电脑", "category": "electronics", "price": 5999.00, "description": "高性能笔记本电脑"},
            {"name": "无线耳机", "category": "electronics", "price": 299.50, "description": "降噪无线耳机"},
            {"name": "咖啡杯", "category": "home", "price": 49.99, "description": "陶瓷咖啡杯"},
            {"name": "运动鞋", "category": "sports", "price": 599.00, "description": "专业运动鞋"},
        ]
        
        for product_data in products_data:
            product = {
                "id": self.product_id_counter,
                **product_data
            }
            self.fake_products.append(product)
            self.product_id_counter += 1
        
        # 生成虚拟订单
        statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
        for i in range(5):
            order = {
                "id": self.order_id_counter,
                "userId": random.choice(self.fake_users)["id"],
                "items": [
                    {
                        "productId": random.choice(self.fake_products)["id"],
                        "quantity": random.randint(1, 3),
                        "price": random.uniform(50, 1000)
                    }
                ],
                "total": random.uniform(100, 3000),
                "status": random.choice(statuses),
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
            }
            self.fake_orders.append(order)
            self.order_id_counter += 1

    def get_users(self, page=1, limit=10, role=None):
        """获取用户列表"""
        filtered_users = self.fake_users
        if role:
            filtered_users = [u for u in filtered_users if u["role"] == role]
        
        start = (page - 1) * limit
        end = start + limit
        users_page = filtered_users[start:end]
        
        return {
            "users": users_page,
            "total": len(filtered_users),
            "page": page,
            "limit": limit
        }
    
    def get_user_by_id(self, user_id):
        """根据ID获取用户"""
        for user in self.fake_users:
            if user["id"] == user_id:
                return user
        return None
    
    def create_user(self, user_data):
        """创建用户"""
        new_user = {
            "id": self.user_id_counter,
            "name": user_data["name"],
            "email": user_data["email"],
            "role": user_data.get("role", "user"),
            "created_at": datetime.now().isoformat()
        }
        self.fake_users.append(new_user)
        self.user_id_counter += 1
        return new_user
    
    def update_user(self, user_id, user_data):
        """更新用户"""
        for i, user in enumerate(self.fake_users):
            if user["id"] == user_id:
                if "name" in user_data:
                    user["name"] = user_data["name"]
                if "email" in user_data:
                    user["email"] = user_data["email"]
                if "role" in user_data:
                    user["role"] = user_data["role"]
                return user
        return None
    
    def delete_user(self, user_id):
        """删除用户"""
        for i, user in enumerate(self.fake_users):
            if user["id"] == user_id:
                del self.fake_users[i]
                return True
        return False
    
    def get_products(self, category=None, search=None, min_price=None, max_price=None):
        """获取产品列表"""
        filtered_products = self.fake_products
        
        if category:
            filtered_products = [p for p in filtered_products if p["category"] == category]
        
        if search:
            filtered_products = [p for p in filtered_products 
                               if search.lower() in p["name"].lower() or 
                                  search.lower() in p["description"].lower()]
        
        if min_price is not None:
            filtered_products = [p for p in filtered_products if p["price"] >= min_price]
        
        if max_price is not None:
            filtered_products = [p for p in filtered_products if p["price"] <= max_price]
        
        return filtered_products
    
    def create_order(self, order_data):
        """创建订单"""
        # 计算总价
        total = 0
        for item in order_data["items"]:
            product = next((p for p in self.fake_products if p["id"] == item["productId"]), None)
            if product:
                item["price"] = product["price"]
                total += product["price"] * item["quantity"]
        
        new_order = {
            "id": self.order_id_counter,
            "userId": order_data["userId"],
            "items": order_data["items"],
            "total": total,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        self.fake_orders.append(new_order)
        self.order_id_counter += 1
        return new_order


class MockServer:
    """Mock服务器"""
    
    def __init__(self, openapi_file):
        self.app = Flask(__name__)
        CORS(self.app)  # 启用CORS
        
        # 初始化数据生成器
        self.data_generator = MockDataGenerator()
        
        # 解析OpenAPI规范
        self.parser = OpenAPIParser(openapi_file)
        
        # 注册路由
        self._register_routes()
    
    def _register_routes(self):
        """注册路由"""
        
        # 用户相关接口
        @self.app.route('/users', methods=['GET'])
        def get_users():
            page = int(request.args.get('page', 1))
            limit = int(request.args.get('limit', 10))
            role = request.args.get('role')
            
            logger.info(f"GET /users - page: {page}, limit: {limit}, role: {role}")
            
            result = self.data_generator.get_users(page, limit, role)
            return jsonify(result)
        
        @self.app.route('/users', methods=['POST'])
        def create_user():
            user_data = request.get_json()
            logger.info(f"POST /users - data: {user_data}")
            
            # 验证必填字段
            if not user_data or 'name' not in user_data or 'email' not in user_data:
                return jsonify({"error": "name and email are required"}), 400
            
            new_user = self.data_generator.create_user(user_data)
            return jsonify(new_user), 201
        
        @self.app.route('/users/<int:user_id>', methods=['GET'])
        def get_user_by_id(user_id):
            logger.info(f"GET /users/{user_id}")
            
            user = self.data_generator.get_user_by_id(user_id)
            if user:
                return jsonify(user)
            else:
                return jsonify({"error": "User not found"}), 404
        
        @self.app.route('/users/<int:user_id>', methods=['PUT'])
        def update_user(user_id):
            user_data = request.get_json()
            logger.info(f"PUT /users/{user_id} - data: {user_data}")
            
            updated_user = self.data_generator.update_user(user_id, user_data)
            if updated_user:
                return jsonify(updated_user)
            else:
                return jsonify({"error": "User not found"}), 404
        
        @self.app.route('/users/<int:user_id>', methods=['DELETE'])
        def delete_user(user_id):
            logger.info(f"DELETE /users/{user_id}")
            
            if self.data_generator.delete_user(user_id):
                return '', 204
            else:
                return jsonify({"error": "User not found"}), 404
        
        # 产品相关接口
        @self.app.route('/products', methods=['GET'])
        def get_products():
            category = request.args.get('category')
            search = request.args.get('search')
            min_price = request.args.get('min_price', type=float)
            max_price = request.args.get('max_price', type=float)
            
            logger.info(f"GET /products - category: {category}, search: {search}, min_price: {min_price}, max_price: {max_price}")
            
            products = self.data_generator.get_products(category, search, min_price, max_price)
            return jsonify(products)
        
        # 订单相关接口
        @self.app.route('/orders', methods=['POST'])
        def create_order():
            order_data = request.get_json()
            logger.info(f"POST /orders - data: {order_data}")
            
            # 验证必填字段
            if not order_data or 'userId' not in order_data or 'items' not in order_data:
                return jsonify({"error": "userId and items are required"}), 400
            
            new_order = self.data_generator.create_order(order_data)
            return jsonify(new_order), 201
        
        # 健康检查接口
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "message": "Mock server is running"
            })
        
        # API文档接口
        @self.app.route('/docs', methods=['GET'])
        def api_docs():
            try:
                with open('example_openapi.yaml', 'r', encoding='utf-8') as f:
                    openapi_content = f.read()
                return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Mock API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.25.0/swagger-ui.css" />
    <style>
        html {{ box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }}
        *, *:before, *:after {{ box-sizing: inherit; }}
        body {{ margin:0; background: #fafafa; }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@3.25.0/swagger-ui-bundle.js"></script>
    <script>
        SwaggerUIBundle({{
            url: '/openapi.yaml',
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.presets.standalone
            ],
            plugins: [
                SwaggerUIBundle.plugins.DownloadUrl
            ],
            layout: "StandaloneLayout"
        }});
    </script>
</body>
</html>
                """
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/openapi.yaml', methods=['GET'])
        def openapi_spec():
            try:
                with open('example_openapi.yaml', 'r', encoding='utf-8') as f:
                    content = f.read()
                return content, 200, {'Content-Type': 'text/yaml'}
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    
    def run(self, host='127.0.0.1', port=8080, debug=True):
        """启动服务器"""
        print(f"""
🚀 Mock服务器启动成功！

📍 服务地址: http://{host}:{port}
📖 API文档: http://{host}:{port}/docs
🔍 健康检查: http://{host}:{port}/health
📋 OpenAPI规范: http://{host}:{port}/openapi.yaml

可用的接口:
- GET  /users              - 获取用户列表
- POST /users              - 创建用户
- GET  /users/{{id}}         - 获取指定用户
- PUT  /users/{{id}}         - 更新用户信息
- DELETE /users/{{id}}       - 删除用户
- GET  /products           - 获取产品列表
- POST /orders             - 创建订单
- GET  /health             - 健康检查
- GET  /docs               - API文档
        """)
        
        self.app.run(host=host, port=port, debug=debug)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='OpenAPI Mock Server')
    parser.add_argument('--openapi', '-f', default='example_openapi.yaml',
                       help='OpenAPI规范文件路径 (默认: example_openapi.yaml)')
    parser.add_argument('--host', default='127.0.0.1',
                       help='服务器主机地址 (默认: 127.0.0.1)')
    parser.add_argument('--port', '-p', type=int, default=8080,
                       help='服务器端口 (默认: 8080)')
    parser.add_argument('--debug', action='store_true',
                       help='启用调试模式')
    
    args = parser.parse_args()
    
    try:
        # 创建并启动mock服务器
        mock_server = MockServer(args.openapi)
        mock_server.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动服务器时出错: {e}")


if __name__ == '__main__':
    main()
