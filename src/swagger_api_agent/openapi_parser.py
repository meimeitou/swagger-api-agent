"""
OpenAPI 文档解析器
用于解析 Swagger/OpenAPI 文档并转换为 Function Calling Schema
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Union

from prance import ResolvingParser
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ParameterSchema(BaseModel):
    """参数模式定义"""

    name: str
    type: str
    description: Optional[str] = None
    required: bool = False
    default: Any = None
    enum: Optional[List[str]] = None
    minimum: Optional[Union[int, float]] = None
    maximum: Optional[Union[int, float]] = None
    format: Optional[str] = None


class FunctionSchema(BaseModel):
    """Function Calling Schema"""

    name: str
    description: str
    parameters: Dict[str, Any]


class APIEndpoint(BaseModel):
    """API 端点信息"""

    path: str
    method: str
    operation_id: str
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: List[ParameterSchema] = Field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Any] = Field(default_factory=dict)


class OpenAPIParser:
    """OpenAPI 文档解析器"""

    def __init__(self, openapi_file: str):
        """
        初始化解析器

        Args:
            openapi_file: OpenAPI 文档文件路径
        """
        self.openapi_file = openapi_file
        self.parser = None
        self.spec = None
        self.endpoints: List[APIEndpoint] = []
        self.function_schemas: List[FunctionSchema] = []

    def parse(self) -> None:
        """解析 OpenAPI 文档"""
        try:
            logger.info(f"开始解析 OpenAPI 文档: {self.openapi_file}")

            # 使用 prance 解析文档，禁用验证以避免后端问题
            try:
                # 首先尝试使用 openapi-spec-validator
                self.parser = ResolvingParser(self.openapi_file, backend="openapi-spec-validator")
            except Exception:
                try:
                    # 如果失败，尝试禁用验证
                    self.parser = ResolvingParser(self.openapi_file, validate_swagger=False)
                except Exception:
                    # 最后尝试使用原始方法，但不验证
                    import yaml

                    with open(self.openapi_file, "r", encoding="utf-8") as f:
                        self.spec = yaml.safe_load(f)
                    self.parser = None

            if self.parser:
                self.spec = self.parser.specification

            logger.info(f"文档标题: {self.spec.get('info', {}).get('title', 'Unknown')}")
            logger.info(f"文档版本: {self.spec.get('info', {}).get('version', 'Unknown')}")

            # 解析所有路径和方法
            self._parse_paths()

            # 生成 Function Calling Schemas
            self._generate_function_schemas()

            logger.info(f"解析完成，共找到 {len(self.endpoints)} 个 API 端点")

        except Exception as e:
            logger.error(f"解析 OpenAPI 文档失败: {str(e)}")
            raise

    def _parse_paths(self) -> None:
        """解析路径和方法"""
        paths = self.spec.get("paths", {})

        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() in ["get", "post", "put", "delete", "patch"]:
                    endpoint = self._parse_operation(path, method.lower(), operation)
                    if endpoint:
                        self.endpoints.append(endpoint)

    def _parse_operation(self, path: str, method: str, operation: Dict[str, Any]) -> Optional[APIEndpoint]:
        """解析单个操作"""
        try:
            operation_id = operation.get("operationId", f"{method}_{self._path_to_name(path)}")
            summary = operation.get("summary", "")
            description = operation.get("description", summary)

            # 解析参数
            parameters = self._parse_parameters(operation.get("parameters", []))

            # 解析请求体
            request_body = self._parse_request_body(operation.get("requestBody"))

            # 解析响应
            responses = operation.get("responses", {})

            endpoint = APIEndpoint(
                path=path,
                method=method,
                operation_id=operation_id,
                summary=summary,
                description=description,
                parameters=parameters,
                request_body=request_body,
                responses=responses,
            )

            return endpoint

        except Exception as e:
            logger.warning(f"解析操作失败 {method} {path}: {str(e)}")
            return None

    def _parse_parameters(self, parameters: List[Dict[str, Any]]) -> List[ParameterSchema]:
        """解析参数"""
        parsed_params = []

        for param in parameters:
            try:
                schema = param.get("schema", {})

                param_schema = ParameterSchema(
                    name=param["name"],
                    type=schema.get("type", "string"),
                    description=param.get("description", ""),
                    required=param.get("required", False),
                    default=schema.get("default"),
                    enum=schema.get("enum"),
                    minimum=schema.get("minimum"),
                    maximum=schema.get("maximum"),
                    format=schema.get("format"),
                )

                parsed_params.append(param_schema)

            except Exception as e:
                logger.warning(f"解析参数失败: {param.get('name', 'unknown')}: {str(e)}")

        return parsed_params

    def _parse_request_body(self, request_body: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """解析请求体"""
        if not request_body:
            return None

        try:
            content = request_body.get("content", {})

            # 优先处理 application/json
            json_content = content.get("application/json")
            if json_content:
                return {
                    "required": request_body.get("required", False),
                    "content_type": "application/json",
                    "schema": json_content.get("schema", {}),
                }

            # 处理其他内容类型
            for content_type, content_schema in content.items():
                return {
                    "required": request_body.get("required", False),
                    "content_type": content_type,
                    "schema": content_schema.get("schema", {}),
                }

        except Exception as e:
            logger.warning(f"解析请求体失败: {str(e)}")

        return None

    def _generate_function_schemas(self) -> None:
        """生成 Function Calling Schemas"""
        self.function_schemas = []

        for endpoint in self.endpoints:
            try:
                function_schema = self._endpoint_to_function_schema(endpoint)
                if function_schema:
                    self.function_schemas.append(function_schema)
            except Exception as e:
                logger.warning(f"生成函数模式失败 {endpoint.operation_id}: {str(e)}")

    def _endpoint_to_function_schema(self, endpoint: APIEndpoint) -> Optional[FunctionSchema]:
        """将 API 端点转换为 Function Schema"""
        try:
            # 生成函数名
            function_name = self._generate_function_name(endpoint)

            # 生成描述
            description = self._generate_function_description(endpoint)

            # 生成参数模式
            parameters = self._generate_parameters_schema(endpoint)

            return FunctionSchema(name=function_name, description=description, parameters=parameters)

        except Exception as e:
            logger.error(f"转换端点到函数模式失败: {str(e)}")
            return None

    def _generate_function_name(self, endpoint: APIEndpoint) -> str:
        """生成函数名"""
        # 使用 operationId 作为函数名，确保唯一性
        function_name = endpoint.operation_id

        # 清理函数名，确保符合命名规范
        function_name = re.sub(r"[^a-zA-Z0-9_]", "_", function_name)
        function_name = re.sub(r"_+", "_", function_name)
        function_name = function_name.strip("_")

        return function_name

    def _generate_function_description(self, endpoint: APIEndpoint) -> str:
        """生成函数描述"""
        description_parts = []

        if endpoint.summary:
            description_parts.append(endpoint.summary)

        if endpoint.description and endpoint.description != endpoint.summary:
            description_parts.append(endpoint.description)

        description_parts.append(f"API端点: {endpoint.method.upper()} {endpoint.path}")

        return " | ".join(description_parts)

    def _generate_parameters_schema(self, endpoint: APIEndpoint) -> Dict[str, Any]:
        """生成参数模式"""
        properties = {}
        required = []

        # 处理路径参数和查询参数
        for param in endpoint.parameters:
            prop_schema = {
                "type": self._convert_type(param.type),
                "description": param.description or f"{param.name} 参数",
            }

            # 添加约束条件
            if param.enum:
                prop_schema["enum"] = param.enum
            if param.minimum is not None:
                prop_schema["minimum"] = param.minimum
            if param.maximum is not None:
                prop_schema["maximum"] = param.maximum
            if param.format:
                prop_schema["format"] = param.format
            if param.default is not None:
                prop_schema["default"] = param.default

            properties[param.name] = prop_schema

            if param.required:
                required.append(param.name)

        # 处理请求体参数
        if endpoint.request_body:
            body_schema = endpoint.request_body.get("schema", {})
            if body_schema.get("type") == "object":
                # 展开对象属性
                body_properties = body_schema.get("properties", {})
                for prop_name, prop_schema in body_properties.items():
                    properties[prop_name] = self._convert_schema(prop_schema)

                # 添加必需字段
                body_required = body_schema.get("required", [])
                if endpoint.request_body.get("required", False):
                    required.extend(body_required)
            else:
                # 整个请求体作为一个参数
                properties["request_body"] = self._convert_schema(body_schema)
                if endpoint.request_body.get("required", False):
                    required.append("request_body")

        return {"type": "object", "properties": properties, "required": required}

    def _convert_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """转换 JSON Schema"""
        converted = {}

        schema_type = schema.get("type", "string")
        converted["type"] = self._convert_type(schema_type)

        if "description" in schema:
            converted["description"] = schema["description"]

        if "enum" in schema:
            converted["enum"] = schema["enum"]

        if "default" in schema:
            converted["default"] = schema["default"]

        if "minimum" in schema:
            converted["minimum"] = schema["minimum"]

        if "maximum" in schema:
            converted["maximum"] = schema["maximum"]

        if "format" in schema:
            converted["format"] = schema["format"]

        if schema_type == "array" and "items" in schema:
            converted["items"] = self._convert_schema(schema["items"])

        if schema_type == "object" and "properties" in schema:
            converted["properties"] = {}
            for prop_name, prop_schema in schema["properties"].items():
                converted["properties"][prop_name] = self._convert_schema(prop_schema)

            if "required" in schema:
                converted["required"] = schema["required"]

        return converted

    def _convert_type(self, openapi_type: str) -> str:
        """转换数据类型"""
        type_mapping = {
            "integer": "integer",
            "number": "number",
            "string": "string",
            "boolean": "boolean",
            "array": "array",
            "object": "object",
        }
        return type_mapping.get(openapi_type, "string")

    def _path_to_name(self, path: str) -> str:
        """将路径转换为名称"""
        # 移除参数部分 {param}
        name = re.sub(r"\{[^}]+\}", "by_id", path)
        # 移除开头的斜杠
        name = name.lstrip("/")
        # 替换斜杠为下划线
        name = name.replace("/", "_")
        # 清理特殊字符
        name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        name = re.sub(r"_+", "_", name)
        name = name.strip("_")

        return name or "api"

    def get_function_schemas(self) -> List[Dict[str, Any]]:
        """获取 Function Calling Schemas"""
        return [
            {
                "type": "function",
                "function": {"name": schema.name, "description": schema.description, "parameters": schema.parameters},
            }
            for schema in self.function_schemas
        ]

    def get_endpoint_by_function_name(self, function_name: str) -> Optional[APIEndpoint]:
        """根据函数名获取对应的 API 端点"""
        for endpoint in self.endpoints:
            if self._generate_function_name(endpoint) == function_name:
                return endpoint
        return None

    def get_api_info(self) -> Dict[str, Any]:
        """获取 API 基本信息"""
        if not self.spec:
            return {}

        info = self.spec.get("info", {})
        servers = self.spec.get("servers", [])

        return {
            "title": info.get("title", "Unknown API"),
            "description": info.get("description", ""),
            "version": info.get("version", "1.0.0"),
            "servers": servers,
            "endpoints_count": len(self.endpoints),
        }

    def export_schemas(self, output_file: str) -> None:
        """导出 Function Schemas 到文件"""
        try:
            schemas_data = {
                "api_info": self.get_api_info(),
                "function_schemas": [schema.dict() for schema in self.function_schemas],
                "endpoints": [endpoint.dict() for endpoint in self.endpoints],
            }

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(schemas_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Function Schemas 已导出到: {output_file}")

        except Exception as e:
            logger.error(f"导出 Function Schemas 失败: {str(e)}")
            raise
