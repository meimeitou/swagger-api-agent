"""
Swagger API Agent - 自动化自然语言调用 API 接口

一个基于大语言模型的智能 API 调用代理，能够理解自然语言描述并自动选择和调用相应的 API 接口。

主要功能：
- 解析 OpenAPI/Swagger 文档
- 自然语言理解和 API 调用
- 智能参数推断和验证
- 多种调用模式（Web API、直接调用）
- 用户确认和安全控制

作者: Swagger API Agent Team
版本: 1.0.0
许可证: MIT License
"""

from .agent import SwaggerAPIAgent
from .user_session_manager import UserSessionManager, get_session_manager, get_or_create_user_agent
from .config import (DEEPSEEK_API_BASE, DEFAULT_API_BASE_URL,
                     DEFAULT_LLM_MODEL, DEFAULT_OPENAPI_FILE,
                     REQUIRE_USER_CONFIRMATION, SHOW_API_CALL_DETAILS)

__version__ = "1.0.0"
__author__ = "Swagger API Agent Team"
__email__ = "team@swagger-api-agent.com"
__license__ = "MIT"

__all__ = [
    "SwaggerAPIAgent",
    "UserSessionManager",
    "get_session_manager", 
    "get_or_create_user_agent",
    "DEFAULT_OPENAPI_FILE",
    "DEFAULT_API_BASE_URL",
    "DEFAULT_LLM_MODEL",
    "DEEPSEEK_API_BASE",
    "SHOW_API_CALL_DETAILS",
    "REQUIRE_USER_CONFIRMATION",
    "__version__",
    "__author__",
    "__email__",
    "__license__",
]
