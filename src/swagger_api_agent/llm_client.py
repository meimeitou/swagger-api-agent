"""
大模型客户端
负责与支持 Function Calling 的大模型进行交互
"""

import json
import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LLMResponse(BaseModel):
    """大模型响应"""

    success: bool
    message: Optional[str] = None
    function_calls: List[Dict[str, Any]] = []
    error: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None


class LLMClient:
    """大模型客户端"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
        max_tokens: int = 1024,
        temperature: float = 0.1,
    ):
        """
        初始化大模型客户端

        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            model: 模型名称
            max_tokens: 最大令牌数
            temperature: 温度参数
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # 初始化 OpenAI 客户端
        self.client = OpenAI(api_key=api_key, base_url=base_url)

        logger.info(f"初始化大模型客户端: {model}")

    def generate_function_call(
        self, user_message: str, function_schemas: List[Dict[str, Any]], system_message: Optional[str] = None
    ) -> LLMResponse:
        """
        生成函数调用

        Args:
            user_message: 用户消息
            function_schemas: 函数模式列表
            system_message: 系统消息

        Returns:
            LLMResponse: 大模型响应
        """
        try:
            logger.info(f"发送请求到大模型: {self.model}")
            logger.debug(f"用户消息: {user_message}")
            logger.debug(f"可用函数数量: {len(function_schemas)}")

            # 构建消息列表
            messages = []

            if system_message:
                messages.append({"role": "system", "content": system_message})
            else:
                # 默认系统消息
                default_system = self._build_default_system_message(function_schemas)
                messages.append({"role": "system", "content": default_system})

            messages.append({"role": "user", "content": user_message})

            # 调用大模型
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=function_schemas,
                tool_choice="auto",
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            return self._process_response(response)

        except Exception as e:
            error_msg = f"大模型调用失败: {str(e)}"
            logger.error(error_msg)
            return LLMResponse(success=False, error=error_msg)

    def _build_default_system_message(self, function_schemas: List[Dict[str, Any]]) -> str:
        """构建默认系统消息"""
        function_descriptions = []

        for schema in function_schemas:
            func_info = schema.get("function", {})
            name = func_info.get("name", "unknown")
            description = func_info.get("description", "")
            function_descriptions.append(f"- {name}: {description}")

        system_message = f"""你是一个智能API调用助手。用户会用自然语言描述他们的需求，你需要选择最合适的API函数来满足他们的需求。

可用的API函数：
{chr(10).join(function_descriptions)}

请仔细分析用户的需求，选择最合适的函数进行调用。如果需要多个函数调用，请按逻辑顺序进行。

注意事项：
1. 仔细理解用户需求，选择最匹配的API函数
2. 确保参数填写正确和完整
3. 如果信息不足，优先使用默认值或询问用户
4. 优先选择更具体、更精确的API函数"""

        return system_message

    def _process_response(self, response) -> LLMResponse:
        """处理大模型响应"""
        try:
            choice = response.choices[0]
            message = choice.message

            # 获取使用情况
            usage = None
            if hasattr(response, "usage") and response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            # 检查是否有函数调用
            if hasattr(message, "tool_calls") and message.tool_calls:
                function_calls = []

                for tool_call in message.tool_calls:
                    if tool_call.type == "function":
                        try:
                            # 解析函数参数
                            arguments = json.loads(tool_call.function.arguments)

                            function_call = {
                                "name": tool_call.function.name,
                                "arguments": arguments,
                                "call_id": tool_call.id,
                            }
                            function_calls.append(function_call)

                        except json.JSONDecodeError as e:
                            logger.warning(f"解析函数参数失败: {str(e)}")
                            logger.warning(f"原始参数: {tool_call.function.arguments}")

                if function_calls:
                    logger.info(f"识别到 {len(function_calls)} 个函数调用")
                    return LLMResponse(success=True, function_calls=function_calls, usage=usage)

            # 没有函数调用，返回文本消息
            text_content = message.content or "抱歉，我无法理解您的请求或找到合适的API来处理。"

            return LLMResponse(success=True, message=text_content, usage=usage)

        except Exception as e:
            error_msg = f"处理大模型响应失败: {str(e)}"
            logger.error(error_msg)
            return LLMResponse(success=False, error=error_msg)

    def chat_with_context(self, messages: List[Dict[str, str]], function_schemas: List[Dict[str, Any]]) -> LLMResponse:
        """
        带上下文的对话

        Args:
            messages: 对话历史
            function_schemas: 函数模式列表

        Returns:
            LLMResponse: 大模型响应
        """
        try:
            logger.info(f"进行上下文对话，历史消息数: {len(messages)}")

            # 调用大模型
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=function_schemas,
                tool_choice="auto",
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            return self._process_response(response)

        except Exception as e:
            error_msg = f"上下文对话失败: {str(e)}"
            logger.error(error_msg)
            return LLMResponse(success=False, error=error_msg)

    def explain_function_call(
        self, function_name: str, arguments: Dict[str, Any], function_schemas: List[Dict[str, Any]]
    ) -> str:
        """
        解释函数调用

        Args:
            function_name: 函数名
            arguments: 参数
            function_schemas: 函数模式列表

        Returns:
            解释文本
        """
        try:
            # 找到对应的函数模式
            function_schema = None
            for schema in function_schemas:
                if schema.get("function", {}).get("name") == function_name:
                    function_schema = schema.get("function", {})
                    break

            if not function_schema:
                return f"调用函数: {function_name}"

            description = function_schema.get("description", "")

            # 构建参数说明
            param_descriptions = []
            for key, value in arguments.items():
                param_descriptions.append(f"{key}: {value}")

            explanation = f"调用函数: {function_name}"
            if description:
                explanation += f" ({description})"

            if param_descriptions:
                explanation += f"\n参数: {', '.join(param_descriptions)}"

            return explanation

        except Exception as e:
            logger.warning(f"解释函数调用失败: {str(e)}")
            return f"调用函数: {function_name}"

    def validate_api_key(self) -> bool:
        """验证 API 密钥是否有效"""
        try:
            # 发送一个简单的请求来验证密钥
            self.client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": "Hello"}], max_tokens=1
            )
            return True
        except Exception as e:
            logger.error(f"API 密钥验证失败: {str(e)}")
            return False

    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.warning(f"获取模型列表失败: {str(e)}")
            return [self.model]
