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
from .user_session_manager import get_session_manager, get_or_create_user_agent
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

# 用户会话管理器
session_manager = get_session_manager()


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
        
        # 确保用户有对应的agent实例
        try:
            agent = get_or_create_user_agent(
                user_id=request.current_user,
                openapi_file=os.getenv("OPENAPI_FILE"),
                api_base_url=os.getenv("API_BASE_URL"),
                api_token=os.getenv("API_TOKEN"),
                deepseek_api_key=os.getenv("DEEPSEEK_API_KEY")
            )
            request.current_agent = agent
        except Exception as e:
            logger.error(f"为用户 {request.current_user} 创建agent失败: {str(e)}")
            return jsonify({'success': False, 'error': f'用户会话初始化失败: {str(e)}'}), 503
        
        return f(*args, **kwargs)
    
    return decorated_function


def init_agent():
    """初始化默认配置（用于健康检查等）"""
    try:
        # 这个函数主要用于验证配置的有效性
        # 实际的agent实例会在用户登录时按需创建
        
        # 检查必要的配置项
        api_base_url = os.getenv("API_BASE_URL")
        openapi_file = os.getenv("OPENAPI_FILE")
        
        if not api_base_url:
            logger.warning("未设置 API_BASE_URL 环境变量")
        
        if not openapi_file or not Path(openapi_file).exists():
            logger.warning(f"OpenAPI 文档文件不存在或未设置: {openapi_file}")
            return False

        logger.info("Agent 配置验证成功")
        return True

    except Exception as e:
        logger.error(f"验证 Agent 配置异常: {str(e)}")
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
    # 检查配置有效性
    api_base_url = os.getenv("API_BASE_URL")
    openapi_file = os.getenv("OPENAPI_FILE")
    config_valid = bool(api_base_url and openapi_file and Path(openapi_file).exists())
    
    # 检查是否有认证用户，如果有则检查其agent状态
    agent_initialized = False
    auth_header = request.headers.get('Authorization')
    
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        verification_result = verify_jwt_token(token)
        
        if verification_result['success']:
            username = verification_result['username']
            try:
                # 尝试获取或创建用户的agent
                agent = get_or_create_user_agent(
                    user_id=username,
                    openapi_file=openapi_file,
                    api_base_url=api_base_url,
                    api_token=os.getenv("API_TOKEN"),
                    deepseek_api_key=os.getenv("DEEPSEEK_API_KEY")
                )
                # 检查agent是否已初始化并获取详细状态
                agent_initialized = agent.is_initialized if hasattr(agent, 'is_initialized') else bool(agent)
                
                # 获取服务状态详情
                service_status = agent.get_service_status() if hasattr(agent, 'get_service_status') else {}
                
                logger.info(f"用户 {username} 的 agent 初始化状态: {agent_initialized}")
                if not service_status.get('natural_language_enabled', True):
                    logger.warning(f"用户 {username} 的自然语言处理服务不可用")
            except Exception as e:
                logger.warning(f"检查用户 {username} 的 agent 状态时出错: {str(e)}")
                agent_initialized = False
                service_status = {}
    
    status = {
        "status": "healthy",
        "service": "Swagger API Agent",
        "timestamp": datetime.now().isoformat(),
        "agent_initialized": agent_initialized,
        "config_valid": config_valid,
        "api_base_url": api_base_url,
        "openapi_file": openapi_file,
        "session_stats": session_manager.get_session_stats()
    }
    
    # 如果有用户认证，添加详细服务状态
    if auth_header and agent_initialized and 'service_status' in locals():
        status.update({
            "service_details": service_status,
            "natural_language_enabled": service_status.get('natural_language_enabled', False)
        })

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
    agent = request.current_agent

    try:
        data = request.get_json()

        if not data or "message" not in data:
            return jsonify({"success": False, "error": "缺少 message 参数"}), 400

        user_message = data["message"]
        context = data.get("context", {})
        
        # 添加用户信息到上下文
        context["user_id"] = request.current_user

        logger.info(f"用户 {request.current_user} 处理自然语言输入: {user_message}")

        execution_context = {"is_cli_mode": False}
        result = agent.process_natural_language(user_message, context, execution_context)

        # 确保返回完整的结果，包括所有字段
        response_data = {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "data": result.get("function_calls", None) or result.get("data", None),
            "function_calls": result.get("function_calls", []),
            "usage": result.get("usage", None),
            "timestamp": datetime.now().isoformat(),
            "user_id": request.current_user
        }

        # 如果有错误，包含错误信息
        if not result.get("success", False):
            response_data["error"] = result.get("error", "未知错误")

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"用户 {request.current_user} 处理自然语言输入异常: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"处理异常: {str(e)}",
            "message": "",
            "data": None,
            "function_calls": [],
            "usage": None,
            "user_id": request.current_user
        }), 500


@app.route("/api/call", methods=["POST"])
@require_auth
def call_function_directly():
    """直接调用函数"""
    agent = request.current_agent

    try:
        data = request.get_json()

        if not data or "function_name" not in data:
            return jsonify({"success": False, "error": "缺少 function_name 参数"}), 400

        function_name = data["function_name"]
        parameters = data.get("parameters", {})

        logger.info(f"用户 {request.current_user} 直接调用函数: {function_name}")

        result = agent.call_api_directly(function_name, parameters)
        result["user_id"] = request.current_user

        return jsonify(result)

    except Exception as e:
        logger.error(f"用户 {request.current_user} 直接调用函数异常: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"调用异常: {str(e)}",
            "user_id": request.current_user
        }), 500


@app.route("/api/functions", methods=["GET"])
@require_auth
def get_functions():
    """获取可用函数列表"""
    agent = request.current_agent

    try:
        functions = agent.get_available_functions()

        return jsonify({
            "success": True, 
            "functions": functions, 
            "count": len(functions),
            "user_id": request.current_user
        })

    except Exception as e:
        logger.error(f"用户 {request.current_user} 获取函数列表异常: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"获取异常: {str(e)}",
            "user_id": request.current_user
        }), 500


@app.route("/api/info", methods=["GET"])
@require_auth
def get_api_info():
    """获取 API 信息"""
    agent = request.current_agent

    try:
        api_info = agent.get_api_info()
        status = agent.get_status()

        return jsonify({
            "success": True, 
            "api_info": api_info, 
            "agent_status": status,
            "user_id": request.current_user
        })

    except Exception as e:
        logger.error(f"用户 {request.current_user} 获取 API 信息异常: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"获取异常: {str(e)}",
            "user_id": request.current_user
        }), 500


@app.route("/api/history", methods=["GET"])
@require_auth
def get_conversation_history():
    """获取对话历史"""
    agent = request.current_agent

    try:
        history = agent.get_conversation_history()

        return jsonify({
            "success": True, 
            "history": history, 
            "count": len(history),
            "user_id": request.current_user
        })

    except Exception as e:
        logger.error(f"用户 {request.current_user} 获取对话历史异常: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"获取异常: {str(e)}",
            "user_id": request.current_user
        }), 500


@app.route("/api/history", methods=["DELETE"])
@require_auth
def clear_conversation_history():
    """清空对话历史"""
    agent = request.current_agent

    try:
        agent.clear_conversation_history()

        return jsonify({
            "success": True, 
            "message": "对话历史已清空",
            "user_id": request.current_user
        })

    except Exception as e:
        logger.error(f"用户 {request.current_user} 清空对话历史异常: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"清空异常: {str(e)}",
            "user_id": request.current_user
        }), 500


@app.route("/api/session/info", methods=["GET"])
@require_auth
def get_session_info():
    """获取当前用户会话信息"""
    try:
        session = session_manager.get_user_session(request.current_user)
        if session:
            return jsonify({
                "success": True,
                "session_info": session.get_session_info()
            })
        else:
            return jsonify({
                "success": False,
                "error": "未找到用户会话"
            }), 404

    except Exception as e:
        logger.error(f"获取用户 {request.current_user} 会话信息异常: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"获取会话信息异常: {str(e)}"
        }), 500


@app.route("/api/session/reset", methods=["POST"])
@require_auth
def reset_user_session():
    """重置当前用户会话（创建新的agent实例）"""
    try:
        # 关闭现有会话
        session_manager.close_user_session(request.current_user)
        
        # 创建新会话
        new_session = session_manager.create_user_session(
            user_id=request.current_user,
            openapi_file=os.getenv("OPENAPI_FILE"),
            api_base_url=os.getenv("API_BASE_URL"),
            api_token=os.getenv("API_TOKEN"),
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
            force_new=True
        )
        
        return jsonify({
            "success": True,
            "message": "用户会话已重置",
            "session_info": new_session.get_session_info()
        })

    except Exception as e:
        logger.error(f"重置用户 {request.current_user} 会话异常: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"重置会话异常: {str(e)}"
        }), 500


@app.route("/api/admin/sessions", methods=["GET"])
@require_auth
def get_all_sessions():
    """获取所有会话信息（管理员功能）"""
    try:
        # 这里可以添加管理员权限检查
        # if request.current_user != "admin":
        #     return jsonify({"success": False, "error": "权限不足"}), 403
        
        all_sessions = session_manager.get_all_sessions_info()
        
        return jsonify({
            "success": True,
            "sessions_info": all_sessions
        })

    except Exception as e:
        logger.error(f"获取所有会话信息异常: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"获取所有会话信息异常: {str(e)}"
        }), 500


@app.route("/api/admin/cleanup", methods=["POST"])
@require_auth
def manual_cleanup_sessions():
    """手动清理过期会话（管理员功能）"""
    try:
        # 这里可以添加管理员权限检查
        # if request.current_user != "admin":
        #     return jsonify({"success": False, "error": "权限不足"}), 403
        
        session_manager.cleanup_expired_sessions()
        
        return jsonify({
            "success": True,
            "message": "过期会话清理完成",
            "current_stats": session_manager.get_session_stats()
        })

    except Exception as e:
        logger.error(f"手动清理会话异常: {str(e)}")
        return jsonify({
            "success": False, 
            "error": f"清理会话异常: {str(e)}"
        }), 500


@app.route("/", methods=["GET"])
def index():
    """首页"""
    return jsonify(
        {
            "name": "Swagger API Agent",
            "version": "1.0.0",
            "description": "自动化自然语言调用 Swagger/OpenAPI 接口服务 - 支持多用户会话",
            "features": [
                "多用户独立会话管理",
                "JWT 用户认证",
                "自然语言 API 调用",
                "对话历史管理",
                "自动会话清理"
            ],
            "endpoints": {
                "认证相关": {
                    "POST /api/login": "用户登录，获取JWT token"
                },
                "API 调用": {
                    "POST /api/process": "处理自然语言输入 (需要认证)",
                    "POST /api/call": "直接调用函数 (需要认证)",
                    "GET /api/functions": "获取可用函数列表 (需要认证)",
                    "GET /api/info": "获取 API 信息 (需要认证)"
                },
                "对话管理": {
                    "GET /api/history": "获取对话历史 (需要认证)",
                    "DELETE /api/history": "清空对话历史 (需要认证)"
                },
                "会话管理": {
                    "GET /api/session/info": "获取当前用户会话信息 (需要认证)",
                    "POST /api/session/reset": "重置当前用户会话 (需要认证)"
                },
                "管理员功能": {
                    "GET /api/admin/sessions": "获取所有会话信息 (需要认证)",
                    "POST /api/admin/cleanup": "手动清理过期会话 (需要认证)"
                },
                "系统信息": {
                    "GET /health": "健康检查"
                }
            },
            "authentication": {
                "type": "JWT Bearer Token",
                "login_endpoint": "/api/login",
                "header_format": "Authorization: Bearer <token>",
                "token_expiration": f"{config.JWT_EXPIRATION_HOURS} hours"
            },
            "session_management": {
                "description": "每个用户登录后都会获得独立的 agent 实例和对话上下文",
                "session_timeout": "24 hours",
                "auto_cleanup": "每 1 小时自动清理过期会话"
            }
        }
    )


def create_app(config=None):
    """应用工厂函数"""
    if config:
        app.config.update(config)

    # 验证基础配置
    if not init_agent():
        logger.warning("配置验证失败，但服务仍将启动（用户登录时按需创建agent）")

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
        logger.error("应用初始化失败")
        sys.exit(1)

    logger.info(f"启动 Swagger API Agent Web Server")
    logger.info(f"访问地址: http://{args.host}:{args.port}")

    # 启动服务器
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
