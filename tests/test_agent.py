"""
测试 Agent 基本功能
"""

from unittest.mock import patch

from swagger_api_agent import SwaggerAPIAgent


class TestSwaggerAPIAgent:
    """测试 Swagger API Agent"""

    def test_init(self, mock_env):
        """测试初始化"""
        agent = SwaggerAPIAgent()
        assert agent is not None
        assert hasattr(agent, "openapi_file")
        assert hasattr(agent, "api_base_url")

    @patch("swagger_api_agent.agent.LLMClient")
    @patch("swagger_api_agent.agent.APICaller")
    @patch("swagger_api_agent.agent.OpenAPIParser")
    def test_initialize(self, mock_parser, mock_caller, mock_llm, mock_env):
        """测试组件初始化"""
        # 设置 mock
        mock_parser.return_value.parse_file.return_value = True
        mock_llm.return_value.test_connection.return_value = True

        agent = SwaggerAPIAgent()
        result = agent.initialize()

        assert result is True
        assert agent.is_initialized is True

    def test_get_api_info(self, mock_env):
        """测试获取 API 信息"""
        agent = SwaggerAPIAgent()
        # 需要先初始化才能获取信息
        # 这里只测试方法存在
        assert hasattr(agent, "get_api_info")

    def test_get_available_functions(self, mock_env):
        """测试获取可用函数"""
        agent = SwaggerAPIAgent()
        assert hasattr(agent, "get_available_functions")
