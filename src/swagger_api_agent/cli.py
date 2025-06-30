#!/usr/bin/env python3
"""
Swagger API Agent 命令行界面
提供交互式的自然语言 API 调用功能
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict

from colorama import Fore, Style, init

from .agent import SwaggerAPIAgent

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

# 初始化 colorama
init(autoreset=True)


def setup_logging(debug: bool = False):
    """设置日志"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout) if debug else logging.NullHandler()],
    )


def print_success(message: str):
    """打印成功消息"""
    print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")


def print_error(message: str):
    """打印错误消息"""
    print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")


def print_warning(message: str):
    """打印警告消息"""
    print(f"{Fore.YELLOW}⚠️ {message}{Style.RESET_ALL}")


def print_info(message: str):
    """打印信息消息"""
    print(f"{Fore.CYAN}ℹ️ {message}{Style.RESET_ALL}")


def print_header(message: str):
    """打印标题"""
    print(f"\n{Fore.BLUE}{'='*60}")
    print(f"{Fore.BLUE}{message}")
    print(f"{Fore.BLUE}{'='*60}{Style.RESET_ALL}")


def format_json(data: Any) -> str:
    """格式化 JSON 数据"""
    return json.dumps(data, ensure_ascii=False, indent=2)


def print_api_response(result: Dict[str, Any]):
    """打印 API 响应结果"""
    if result["success"]:
        if "function_calls" in result:
            print_success("API 调用成功！")
            print(f"\n{Fore.GREEN}执行结果:{Style.RESET_ALL}")

            for i, call_result in enumerate(result["function_calls"], 1):
                explanation = call_result.get("explanation", f"调用 {call_result.get('function_name', 'unknown')}")
                print(f"\n{Fore.CYAN}调用 {i}: {explanation}{Style.RESET_ALL}")

                # 如果配置为不显示调用详情，则在这里显示
                if "call_info" in call_result and not os.getenv("SHOW_API_CALL_DETAILS", "true").lower() in (
                    "true",
                    "1",
                    "yes",
                    "on",
                ):
                    print(f"\n{Fore.YELLOW}{call_result['call_info']}{Style.RESET_ALL}")

                # 检查是否被用户取消
                if call_result.get("cancelled_by_user", False):
                    print(f"  {Fore.YELLOW}⏭️ 用户取消执行{Style.RESET_ALL}")
                    continue

                if call_result["success"]:
                    api_resp = call_result["api_response"]
                    print(f"  状态码: {Fore.GREEN}{api_resp['status_code']}{Style.RESET_ALL}")
                    print(f"  URL: {api_resp['method']} {api_resp['url']}")

                    if api_resp["data"]:
                        print(f"  响应数据:")
                        print(f"{Fore.WHITE}{format_json(api_resp['data'])}{Style.RESET_ALL}")
                else:
                    print(f"  {Fore.RED}错误: {call_result['error']}{Style.RESET_ALL}")
        else:
            print_success(result.get("message", "操作完成"))

        # 显示使用情况
        if "usage" in result and result["usage"]:
            usage = result["usage"]
            print(f"\n{Fore.MAGENTA}Token 使用情况:")
            print(f"  输入: {usage.get('prompt_tokens', 0)}")
            print(f"  输出: {usage.get('completion_tokens', 0)}")
            print(f"  总计: {usage.get('total_tokens', 0)}{Style.RESET_ALL}")
    else:
        print_error(f"操作失败: {result.get('error', '未知错误')}")


def print_available_functions(functions: list):
    """打印可用函数列表"""
    if not functions:
        print_warning("没有可用的 API 函数")
        return

    print_header("可用的 API 函数")

    for i, func in enumerate(functions, 1):
        print(f"\n{Fore.CYAN}{i}. {func['name']}{Style.RESET_ALL}")
        print(f"   描述: {func['description']}")

        # 显示参数信息
        params = func["parameters"]
        if params.get("properties"):
            print(f"   参数:")
            for param_name, param_info in params["properties"].items():
                required = "必需" if param_name in params.get("required", []) else "可选"
                param_type = param_info.get("type", "string")
                description = param_info.get("description", "")
                print(f"     - {param_name} ({param_type}, {required}): {description}")


def interactive_mode(agent: SwaggerAPIAgent):
    """交互模式"""
    print_header("Swagger API Agent 交互模式")
    print(f"{Fore.GREEN}欢迎使用 Swagger API Agent！")
    print(f"您可以用自然语言描述需求，我会自动选择并调用相应的 API。")
    print(f"输入 'help' 查看帮助，输入 'quit' 退出。{Style.RESET_ALL}\n")

    while True:
        try:
            # 获取用户输入
            user_input = input(f"{Fore.YELLOW}👤 您: {Style.RESET_ALL}").strip()

            if not user_input:
                continue

            # 处理特殊命令
            if user_input.lower() in ["quit", "exit", "q"]:
                print_info("再见！")
                break
            elif user_input.lower() == "help":
                show_help()
                continue
            elif user_input.lower() == "functions":
                functions = agent.get_available_functions()
                print_available_functions(functions)
                continue
            elif user_input.lower() == "clear":
                agent.clear_conversation_history()
                print_info("对话历史已清空")
                continue
            elif user_input.lower() == "status":
                status = agent.get_status()
                print_header("系统状态")
                print(format_json(status))
                continue

            # 处理自然语言输入
            print(f"\n{Fore.BLUE}🤖 正在处理您的请求...{Style.RESET_ALL}")

            execution_context = {"is_cli_mode": True}
            result = agent.process_natural_language(user_input, execution_context=execution_context)

            print(f"\n{Fore.BLUE}🤖 助手: {Style.RESET_ALL}")
            print_api_response(result)
            print()

        except KeyboardInterrupt:
            print_info("\n\n用户中断，退出程序")
            break
        except Exception as e:
            print_error(f"处理过程中出现错误: {str(e)}")


def show_help():
    """显示帮助信息"""
    print_header("帮助信息")
    print(f"{Fore.GREEN}可用命令:")
    print(f"  help      - 显示此帮助信息")
    print(f"  functions - 显示所有可用的 API 函数")
    print(f"  clear     - 清空对话历史")
    print(f"  status    - 显示系统状态")
    print(f"  quit/exit - 退出程序")
    print(f"\n{Fore.GREEN}使用示例:")
    print(f"  获取用户列表")
    print(f"  创建一个新用户，名字叫张三，邮箱是zhangsan@example.com")
    print(f"  查找ID为123的用户信息")
    print(f"  搜索价格在100到500之间的电子产品{Style.RESET_ALL}")


def test_mode(agent: SwaggerAPIAgent):
    """测试模式"""
    print_header("Swagger API Agent 测试模式")

    test_cases = [
        "获取所有用户列表",
        "创建一个用户，名字叫李四，邮箱是lisi@example.com",
        "查找ID为123的用户信息",
        "搜索电子产品",
        "创建一个订单，用户ID是123，购买产品ID为456，数量为2",
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{Fore.CYAN}测试用例 {i}: {test_case}{Style.RESET_ALL}")

        execution_context = {"is_cli_mode": True}
        result = agent.process_natural_language(test_case, execution_context=execution_context)
        print_api_response(result)

        # 等待用户按回车继续
        input(f"\n{Fore.YELLOW}按回车键继续下一个测试...{Style.RESET_ALL}")


def list_functions_mode(agent: SwaggerAPIAgent):
    """列出所有函数"""
    functions = agent.get_available_functions()
    print_available_functions(functions)


def call_function_mode(agent: SwaggerAPIAgent, function_name: str, parameters_json: str):
    """直接调用函数模式"""
    try:
        parameters = json.loads(parameters_json) if parameters_json else {}

        print_info(f"直接调用函数: {function_name}")
        print_info(f"参数: {format_json(parameters)}")

        # 检查是否启用了用户确认
        if os.getenv("REQUIRE_USER_CONFIRMATION", "false").lower() in ("true", "1", "yes", "on"):
            # 使用 _execute_function_call 方法来支持用户确认
            function_call = {"name": function_name, "arguments": parameters}

            function_schemas = agent.parser.get_function_schemas()
            execution_context = {"is_cli_mode": True}

            result = agent._execute_function_call(function_call, function_schemas, execution_context)

            if result.get("cancelled_by_user", False):
                print_warning("用户取消了操作")
                return
            elif result["success"]:
                print_success("API 调用成功！")
                api_resp = result["api_response"]
                print(f"状态码: {api_resp['status_code']}")
                print(f"URL: {api_resp['method']} {api_resp['url']}")

                if api_resp["data"]:
                    print("响应数据:")
                    print(format_json(api_resp["data"]))
            else:
                print_error(f"API 调用失败: {result['error']}")
        else:
            # 直接调用，不需要确认
            result = agent.call_api_directly(function_name, parameters)

            if result["success"]:
                print_success("API 调用成功！")
                api_resp = result["api_response"]
                print(f"状态码: {api_resp['status_code']}")
                print(f"URL: {api_resp['method']} {api_resp['url']}")

                if api_resp["data"]:
                    print("响应数据:")
                    print(format_json(api_resp["data"]))
            else:
                print_error(f"API 调用失败: {result['error']}")

    except json.JSONDecodeError:
        print_error("参数格式错误，请使用有效的 JSON 格式")
    except Exception as e:
        print_error(f"调用失败: {str(e)}")


def main():
    """主函数"""
    # 加载环境变量
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        # 如果没有安装 python-dotenv，忽略错误
        pass

    parser = argparse.ArgumentParser(
        description="Swagger API Agent - 自然语言调用 API 接口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s                                    # 启动交互模式
  %(prog)s --test                             # 运行测试模式
  %(prog)s --list-functions                   # 列出所有可用函数
  %(prog)s --call getUsers '{"page": 1}'      # 直接调用函数
  %(prog)s --openapi custom.yaml              # 使用自定义 OpenAPI 文档
  %(prog)s --api-token "your_token_here"      # 设置 API 认证 Token
        """,
    )

    parser.add_argument("--openapi", type=str, help="OpenAPI 文档文件路径")

    parser.add_argument("--api-url", type=str, help="API 基础 URL")

    parser.add_argument("--api-token", type=str, help="API 认证 Token (Bearer Token)")

    parser.add_argument("--api-key", type=str, help="DeepSeek API 密钥")

    parser.add_argument("--test", action="store_true", help="运行测试模式")

    parser.add_argument("--list-functions", action="store_true", help="列出所有可用的 API 函数")

    parser.add_argument("--call", type=str, help="直接调用指定的函数")

    parser.add_argument("--params", type=str, default="{}", help="函数参数（JSON 格式）")

    parser.add_argument("--debug", action="store_true", help="启用调试模式")

    parser.add_argument("--export-schemas", type=str, help="导出函数模式到指定文件")

    parser.add_argument("--require-confirmation", action="store_true", help="执行 API 调用前需要用户确认")

    args = parser.parse_args()

    # 设置日志
    setup_logging(args.debug)

    # 处理用户确认参数
    if args.require_confirmation:
        os.environ["REQUIRE_USER_CONFIRMATION"] = "true"

    try:
        # 初始化 agent
        agent = SwaggerAPIAgent(
            openapi_file=args.openapi, 
            api_base_url=args.api_url, 
            api_token=args.api_token,
            deepseek_api_key=args.api_key
        )

        # 初始化系统
        print_info("正在初始化 Swagger API Agent...")
        if not agent.initialize():
            print_error(f"初始化失败: {agent.last_error}")
            sys.exit(1)

        print_success("初始化成功！")

        # 显示 API 信息
        api_info = agent.get_api_info()
        print_info(f"已加载 API: {api_info['title']} v{api_info['version']}")
        print_info(f"发现 {api_info['endpoints_count']} 个 API 端点")

        # 导出模式
        if args.export_schemas:
            print_info(f"导出函数模式到: {args.export_schemas}")
            agent.export_function_schemas(args.export_schemas)
            print_success("导出完成！")
            return

        # 根据参数选择运行模式
        if args.test:
            test_mode(agent)
        elif args.list_functions:
            list_functions_mode(agent)
        elif args.call:
            call_function_mode(agent, args.call, args.params)
        else:
            interactive_mode(agent)

    except KeyboardInterrupt:
        print_info("\n用户中断，程序退出")
        sys.exit(0)
    except Exception as e:
        print_error(f"程序运行异常: {str(e)}")
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
