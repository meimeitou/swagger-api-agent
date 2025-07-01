"""
API 调用器
负责根据解析的参数实际调用外部 API 接口
"""

import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from pydantic import BaseModel
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .openapi_parser import APIEndpoint

logger = logging.getLogger(__name__)


class APIResponse(BaseModel):
    """API 响应模型"""

    success: bool
    status_code: int
    data: Any = None
    error: Optional[str] = None
    headers: Dict[str, str] = {}
    url: str = ""
    method: str = ""

    def format_as_markdown(self) -> str:
        """将 API 响应格式化为 Markdown"""
        markdown_lines = []
        
        # 标题
        status_icon = "✅" if self.success else "❌"
        markdown_lines.append(f"## {status_icon} API 调用结果")
        markdown_lines.append("")
        
        # 基本信息
        markdown_lines.append(f"**方法**: `{self.method}`")
        markdown_lines.append(f"**URL**: `{self.url}`")
        markdown_lines.append(f"**状态码**: `{self.status_code}`")
        markdown_lines.append(f"**结果**: {'成功' if self.success else '失败'}")
        markdown_lines.append("")
        
        # 错误信息
        if self.error:
            markdown_lines.append("### ❌ 错误信息")
            markdown_lines.append(f"```")
            markdown_lines.append(self.error)
            markdown_lines.append(f"```")
            markdown_lines.append("")
        
        # 响应数据
        if self.data is not None:
            markdown_lines.append("### 📄 响应数据")
            if isinstance(self.data, (dict, list)):
                markdown_lines.append("```json")
                markdown_lines.append(json.dumps(self.data, indent=2, ensure_ascii=False))
                markdown_lines.append("```")
            else:
                markdown_lines.append("```")
                markdown_lines.append(str(self.data))
                markdown_lines.append("```")
            markdown_lines.append("")
        
        # 响应头（如果有重要的）
        important_headers = ['content-type', 'content-length', 'server', 'date']
        filtered_headers = {k.lower(): v for k, v in self.headers.items() 
                          if k.lower() in important_headers}
        
        if filtered_headers:
            markdown_lines.append("### 📋 响应头")
            for key, value in filtered_headers.items():
                markdown_lines.append(f"- **{key.title()}**: `{value}`")
            markdown_lines.append("")
        
        return "\n".join(markdown_lines)


class APICallError(Exception):
    """API 调用异常"""

    pass


class APICaller:
    """API 调用器"""

    def __init__(self, base_url: str, timeout: int = 30, max_retries: int = 3, auth_token: Optional[str] = None):
        """
        初始化 API 调用器

        Args:
            base_url: API 基础 URL
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            auth_token: 认证 token，如果提供则在请求头中添加 Authorization: Bearer {token}
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.auth_token = auth_token
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """创建请求会话，配置重试策略"""
        session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"],
            backoff_factor=1,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # 设置默认请求头
        session.headers.update(
            {"User-Agent": "SwaggerAPIAgent/1.0.0", "Accept": "application/json", "Content-Type": "application/json"}
        )
        
        # 如果提供了认证 token，添加 Authorization 头
        if self.auth_token:
            session.headers.update({"Authorization": f"Bearer {self.auth_token}"})

        return session

    def call_api(self, endpoint: APIEndpoint, parameters: Dict[str, Any]) -> APIResponse:
        """
        调用 API 接口

        Args:
            endpoint: API 端点信息
            parameters: 调用参数

        Returns:
            APIResponse: API 响应结果
        """
        try:
            logger.info(f"调用 API: {endpoint.method.upper()} {endpoint.path}")
            logger.debug(f"参数: {parameters}")

            # 构建请求 URL
            url = self._build_url(endpoint, parameters)

            # 构建请求参数
            request_kwargs = self._build_request_kwargs(endpoint, parameters)

            # 发起请求
            response = self.session.request(
                method=endpoint.method.upper(), url=url, timeout=self.timeout, **request_kwargs
            )

            # 处理响应
            api_response = self._process_response(response, endpoint)

            logger.info(f"API 调用成功: {response.status_code}")
            return api_response

        except requests.exceptions.Timeout:
            error_msg = f"API 调用超时: {endpoint.path}"
            logger.error(error_msg)
            return APIResponse(
                success=False,
                status_code=408,
                error=error_msg,
                url=url if "url" in locals() else "",
                method=endpoint.method.upper(),
            )

        except requests.exceptions.ConnectionError:
            error_msg = f"API 连接失败: {endpoint.path}"
            logger.error(error_msg)
            return APIResponse(
                success=False,
                status_code=503,
                error=error_msg,
                url=url if "url" in locals() else "",
                method=endpoint.method.upper(),
            )

        except Exception as e:
            error_msg = f"API 调用异常: {str(e)}"
            logger.error(error_msg)
            return APIResponse(
                success=False,
                status_code=500,
                error=error_msg,
                url=url if "url" in locals() else "",
                method=endpoint.method.upper(),
            )

    def _build_url(self, endpoint: APIEndpoint, parameters: Dict[str, Any]) -> str:
        """构建请求 URL"""
        path = endpoint.path

        # 替换路径参数
        path_params = {}
        for param in endpoint.parameters:
            if param.name in parameters and "{" + param.name + "}" in path:
                path_params[param.name] = parameters[param.name]

        # 替换路径中的参数
        for param_name, param_value in path_params.items():
            path = path.replace("{" + param_name + "}", str(param_value))

        # 构建完整 URL
        url = urljoin(self.base_url, path.lstrip("/"))

        return url

    def _build_request_kwargs(self, endpoint: APIEndpoint, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """构建请求参数"""
        kwargs = {}

        # 处理查询参数
        query_params = {}
        path_param_names = set()

        # 收集路径参数名称
        for param in endpoint.parameters:
            if "{" + param.name + "}" in endpoint.path:
                path_param_names.add(param.name)

        # 收集查询参数
        for param in endpoint.parameters:
            if param.name in parameters and param.name not in path_param_names:
                query_params[param.name] = parameters[param.name]

        if query_params:
            kwargs["params"] = query_params

        # 处理请求体
        if endpoint.request_body and endpoint.method.lower() in ["post", "put", "patch"]:
            body_data = self._build_request_body(endpoint, parameters)
            if body_data is not None:
                content_type = endpoint.request_body.get("content_type", "application/json")

                if content_type == "application/json":
                    kwargs["json"] = body_data
                else:
                    kwargs["data"] = body_data

        return kwargs

    def _build_request_body(self, endpoint: APIEndpoint, parameters: Dict[str, Any]) -> Any:
        """构建请求体"""
        if not endpoint.request_body:
            return None

        schema = endpoint.request_body.get("schema", {})

        if "request_body" in parameters:
            # 整个请求体作为参数传递
            return parameters["request_body"]

        # 根据 schema 构建请求体
        if schema.get("type") == "object":
            body = {}
            properties = schema.get("properties", {})

            for prop_name in properties.keys():
                if prop_name in parameters:
                    body[prop_name] = parameters[prop_name]

            return body if body else None

        return None

    def _process_response(self, response: requests.Response, endpoint: APIEndpoint) -> APIResponse:
        """处理 API 响应"""
        success = 200 <= response.status_code < 300

        # 尝试解析 JSON 响应
        data = None
        try:
            if response.content:
                data = response.json()
        except (json.JSONDecodeError, ValueError):
            # 如果不是 JSON，返回原始文本
            data = response.text if response.text else None

        # 提取响应头
        headers = dict(response.headers)

        error_msg = None
        if not success:
            error_msg = f"HTTP {response.status_code}"
            if isinstance(data, dict) and "message" in data:
                error_msg += f": {data['message']}"
            elif isinstance(data, str):
                error_msg += f": {data}"

        return APIResponse(
            success=success,
            status_code=response.status_code,
            data=data,
            error=error_msg,
            headers=headers,
            url=response.url,
            method=endpoint.method.upper(),
        )

    def validate_parameters(self, endpoint: APIEndpoint, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证和处理参数

        Args:
            endpoint: API 端点信息
            parameters: 原始参数

        Returns:
            验证后的参数

        Raises:
            ValidationError: 参数验证失败
        """
        validated_params = {}
        errors = []

        # 验证路径参数和查询参数
        for param in endpoint.parameters:
            param_name = param.name
            param_value = parameters.get(param_name)

            # 检查必需参数
            if param.required and param_value is None:
                errors.append(f"缺少必需参数: {param_name}")
                continue

            # 如果参数不存在且有默认值，使用默认值
            if param_value is None and param.default is not None:
                validated_params[param_name] = param.default
                continue

            # 如果参数不存在且不是必需的，跳过
            if param_value is None:
                continue

            # 类型转换和验证
            try:
                validated_value = self._validate_parameter_value(param, param_value)
                validated_params[param_name] = validated_value
            except ValueError as e:
                errors.append(f"参数 {param_name} 验证失败: {str(e)}")

        # 验证请求体参数
        if endpoint.request_body:
            body_errors = self._validate_request_body(endpoint, parameters, validated_params)
            errors.extend(body_errors)

        if errors:
            error_message = f"参数验证失败: {'; '.join(errors)}"
            raise ValueError(error_message)

        return validated_params

    def _validate_parameter_value(self, param, value) -> Any:
        """验证单个参数值"""
        # 类型转换
        if param.type == "integer":
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise ValueError(f"无法转换为整数: {value}")
        elif param.type == "number":
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise ValueError(f"无法转换为数字: {value}")
        elif param.type == "boolean":
            if isinstance(value, str):
                value = value.lower() in ("true", "1", "yes", "on")
            else:
                value = bool(value)
        else:
            value = str(value)

        # 枚举值验证
        if param.enum and value not in param.enum:
            raise ValueError(f"值必须是以下之一: {param.enum}")

        # 数值范围验证
        if param.type in ["integer", "number"]:
            if param.minimum is not None and value < param.minimum:
                raise ValueError(f"值不能小于 {param.minimum}")
            if param.maximum is not None and value > param.maximum:
                raise ValueError(f"值不能大于 {param.maximum}")

        return value

    def _validate_request_body(
        self, endpoint: APIEndpoint, parameters: Dict[str, Any], validated_params: Dict[str, Any]
    ) -> List[str]:
        """验证请求体参数"""
        errors = []

        if not endpoint.request_body:
            return errors

        schema = endpoint.request_body.get("schema", {})
        required_fields = schema.get("required", [])
        properties = schema.get("properties", {})

        # 检查必需字段
        if endpoint.request_body.get("required", False):
            for field in required_fields:
                if field not in parameters:
                    errors.append(f"缺少必需的请求体字段: {field}")

        # 验证字段类型（简单验证）
        for field_name, field_value in parameters.items():
            if field_name in properties:
                field_schema = properties[field_name]
                field_type = field_schema.get("type", "string")

                try:
                    self._validate_field_type(field_name, field_value, field_type)
                    validated_params[field_name] = field_value
                except ValueError as e:
                    errors.append(f"请求体字段 {field_name} 验证失败: {str(e)}")

        return errors

    def _validate_field_type(self, field_name: str, value: Any, expected_type: str) -> None:
        """验证字段类型"""
        if expected_type == "integer" and not isinstance(value, int):
            try:
                int(value)
            except (ValueError, TypeError):
                raise ValueError(f"字段 {field_name} 必须是整数")
        elif expected_type == "number" and not isinstance(value, (int, float)):
            try:
                float(value)
            except (ValueError, TypeError):
                raise ValueError(f"字段 {field_name} 必须是数字")
        elif expected_type == "boolean" and not isinstance(value, bool):
            if isinstance(value, str) and value.lower() not in ("true", "false", "1", "0"):
                raise ValueError(f"字段 {field_name} 必须是布尔值")
        elif expected_type == "array" and not isinstance(value, list):
            raise ValueError(f"字段 {field_name} 必须是数组")
        elif expected_type == "object" and not isinstance(value, dict):
            raise ValueError(f"字段 {field_name} 必须是对象")

    def set_auth_headers(self, headers: Dict[str, str]) -> None:
        """设置认证头"""
        self.session.headers.update(headers)

    def set_header(self, key: str, value: str) -> None:
        """设置请求头"""
        self.session.headers[key] = value

    def close(self) -> None:
        """关闭会话"""
        if self.session:
            self.session.close()
