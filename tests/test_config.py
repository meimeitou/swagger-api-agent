"""
测试配置模块
"""

import os

from swagger_api_agent.config import (DEEPSEEK_API_BASE, DEFAULT_API_BASE_URL,
                                      DEFAULT_LLM_MODEL, DEFAULT_OPENAPI_FILE)


def test_default_config():
    """测试默认配置"""
    assert DEFAULT_OPENAPI_FILE is not None
    assert DEFAULT_API_BASE_URL is not None
    assert DEFAULT_LLM_MODEL is not None
    assert DEEPSEEK_API_BASE is not None


def test_environment_variables():
    """测试环境变量读取"""
    # 设置测试环境变量
    test_value = "test_value"
    os.environ["TEST_CONFIG"] = test_value

    # 验证能正确读取
    assert os.getenv("TEST_CONFIG") == test_value

    # 清理
    del os.environ["TEST_CONFIG"]
