"""
Swagger API Agent 主类
整合所有组件，提供统一的接口调用服务
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .api_caller import APICaller
from .config import (CURRENT_TIME, CURRENT_USER, DEEPSEEK_API_BASE,
                     DEEPSEEK_API_KEY, DEFAULT_API_BASE_URL, DEFAULT_API_TOKEN,
                     DEFAULT_LLM_MODEL, DEFAULT_OPENAPI_FILE)
from .llm_client import LLMClient
from .openapi_parser import APIEndpoint, OpenAPIParser

logger = logging.getLogger(__name__)


class ConversationHistory:
    """对话历史管理"""

    def __init__(self, max_history: int = 10):
        self.messages: List[Dict[str, str]] = []
        self.max_history = max_history

    def add_message(self, role: str, content: str):
        """添加消息"""
        self.messages.append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})

        # 保持历史记录在限制范围内
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history :]

    def get_messages(self) -> List[Dict[str, str]]:
        """获取消息历史（不包含时间戳）"""
        return [{"role": msg["role"], "content": msg["content"]} for msg in self.messages]

    def clear(self):
        """清空历史"""
        self.messages.clear()


def format_api_call_info(endpoint: APIEndpoint, arguments: Dict[str, Any], validated_params: Dict[str, Any]) -> str:
    """
    格式化 API 调用信息，用于在执行前显示

    Args:
        endpoint: API 端点信息
        arguments: 原始参数
        validated_params: 验证后的参数

    Returns:
        格式化的调用信息字符串
    """
    info_lines = []
    info_lines.append(f"📡 即将调用 API 接口:")
    info_lines.append(f"   接口名称: {endpoint.operation_id}")
    info_lines.append(f"   请求方法: {endpoint.method.upper()}")
    info_lines.append(f"   请求路径: {endpoint.path}")

    if endpoint.summary:
        info_lines.append(f"   接口描述: {endpoint.summary}")

    # 显示参数信息
    if validated_params:
        info_lines.append(f"   请求参数:")
        for param_name, param_value in validated_params.items():
            # 找到对应的参数定义以获取类型信息
            param_info = None
            for param in endpoint.parameters:
                if param.name == param_name:
                    param_info = param
                    break

            if param_info:
                info_lines.append(f"     - {param_name} ({param_info.type}): {param_value}")
            else:
                info_lines.append(f"     - {param_name}: {param_value}")
    else:
        info_lines.append(f"   请求参数: 无")

    # 显示请求体信息
    if endpoint.request_body:
        info_lines.append(f"   请求体类型: {endpoint.request_body.get('content_type', 'application/json')}")

        # 如果有请求体数据，显示
        body_data = {}
        for key, value in validated_params.items():
            # 检查是否是请求体参数（不在路径参数和查询参数中）
            is_path_or_query = any(param.name == key for param in endpoint.parameters)
            if not is_path_or_query:
                body_data[key] = value

        if body_data:
            info_lines.append(f"   请求体数据:")
            for key, value in body_data.items():
                info_lines.append(f"     - {key}: {value}")

    return "\n".join(info_lines)


def get_user_confirmation(call_info: str, is_cli_mode: bool = True) -> bool:
    """
    获取用户确认是否执行 API 调用

    Args:
        call_info: API 调用信息
        is_cli_mode: 是否为命令行模式

    Returns:
        用户是否确认执行
    """
    if not is_cli_mode:
        # 在非 CLI 模式下（如 Web API），默认执行
        return True

    # 动态检查是否需要用户确认
    require_confirmation = os.getenv("REQUIRE_USER_CONFIRMATION", "false").lower() in ("true", "1", "yes", "on")
    if not require_confirmation:
        # 如果未启用用户确认，默认执行
        return True

    try:
        # 显示调用信息
        print(f"\n{call_info}\n")

        # 询问用户确认
        while True:
            response = input("🤔 是否执行此 API 调用？(y/yes 确认, n/no 取消, s/skip 跳过): ").strip().lower()

            if response in ["y", "yes", "是", "确认"]:
                return True
            elif response in ["n", "no", "否", "取消"]:
                return False
            elif response in ["s", "skip", "跳过"]:
                return False
            else:
                print("请输入 y/yes (确认), n/no (取消), 或 s/skip (跳过)")

    except (KeyboardInterrupt, EOFError):
        print("\n用户中断，取消执行")
        return False


class SwaggerAPIAgent:
    """Swagger API Agent 主类"""

    def __init__(
        self, openapi_file: str = None, api_base_url: str = None, api_token: str = None, deepseek_api_key: str = None, config_file: str = None
    ):
        """
        初始化 Swagger API Agent

        Args:
            openapi_file: OpenAPI 文档路径
            api_base_url: API 基础 URL
            api_token: API 认证 Token (Bearer Token)
            deepseek_api_key: DeepSeek API 密钥
            config_file: 配置文件路径
        """
        # 加载配置
        self._load_config(config_file)

        # 覆盖配置参数
        if openapi_file:
            self.openapi_file = openapi_file
        if api_base_url:
            self.api_base_url = api_base_url
        if api_token:
            self.api_token = api_token
        if api_base_url:
            self.api_base_url = api_base_url
        if api_token:
            self.api_token = api_token
        if deepseek_api_key:
            self.deepseek_api_key = deepseek_api_key

        # 初始化组件
        self.parser: Optional[OpenAPIParser] = None
        self.api_caller: Optional[APICaller] = None
        self.llm_client: Optional[LLMClient] = None
        self.conversation_history = ConversationHistory()

        # 状态信息
        self.is_initialized = False
        self.last_error: Optional[str] = None

        logger.info("Swagger API Agent 初始化完成")

    def _load_config(self, config_file: str = None):
        """加载配置"""
        # 加载环境变量
        from dotenv import load_dotenv

        load_dotenv()

        # 从环境变量或配置文件获取配置
        self.openapi_file = os.getenv("OPENAPI_FILE", DEFAULT_OPENAPI_FILE)
        self.api_base_url = os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL)
        self.api_token = os.getenv("API_TOKEN", DEFAULT_API_TOKEN)
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", DEEPSEEK_API_KEY)
        self.deepseek_api_url = os.getenv("DEEPSEEK_API_URL", DEEPSEEK_API_BASE)
        self.deepseek_model = os.getenv("DEEPSEEK_MODEL", DEFAULT_LLM_MODEL)

        # 验证必需的配置
        if not self.deepseek_api_key or self.deepseek_api_key == "your_deepseek_api_key_here":
            logger.warning("未设置 DeepSeek API 密钥，部分功能可能无法使用")

    def initialize(self) -> bool:
        """初始化所有组件"""
        try:
            logger.info("开始初始化 Swagger API Agent 组件...")

            # 检查 OpenAPI 文档文件
            if not Path(self.openapi_file).exists():
                self.last_error = f"OpenAPI 文档文件不存在: {self.openapi_file}"
                logger.error(self.last_error)
                return False

            # 1. 初始化 OpenAPI 解析器
            logger.info("初始化 OpenAPI 解析器...")
            self.parser = OpenAPIParser(self.openapi_file)
            self.parser.parse()

            api_info = self.parser.get_api_info()
            logger.info(f"成功解析 API: {api_info['title']} v{api_info['version']}")
            logger.info(f"发现 {api_info['endpoints_count']} 个 API 端点")

            # 2. 初始化 API 调用器
            logger.info("初始化 API 调用器...")
            self.api_caller = APICaller(self.api_base_url, auth_token=self.api_token)

            # 3. 初始化大模型客户端
            if self.deepseek_api_key and self.deepseek_api_key != "your_deepseek_api_key_here":
                logger.info("初始化大模型客户端...")
                self.llm_client = LLMClient(
                    api_key=self.deepseek_api_key, base_url=self.deepseek_api_url, model=self.deepseek_model
                )

                # 验证 API 密钥
                if not self.llm_client.validate_api_key():
                    logger.warning("DeepSeek API 密钥验证失败，将仅支持手动调用模式")
                    self.llm_client = None
            else:
                logger.warning("未配置 DeepSeek API 密钥，将仅支持手动调用模式")
                self.llm_client = None

            self.is_initialized = True
            logger.info("Swagger API Agent 初始化成功！")
            return True

        except Exception as e:
            self.last_error = f"初始化失败: {str(e)}"
            logger.error(self.last_error)
            return False

    def process_natural_language(
        self, user_input: str, context: Dict[str, Any] = None, execution_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        处理自然语言输入

        Args:
            user_input: 用户自然语言输入
            context: 上下文信息
            execution_context: 执行上下文（如是否为 CLI 模式等）

        Returns:
            处理结果
        """
        if not self.is_initialized:
            return {"success": False, "error": "系统未初始化，请先调用 initialize() 方法"}

        if not self.llm_client:
            return {"success": False, "error": "大模型客户端未配置，请检查 DeepSeek API 密钥"}

        try:
            logger.info(f"处理自然语言输入: {user_input}")

            # 获取函数模式
            function_schemas = self.parser.get_function_schemas()

            if not function_schemas:
                return {"success": False, "error": "没有可用的 API 函数"}

            # 构建系统消息
            system_message = self._build_system_message(context)

            # 调用大模型
            llm_response = self.llm_client.generate_function_call(
                user_message=user_input, function_schemas=function_schemas, system_message=system_message
            )

            if not llm_response.success:
                return {"success": False, "error": f"大模型调用失败: {llm_response.error}"}

            # 添加用户消息到历史
            self.conversation_history.add_message("user", user_input)

            # 处理函数调用
            if llm_response.function_calls:
                results = []

                for function_call in llm_response.function_calls:
                    result = self._execute_function_call(function_call, function_schemas, execution_context)
                    results.append(result)

                # 添加助手响应到历史
                assistant_message = self._format_results_for_history(results)
                self.conversation_history.add_message("assistant", assistant_message)

                return {
                    "success": True,
                    "function_calls": results,
                    "message": self._format_results_message(results),
                    "usage": llm_response.usage,
                }
            else:
                # 没有函数调用，返回文本响应
                if llm_response.message:
                    self.conversation_history.add_message("assistant", llm_response.message)

                return {
                    "success": True,
                    "message": llm_response.message or "没有找到合适的 API 来处理您的请求",
                    "usage": llm_response.usage,
                }

        except Exception as e:
            error_msg = f"处理自然语言输入失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def _build_system_message(self, context: Dict[str, Any] = None) -> str:
        """构建系统消息"""
        api_info = self.parser.get_api_info()

        system_parts = [
            f"你是一个智能 API 调用助手，专门处理 {api_info['title']} API 的调用请求。",
            f"API 版本: {api_info['version']}",
            f"当前时间: {CURRENT_TIME}",
            f"当前用户: {CURRENT_USER}",
        ]

        if context:
            system_parts.append(f"上下文信息: {json.dumps(context, ensure_ascii=False)}")

        system_parts.extend(
            [
                "",
                "请根据用户的自然语言描述，选择最合适的 API 函数进行调用。",
                "注意事项：",
                "1. 仔细理解用户需求，选择最匹配的 API 函数",
                "2. 确保参数填写正确和完整",
                "3. 如果信息不足，优先使用默认值",
                "4. 如果需要路径参数（如用户ID），请根据上下文推断或使用示例值",
            ]
        )

        return "\n".join(system_parts)

    def _execute_function_call(
        self,
        function_call: Dict[str, Any],
        function_schemas: List[Dict[str, Any]],
        execution_context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """执行函数调用"""
        try:
            function_name = function_call["name"]
            arguments = function_call["arguments"]

            logger.info(f"执行函数调用: {function_name}")
            logger.debug(f"参数: {arguments}")

            # 获取对应的 API 端点
            endpoint = self.parser.get_endpoint_by_function_name(function_name)
            if not endpoint:
                return {
                    "function_name": function_name,
                    "success": False,
                    "explanation": f"未找到 API 端点: {function_name}",
                    "error": f"未找到对应的 API 端点: {function_name}",
                }

            # 验证参数
            try:
                validated_params = self.api_caller.validate_parameters(endpoint, arguments)
            except Exception as e:
                return {
                    "function_name": function_name,
                    "success": False,
                    "explanation": f"参数验证失败: {function_name}",
                    "error": f"参数验证失败: {str(e)}",
                }

            # 在执行 API 调用前输出接口和参数信息，并获取用户确认
            call_info = format_api_call_info(endpoint, arguments, validated_params)

            # 动态检查是否需要用户确认
            require_confirmation = os.getenv("REQUIRE_USER_CONFIRMATION", "false").lower() in ("true", "1", "yes", "on")
            show_details = os.getenv("SHOW_API_CALL_DETAILS", "true").lower() in ("true", "1", "yes", "on")

            # 如果启用了详情显示但不需要确认，则在这里显示
            if show_details and not require_confirmation:
                print(f"\n{call_info}\n")
            logger.info(call_info)

            # 获取用户确认（如果启用）
            is_cli_mode = execution_context.get("is_cli_mode", True) if execution_context else True
            if not get_user_confirmation(call_info, is_cli_mode=is_cli_mode):
                return {
                    "function_name": function_name,
                    "success": False,
                    "explanation": f"用户取消执行 {function_name}",
                    "call_info": call_info,
                    "error": "用户取消执行",
                    "cancelled_by_user": True,
                }

            # 调用 API
            api_response = self.api_caller.call_api(endpoint, validated_params)

            # 生成解释
            explanation = (
                self.llm_client.explain_function_call(function_name, arguments, function_schemas)
                if self.llm_client
                else f"调用 {function_name}"
            )

            return {
                "function_name": function_name,
                "success": api_response.success,
                "explanation": explanation,
                "call_info": call_info,  # 添加调用信息到返回结果
                "api_response": {
                    "status_code": api_response.status_code,
                    "data": api_response.data,
                    "url": api_response.url,
                    "method": api_response.method,
                },
                "error": api_response.error if not api_response.success else None,
            }

        except Exception as e:
            error_msg = f"执行函数调用失败: {str(e)}"
            logger.error(error_msg)
            return {
                "function_name": function_call.get("name", "unknown"),
                "success": False,
                "explanation": f"执行 {function_call.get('name', 'unknown')} 时发生异常",
                "error": error_msg,
            }

    def _format_results_for_history(self, results: List[Dict[str, Any]]) -> str:
        """格式化结果用于对话历史"""
        if not results:
            return "没有执行任何函数调用"

        formatted_parts = []
        for result in results:
            if result["success"]:
                formatted_parts.append(f"✅ {result['explanation']}")
            else:
                formatted_parts.append(f"❌ {result['function_name']}: {result['error']}")

        return "\n".join(formatted_parts)

    def _format_results_message(self, results: List[Dict[str, Any]]) -> str:
        """格式化结果消息"""
        if not results:
            return "没有执行任何操作"

        success_count = sum(1 for r in results if r["success"])
        total_count = len(results)

        message_parts = [f"执行了 {total_count} 个 API 调用，成功 {success_count} 个：\n"]

        for i, result in enumerate(results, 1):
            if result["success"]:
                api_resp = result["api_response"]
                message_parts.append(
                    f"{i}. ✅ {result['explanation']}\n"
                    f"   状态码: {api_resp['status_code']}\n"
                    f"   URL: {api_resp['method']} {api_resp['url']}"
                )

                if api_resp["data"]:
                    # 简化数据显示
                    data_str = json.dumps(api_resp["data"], ensure_ascii=False, indent=2)
                    if len(data_str) > 500:
                        data_str = data_str[:500] + "..."
                    message_parts.append(f"   响应数据: {data_str}")
            else:
                message_parts.append(f"{i}. ❌ {result['function_name']}: {result['error']}")

        return "\n".join(message_parts)

    def call_api_directly(self, function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        直接调用 API（不使用大模型）

        Args:
            function_name: 函数名
            parameters: 参数

        Returns:
            调用结果
        """
        if not self.is_initialized:
            return {"success": False, "error": "系统未初始化，请先调用 initialize() 方法"}

        try:
            # 获取对应的 API 端点
            endpoint = self.parser.get_endpoint_by_function_name(function_name)
            if not endpoint:
                return {"success": False, "error": f"未找到对应的 API 端点: {function_name}"}

            # 验证参数
            validated_params = self.api_caller.validate_parameters(endpoint, parameters)

            # 调用 API
            api_response = self.api_caller.call_api(endpoint, validated_params)

            return {
                "success": api_response.success,
                "function_name": function_name,
                "api_response": {
                    "status_code": api_response.status_code,
                    "data": api_response.data,
                    "url": api_response.url,
                    "method": api_response.method,
                    "headers": api_response.headers,
                },
                "error": api_response.error if not api_response.success else None,
            }

        except Exception as e:
            error_msg = f"直接调用 API 失败: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def get_available_functions(self) -> List[Dict[str, Any]]:
        """获取可用的函数列表"""
        if not self.is_initialized:
            return []

        function_schemas = self.parser.get_function_schemas()
        return [
            {
                "name": schema["function"]["name"],
                "description": schema["function"]["description"],
                "parameters": schema["function"]["parameters"],
            }
            for schema in function_schemas
        ]

    def get_api_info(self) -> Dict[str, Any]:
        """获取 API 信息"""
        if not self.is_initialized:
            return {}

        return self.parser.get_api_info()

    def clear_conversation_history(self):
        """清空对话历史"""
        self.conversation_history.clear()
        logger.info("对话历史已清空")

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history.messages

    def set_api_auth(self, auth_type: str, **kwargs):
        """设置 API 认证"""
        if not self.api_caller:
            logger.warning("API 调用器未初始化")
            return

        if auth_type.lower() == "bearer":
            token = kwargs.get("token")
            if token:
                self.api_caller.set_header("Authorization", f"Bearer {token}")
                logger.info("设置 Bearer 认证成功")
        elif auth_type.lower() == "apikey":
            key = kwargs.get("key")
            header_name = kwargs.get("header", "X-API-Key")
            if key:
                self.api_caller.set_header(header_name, key)
                logger.info(f"设置 API Key 认证成功: {header_name}")
        else:
            logger.warning(f"不支持的认证类型: {auth_type}")

    def export_function_schemas(self, output_file: str):
        """导出函数模式到文件"""
        if not self.is_initialized:
            logger.error("系统未初始化")
            return

        self.parser.export_schemas(output_file)

    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "initialized": self.is_initialized,
            "openapi_file": self.openapi_file,
            "api_base_url": self.api_base_url,
            "llm_available": self.llm_client is not None,
            "last_error": self.last_error,
            "conversation_length": len(self.conversation_history.messages),
            "api_info": self.get_api_info() if self.is_initialized else {},
        }
