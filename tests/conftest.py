"""
测试配置
"""

import os
import sys
from pathlib import Path

import pytest

# 设置测试环境
TEST_ROOT = Path(__file__).parent
PROJECT_ROOT = TEST_ROOT.parent
SRC_ROOT = PROJECT_ROOT / "src"

# 添加 src 到 Python 路径
sys.path.insert(0, str(SRC_ROOT))

# 测试配置
TEST_OPENAPI_FILE = PROJECT_ROOT / "examples" / "example_openapi.yaml"
TEST_API_BASE_URL = "http://localhost:8080"


@pytest.fixture
def mock_env():
    """模拟环境变量"""
    original_env = dict(os.environ)
    os.environ.update(
        {
            "DEEPSEEK_API_KEY": "test-key",
            "OPENAPI_FILE": str(TEST_OPENAPI_FILE),
            "API_BASE_URL": TEST_API_BASE_URL,
        }
    )
    yield
    os.environ.clear()
    os.environ.update(original_env)
