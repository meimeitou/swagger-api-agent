"""
配置文件
包含所有默认配置和环境变量设置
"""

import os
from datetime import datetime

# 加载环境变量文件
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # 如果没有安装 python-dotenv，忽略错误
    pass

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com")
DEFAULT_LLM_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# OpenAPI 和 API 基础配置
DEFAULT_OPENAPI_FILE = os.getenv("OPENAPI_FILE", "examples/example_openapi.yaml")
DEFAULT_API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")

# 当前用户信息
CURRENT_USER = "meimeitou"
CURRENT_TIME = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

# Agent 配置
MAX_RETRIES = 3
TIMEOUT = 120

# 显示和确认配置
SHOW_API_CALL_DETAILS = os.getenv("SHOW_API_CALL_DETAILS", "true").lower() in ("true", "1", "yes", "on")
REQUIRE_USER_CONFIRMATION = os.getenv("REQUIRE_USER_CONFIRMATION", "false").lower() in ("true", "1", "yes", "on")

# LLM 配置
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TEMPERATURE = 0.1

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 文件路径配置
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
EXAMPLES_DIR = os.path.join(PROJECT_ROOT, "examples")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
