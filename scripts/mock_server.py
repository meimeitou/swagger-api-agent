#!/usr/bin/env python3
"""
Mock服务器 - 基于OpenAPI规范自动生成mock响应
"""

import json
import random
import yaml
import sys
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
import argparse
import logging
from functools import wraps

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
        self.user_tokens = {}  # 存储用户令牌
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
            # 创建纯英文的email地址
            email_map = {
                "张三": "zhang3",
                "李四": "li4", 
                "王五": "wang5",
                "赵六": "zhao6",
                "孙七": "sun7",
                "周八": "zhou8",
                "吴九": "wu9", 
                "郑十": "zheng10"
            }
            user = {
                "id": self.user_id_counter,
                "name": name,
                "email": f"{email_map[name]}{i+1}@example.com",
                "role": random.choice(roles),
                "password": self._hash_password("password123"),  # 默认密码
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

    def _hash_password(self, password):
        """简单的密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_token(self):
        """生成随机令牌"""
        return secrets.token_hex(32)
    
    def authenticate_user(self, email, password):
        """用户认证"""
        for user in self.fake_users:
            if user["email"] == email and user["password"] == self._hash_password(password):
                # 生成令牌
                token = self._generate_token()
                self.user_tokens[token] = {
                    "user_id": user["id"],
                    "expires_at": datetime.now() + timedelta(hours=1)
                }
                return {
                    "access_token": token,
                    "token_type": "Bearer",
                    "expires_in": 3600,
                    "user": {k: v for k, v in user.items() if k != "password"}
                }
        return None
    
    def validate_token(self, token):
        """验证令牌"""
        if token in self.user_tokens:
            token_data = self.user_tokens[token]
            if datetime.now() < token_data["expires_at"]:
                return token_data["user_id"]
            else:
                # 令牌已过期，删除它
                del self.user_tokens[token]
        return None
    
    def refresh_token(self, token):
        """刷新令牌"""
        user_id = self.validate_token(token)
        if user_id:
            # 删除旧令牌
            del self.user_tokens[token]
            # 生成新令牌
            new_token = self._generate_token()
            self.user_tokens[new_token] = {
                "user_id": user_id,
                "expires_at": datetime.now() + timedelta(hours=1)
            }
            return {
                "access_token": new_token,
                "token_type": "Bearer",
                "expires_in": 3600
            }
        return None

    def get_users(self, page=1, limit=10, role=None):
        """获取用户列表"""
        filtered_users = self.fake_users
        if role:
            filtered_users = [u for u in filtered_users if u["role"] == role]
        
        start = (page - 1) * limit
        end = start + limit
        users_page = filtered_users[start:end]
        
        # 移除密码字段
        safe_users = []
        for user in users_page:
            safe_user = {k: v for k, v in user.items() if k != "password"}
            safe_users.append(safe_user)
        
        return {
            "users": safe_users,
            "total": len(filtered_users),
            "page": page,
            "limit": limit
        }
    
    def get_user_by_id(self, user_id):
        """根据ID获取用户"""
        for user in self.fake_users:
            if user["id"] == user_id:
                # 移除密码字段
                return {k: v for k, v in user.items() if k != "password"}
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
                # 移除密码字段
                return {k: v for k, v in user.items() if k != "password"}
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
        
        # 配置Flask确保中文正确显示
        self.app.config['JSON_AS_ASCII'] = False
        self.app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
        self.app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'
        
        # 初始化数据生成器
        self.data_generator = MockDataGenerator()
        
        # 解析OpenAPI规范
        self.parser = OpenAPIParser(openapi_file)
        
        # 注册路由
        self._register_routes()
    
    def _json_response(self, data, status_code=200):
        """创建正确编码的JSON响应"""
        response = self.app.response_class(
            json.dumps(data, ensure_ascii=False, indent=2),
            status=status_code,
            mimetype='application/json; charset=utf-8'
        )
        return response
    
    def _require_auth(self, f):
        """认证装饰器"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "Authorization header is required"}), 401
            
            token = auth_header[7:]  # 移除 "Bearer " 前缀
            user_id = self.data_generator.validate_token(token)
            if not user_id:
                return jsonify({"error": "Invalid or expired token"}), 401
            
            # 将用户ID添加到请求上下文
            request.user_id = user_id
            return f(*args, **kwargs)
        return decorated_function
    
    def _register_routes(self):
        """注册路由"""
        
        # 添加响应头处理中文
        @self.app.after_request
        def after_request(response):
            if response.content_type.startswith('application/json'):
                response.headers['Content-Type'] = 'application/json; charset=utf-8'
            # 确保响应数据是UTF-8编码
            if hasattr(response, 'data') and isinstance(response.data, bytes):
                try:
                    # 确保响应内容是正确的UTF-8编码
                    response.data = response.data.decode('utf-8').encode('utf-8')
                except:
                    pass
            return response
        
        # 认证相关接口
        @self.app.route('/auth/login', methods=['POST'])
        def login():
            data = request.get_json()
            logger.info(f"POST /auth/login - email: {data.get('email') if data else None}")
            
            if not data or 'email' not in data or 'password' not in data:
                return jsonify({
                    "error": "Invalid credentials",
                    "message": "邮箱和密码是必填项"
                }), 400
            
            auth_result = self.data_generator.authenticate_user(data['email'], data['password'])
            if auth_result:
                return self._json_response(auth_result, 200)
            else:
                return self._json_response({
                    "error": "Invalid credentials",
                    "message": "邮箱或密码错误"
                }, 401)
        
        @self.app.route('/auth/refresh', methods=['POST'])
        @self._require_auth
        def refresh_token():
            auth_header = request.headers.get('Authorization')
            token = auth_header[7:]  # 移除 "Bearer " 前缀
            
            logger.info("POST /auth/refresh")
            
            refresh_result = self.data_generator.refresh_token(token)
            if refresh_result:
                return jsonify(refresh_result), 200
            else:
                return jsonify({"error": "令牌无效或已过期"}), 401
        
        # 用户相关接口
        @self.app.route('/users', methods=['GET'])
        @self._require_auth
        def get_users():
            page = int(request.args.get('page', 1))
            limit = int(request.args.get('limit', 10))
            role = request.args.get('role')
            
            logger.info(f"GET /users - page: {page}, limit: {limit}, role: {role}")
            
            result = self.data_generator.get_users(page, limit, role)
            return self._json_response(result)
        
        @self.app.route('/users', methods=['POST'])
        @self._require_auth
        def create_user():
            user_data = request.get_json()
            logger.info(f"POST /users - data: {user_data}")
            
            # 验证必填字段
            if not user_data or 'name' not in user_data or 'email' not in user_data:
                return jsonify({"error": "name and email are required"}), 400
            
            new_user = self.data_generator.create_user(user_data)
            return self._json_response(new_user, 201)
        
        @self.app.route('/users/<int:user_id>', methods=['GET'])
        @self._require_auth
        def get_user_by_id(user_id):
            logger.info(f"GET /users/{user_id}")
            
            user = self.data_generator.get_user_by_id(user_id)
            if user:
                return self._json_response(user)
            else:
                return jsonify({"error": "User not found"}), 404
        
        @self.app.route('/users/<int:user_id>', methods=['PUT'])
        @self._require_auth
        def update_user(user_id):
            user_data = request.get_json()
            logger.info(f"PUT /users/{user_id} - data: {user_data}")
            
            updated_user = self.data_generator.update_user(user_id, user_data)
            if updated_user:
                return self._json_response(updated_user)
            else:
                return jsonify({"error": "User not found"}), 404
        
        @self.app.route('/users/<int:user_id>', methods=['DELETE'])
        @self._require_auth
        def delete_user(user_id):
            logger.info(f"DELETE /users/{user_id}")
            
            if self.data_generator.delete_user(user_id):
                return '', 204
            else:
                return jsonify({"error": "User not found"}), 404
        
        # 产品相关接口
        @self.app.route('/products', methods=['GET'])
        @self._require_auth
        def get_products():
            category = request.args.get('category')
            search = request.args.get('search')
            min_price = request.args.get('min_price', type=float)
            max_price = request.args.get('max_price', type=float)
            
            logger.info(f"GET /products - category: {category}, search: {search}, min_price: {min_price}, max_price: {max_price}")
            
            products = self.data_generator.get_products(category, search, min_price, max_price)
            return self._json_response(products)
        
        # 订单相关接口
        @self.app.route('/orders', methods=['POST'])
        @self._require_auth
        def create_order():
            order_data = request.get_json()
            logger.info(f"POST /orders - data: {order_data}")
            
            # 验证必填字段
            if not order_data or 'userId' not in order_data or 'items' not in order_data:
                return jsonify({"error": "userId and items are required"}), 400
            
            new_order = self.data_generator.create_order(order_data)
            return self._json_response(new_order, 201)
        
        # 健康检查接口
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "message": "Mock server is running"
            })
        
        # 调试接口 - 获取可用的登录用户
        @self.app.route('/debug/users', methods=['GET'])
        def debug_users():
            """调试接口：显示可用的登录用户信息"""
            users_info = []
            for user in self.data_generator.fake_users:
                users_info.append({
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "role": user["role"],
                    "login_info": "使用邮箱和密码 'password123' 登录"
                })
            return self._json_response({
                "message": "可用的登录用户",
                "users": users_info,
                "note": "所有用户的默认密码都是 'password123'"
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
                response = self.app.response_class(
                    content,
                    mimetype='text/yaml; charset=utf-8'
                )
                return response
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
- POST /auth/login         - 用户登录
- POST /auth/refresh       - 刷新令牌
- GET  /users              - 获取用户列表 (需要认证)
- POST /users              - 创建用户 (需要认证)
- GET  /users/{{id}}         - 获取指定用户 (需要认证)
- PUT  /users/{{id}}         - 更新用户信息 (需要认证)
- DELETE /users/{{id}}       - 删除用户 (需要认证)
- GET  /products           - 获取产品列表 (需要认证)
- POST /orders             - 创建订单 (需要认证)
- GET  /health             - 健康检查
- GET  /debug/users        - 查看可用登录用户 (调试用)
- GET  /docs               - API文档

认证说明:
- 访问 /debug/users 查看所有可用的登录用户
- 使用任何用户的邮箱和密码 'password123' 进行登录
- 登录成功后会返回 access_token
- 在请求头中添加: Authorization: Bearer {{token}}

示例登录:
curl -X POST http://{host}:{port}/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{{"email": "zhang1@example.com", "password": "password123"}}'
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
