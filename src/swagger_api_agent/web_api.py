"""
Swagger API Agent Web API
提供 HTTP API 接口，支持通过 REST API 调用
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

import jwt
from flask import Flask, jsonify, request
# from flask_cors import CORS

from .agent import SwaggerAPIAgent
from . import config

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

# 创建 Flask 应用
app = Flask(__name__)
# CORS(app)  # 禁用跨域支持

# 配置 Flask 应用以正确显示中文
app.config["JSON_AS_ASCII"] = False  # 禁用 ASCII 转义，正确显示中文
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True  # 格式化 JSON 输出

original_jsonify = jsonify


def custom_jsonify(*args, **kwargs):
    """自定义 jsonify 函数，确保中文正确显示"""
    if args and len(args) == 1:
        response = app.response_class(
            json.dumps(args[0], ensure_ascii=False, indent=2, separators=(",", ": ")),
            mimetype="application/json; charset=utf-8",
        )
    else:
        response = original_jsonify(*args, **kwargs)

    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


# 替换默认的 jsonify
jsonify = custom_jsonify

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局 agent 实例
agent: SwaggerAPIAgent = None


def generate_jwt_token(username: str) -> str:
    """生成 JWT token"""
    payload = {
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=config.JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm='HS256')


def verify_jwt_token(token: str) -> dict:
    """验证 JWT token"""
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=['HS256'])
        return {'success': True, 'username': payload['username']}
    except jwt.ExpiredSignatureError:
        return {'success': False, 'error': 'Token 已过期'}
    except jwt.InvalidTokenError:
        return {'success': False, 'error': 'Token 无效'}


def require_auth(f):
    """JWT 认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'success': False, 'error': '缺少 Authorization 头'}), 401
        
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Authorization 头格式错误，应为: Bearer <token>'}), 401
        
        token = auth_header.split(' ')[1]
        verification_result = verify_jwt_token(token)
        
        if not verification_result['success']:
            return jsonify({'success': False, 'error': verification_result['error']}), 401
        
        # 将用户信息添加到请求上下文
        request.current_user = verification_result['username']
        return f(*args, **kwargs)
    
    return decorated_function


def init_agent():
    """初始化 agent"""
    global agent

    try:
        # 从环境变量或参数获取配置
        api_base_url = os.getenv("API_BASE_URL")
        api_token = os.getenv("API_TOKEN")
        openapi_file = os.getenv("OPENAPI_FILE")

        agent = SwaggerAPIAgent(
            api_base_url=api_base_url, 
            api_token=api_token,
            openapi_file=openapi_file
        )

        if not agent.initialize():
            logger.error(f"Agent 初始化失败: {agent.last_error}")
            return False

        logger.info("Agent 初始化成功")
        return True

    except Exception as e:
        logger.error(f"初始化 Agent 异常: {str(e)}")
        return False


@app.errorhandler(400)
def bad_request(error):
    """处理 400 错误"""
    return jsonify({"success": False, "error": "请求参数错误", "message": str(error)}), 400


@app.errorhandler(500)
def internal_error(error):
    """处理 500 错误"""
    logger.error(f"内部错误: {str(error)}")
    return jsonify({"success": False, "error": "服务器内部错误", "message": str(error)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """健康检查"""
    global agent

    status = {
        "status": "healthy",
        "agent_initialized": agent is not None and agent.is_initialized,
        "timestamp": agent.conversation_history.messages[-1]["timestamp"]
        if agent and agent.conversation_history.messages
        else None,
    }

    if agent and agent.is_initialized:
        api_info = agent.get_api_info()
        status.update(
            {
                "api_title": api_info.get("title", "Unknown"),
                "api_version": api_info.get("version", "Unknown"),
                "endpoints_count": api_info.get("endpoints_count", 0),
            }
        )

    return jsonify(status)


@app.route("/api/login", methods=["POST"])
def login():
    """用户登录，验证用户名密码并返回 JWT token"""
    try:
        data = request.get_json()
        
        if not data or "username" not in data or "password" not in data:
            return jsonify({"success": False, "error": "缺少用户名或密码"}), 400
        
        username = data["username"]
        password = data["password"]
        
        # 验证用户名密码
        if username != config.WEB_API_USERNAME or password != config.WEB_API_PASSWORD:
            return jsonify({"success": False, "error": "用户名或密码错误"}), 401
        
        # 生成 JWT token
        token = generate_jwt_token(username)
        
        return jsonify({
            "success": True,
            "message": "登录成功",
            "token": token,
            "expires_in": config.JWT_EXPIRATION_HOURS * 3600  # 秒
        })
        
    except Exception as e:
        logger.error(f"登录异常: {str(e)}")
        return jsonify({"success": False, "error": f"登录异常: {str(e)}"}), 500


@app.route("/api/process", methods=["POST"])
@require_auth
def process_natural_language():
    """处理自然语言输入"""
    global agent

    if not agent or not agent.is_initialized:
        return jsonify({"success": False, "error": "Agent 未初始化"}), 503

    try:
        data = request.get_json()

        if not data or "message" not in data:
            return jsonify({"success": False, "error": "缺少 message 参数"}), 400

        user_message = data["message"]
        context = data.get("context", {})

        logger.info(f"处理自然语言输入: {user_message}")

        execution_context = {"is_cli_mode": False}
        result = agent.process_natural_language(user_message, context, execution_context)

        # 确保返回完整的结果，包括所有字段
        response_data = {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "data": result.get("function_calls", None) or result.get("data", None),
            "function_calls": result.get("function_calls", []),
            "usage": result.get("usage", None),
            "timestamp": result.get("timestamp", None)
        }

        # 如果有错误，包含错误信息
        if not result.get("success", False):
            response_data["error"] = result.get("error", "未知错误")

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"处理自然语言输入异常: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"处理异常: {str(e)}",
            "message": "",
            "data": None,
            "function_calls": [],
            "usage": None
        }), 500


@app.route("/api/call", methods=["POST"])
@require_auth
def call_function_directly():
    """直接调用函数"""
    global agent

    if not agent or not agent.is_initialized:
        return jsonify({"success": False, "error": "Agent 未初始化"}), 503

    try:
        data = request.get_json()

        if not data or "function_name" not in data:
            return jsonify({"success": False, "error": "缺少 function_name 参数"}), 400

        function_name = data["function_name"]
        parameters = data.get("parameters", {})

        logger.info(f"直接调用函数: {function_name}")

        result = agent.call_api_directly(function_name, parameters)

        return jsonify(result)

    except Exception as e:
        logger.error(f"直接调用函数异常: {str(e)}")
        return jsonify({"success": False, "error": f"调用异常: {str(e)}"}), 500


@app.route("/api/functions", methods=["GET"])
@require_auth
def get_functions():
    """获取可用函数列表"""
    global agent

    if not agent or not agent.is_initialized:
        return jsonify({"success": False, "error": "Agent 未初始化"}), 503

    try:
        functions = agent.get_available_functions()

        return jsonify({"success": True, "functions": functions, "count": len(functions)})

    except Exception as e:
        logger.error(f"获取函数列表异常: {str(e)}")
        return jsonify({"success": False, "error": f"获取异常: {str(e)}"}), 500


@app.route("/api/info", methods=["GET"])
@require_auth
def get_api_info():
    """获取 API 信息"""
    global agent

    if not agent or not agent.is_initialized:
        return jsonify({"success": False, "error": "Agent 未初始化"}), 503

    try:
        api_info = agent.get_api_info()
        status = agent.get_status()

        return jsonify({"success": True, "api_info": api_info, "agent_status": status})

    except Exception as e:
        logger.error(f"获取 API 信息异常: {str(e)}")
        return jsonify({"success": False, "error": f"获取异常: {str(e)}"}), 500


@app.route("/api/history", methods=["GET"])
@require_auth
def get_conversation_history():
    """获取对话历史"""
    global agent

    if not agent or not agent.is_initialized:
        return jsonify({"success": False, "error": "Agent 未初始化"}), 503

    try:
        history = agent.get_conversation_history()

        return jsonify({"success": True, "history": history, "count": len(history)})

    except Exception as e:
        logger.error(f"获取对话历史异常: {str(e)}")
        return jsonify({"success": False, "error": f"获取异常: {str(e)}"}), 500


@app.route("/api/history", methods=["DELETE"])
@require_auth
def clear_conversation_history():
    """清空对话历史"""
    global agent

    if not agent or not agent.is_initialized:
        return jsonify({"success": False, "error": "Agent 未初始化"}), 503

    try:
        agent.clear_conversation_history()

        return jsonify({"success": True, "message": "对话历史已清空"})

    except Exception as e:
        logger.error(f"清空对话历史异常: {str(e)}")
        return jsonify({"success": False, "error": f"清空异常: {str(e)}"}), 500


@app.route("/", methods=["GET"])
def index():
    """首页"""
    return jsonify(
        {
            "name": "Swagger API Agent",
            "version": "1.0.0",
            "description": "自动化自然语言调用 Swagger/OpenAPI 接口服务",
            "endpoints": {
                "POST /api/login": "用户登录，获取JWT token",
                "POST /api/process": "处理自然语言输入 (需要认证)",
                "POST /api/call": "直接调用函数 (需要认证)",
                "GET /api/functions": "获取可用函数列表 (需要认证)",
                "GET /api/info": "获取 API 信息 (需要认证)",
                "GET /api/history": "获取对话历史 (需要认证)",
                "DELETE /api/history": "清空对话历史 (需要认证)",
                "GET /health": "健康检查",
            },
            "authentication": {
                "type": "JWT Bearer Token",
                "login_endpoint": "/api/login",
                "header_format": "Authorization: Bearer <token>"
            }
        }
    )


def create_app(config=None):
    """应用工厂函数"""
    if config:
        app.config.update(config)

    # 初始化 agent
    if not init_agent():
        logger.error("无法启动服务，Agent 初始化失败")
        return None

    return app


def main():
    """主函数"""
    # 开发模式运行
    import argparse

    parser = argparse.ArgumentParser(description="Swagger API Agent Web Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="服务器主机地址")
    parser.add_argument("--port", type=int, default=5000, help="服务器端口")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--api-url", type=str, help="API 基础 URL")
    parser.add_argument("--api-token", type=str, help="API 认证 Token (Bearer Token)")
    parser.add_argument("--openapi", type=str, help="OpenAPI 文档文件路径")

    args = parser.parse_args()

    # 设置环境变量
    if args.api_url:
        os.environ["API_BASE_URL"] = args.api_url
    if args.api_token:
        os.environ["API_TOKEN"] = args.api_token
    if args.openapi:
        os.environ["OPENAPI_FILE"] = args.openapi

    # 初始化应用
    app = create_app()
    if app is None:
        sys.exit(1)

    logger.info(f"启动 Swagger API Agent Web Server")
    logger.info(f"访问地址: http://{args.host}:{args.port}")

    # 启动服务器
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
