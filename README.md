# Swagger API Agent

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

一个智能的自动化 API 调用工具，支持用自然语言描述需求，自动选择并调用 Swagger/OpenAPI 文档中定义的接口。

## 🚀 功能特性

- **自然语言理解**: 用户可以用自然语言描述需求，系统自动理解并选择合适的 API
- **自动参数解析**: 智能解析和验证 API 参数，支持类型转换和约束验证  
- **Function Calling**: 基于大模型的 Function Calling 功能，精确匹配 API 接口
- **API 调用透明化**: 执行前自动显示要调用的接口和参数信息，增强调用过程的可见性
- **用户确认机制**: 可选的执行前用户确认，确保 API 调用的安全性和可控性
- **多种调用方式**: 支持自然语言调用、直接函数调用、命令行工具、Web API 等
- **完整的错误处理**: 详细的错误信息和调试支持
- **对话历史**: 支持上下文对话，记录调用历史
- **灵活配置**: 支持多种认证方式和自定义配置

## 📋 系统要求

- Python 3.8+
- DeepSeek API 密钥（用于自然语言处理）
- 有效的 Swagger/OpenAPI 文档

## 🛠️ 安装

### 使用 Poetry 安装（推荐）

项目使用 Poetry 进行依赖管理。请确保已安装 Poetry：

```bash
# 安装 Poetry（如果尚未安装）
curl -sSL https://install.python-poetry.org | python3 -

# 克隆项目
git clone <your-repo-url>
cd swagger-api-agent

# 安装依赖
poetry install

# 激活虚拟环境
poetry shell
```

### 开发模式安装

```bash
# 安装包括开发和测试依赖
poetry install --with dev,test

# 或使用 Makefile
make install-dev
```

### 传统方式安装（兼容性）

#### 使用 pip 安装

```bash
pip install swagger-api-agent
```

#### 从源码安装

```bash
git clone <your-repo-url>
cd swagger-api-agent
pip install -e .
```

#### 开发模式安装

```bash
git clone <your-repo-url>
cd swagger-api-agent
pip install -e ".[dev]"
```

## 👨‍💻 开发者指南

### Poetry 工作流

项目采用 Poetry 进行依赖管理，以下是常用的开发命令：

```bash
# 安装依赖
make install-dev

# 运行测试
make test

# 代码检查
make lint

# 代码格式化
make format

# 构建项目
make build

# 运行 CLI
make run-cli

# 运行 Web API
make run-web

# 查看所有可用命令
make help
```

### Poetry 命令

```bash
# 安装依赖
poetry install

# 激活虚拟环境
poetry shell

# 运行命令
poetry run python script.py

# 添加新依赖
poetry add package-name

# 添加开发依赖
poetry add --group dev package-name

# 更新依赖
poetry update

# 查看依赖信息
poetry show
```

## ⚙️ 配置

### 1. 环境变量配置

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置必要的配置：

```env
# DeepSeek API 配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_API_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# OpenAPI 文档和 API 配置
OPENAPI_FILE=examples/example_openapi.yaml
API_BASE_URL=http://localhost:8080

# 功能控制
SHOW_API_CALL_DETAILS=true
REQUIRE_USER_CONFIRMATION=false
```

### 2. OpenAPI 文档

将你的 OpenAPI/Swagger 文档放在项目中，或通过环境变量指定路径。

## 🎯 快速开始

### 命令行使用

```bash
# 启动交互模式
swagger-api-agent

# 使用自定义配置
swagger-api-agent --openapi your-api.yaml --api-url http://your-api.com

# 直接调用函数
swagger-api-agent --call getUsers --params '{"limit": 5}'

# 启用用户确认
swagger-api-agent --require-confirmation

# 显示可用函数
swagger-api-agent --list-functions
```

### Web API 使用

```bash
# 启动 Web 服务
swagger-web-api --host 0.0.0.0 --port 5000 --api-url http://localhost:8080

# 或使用 Python 模块
python -m swagger_api_agent.web_api --port 5000
```

然后访问 `http://localhost:5000` 查看 API 文档。

### 程序化使用

```python
from swagger_api_agent import SwaggerAPIAgent

# 初始化 agent
agent = SwaggerAPIAgent(
    openapi_file="your-api.yaml",
    api_base_url="http://your-api.com",
    deepseek_api_key="your-api-key"
)

# 初始化
if agent.initialize():
    # 自然语言调用
    result = agent.process_natural_language("获取前5个用户")
    
    # 直接调用
    result = agent.call_api_directly("getUsers", {"limit": 5})
    
    print(result)
```

## 📂 项目结构

```
swagger-api-agent/
├── src/swagger_api_agent/     # 主要源代码
│   ├── __init__.py           # 包初始化
│   ├── agent.py              # 主要 Agent 类
│   ├── api_caller.py         # API 调用器
│   ├── cli.py                # 命令行界面
│   ├── config.py             # 配置文件
│   ├── llm_client.py         # LLM 客户端
│   ├── openapi_parser.py     # OpenAPI 解析器
│   └── web_api.py            # Web API 服务
├── tests/                    # 测试文件
├── examples/                 # 示例文件
│   └── example_openapi.yaml  # 示例 API 文档
├── scripts/                  # 脚本文件
│   ├── mock_server.py        # Mock 服务器
│   └── start_mock_server.sh  # 启动脚本
├── docs/                     # 文档
├── requirements.txt          # 依赖列表
├── pyproject.toml           # 项目配置
├── setup.py                 # 安装脚本
└── README.md                # 说明文档
```

### 2. 创建虚拟环境

```bash
./manager.sh venv
```

### 4. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# DeepSeek API 配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_API_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# OpenAPI 文档路径
OPENAPI_FILE=example_openapi.yaml

# API 服务器配置  
API_BASE_URL=https://api.example.com/v1

# 调试模式
DEBUG=True
```

## 🎯 快速开始

### 1. 运行测试

```bash
python test.py
```

### 2. 启动交互式命令行

```bash
python cli.py
```

### 3. 启动 Web API 服务

```bash
python web_api.py --host 0.0.0.0 --port 5000
```

### 4. 使用示例

#### 自然语言调用示例

```python
from swagger_api_agent import SwaggerAPIAgent

# 初始化 agent
agent = SwaggerAPIAgent()
agent.initialize()

# 用自然语言调用 API
result = agent.process_natural_language("获取所有用户列表")
print(result)

# 创建用户
result = agent.process_natural_language(
    "创建一个新用户，名字叫张三，邮箱是zhangsan@example.com"
)
print(result)

# 查询特定用户
result = agent.process_natural_language("查找ID为123的用户信息")
print(result)
```

#### 直接函数调用示例

```python
# 直接调用 API 函数
result = agent.call_api_directly("getUsers", {
    "page": 1,
    "limit": 10,
    "role": "user"
})
print(result)

# 创建用户
result = agent.call_api_directly("createUser", {
    "name": "李四",
    "email": "lisi@example.com",
    "role": "user"
})
print(result)
```

## 📖 API 文档

### 核心类

#### `SwaggerAPIAgent`

主要的代理类，整合所有功能组件。

**主要方法:**

- `initialize()`: 初始化所有组件
- `process_natural_language(user_input)`: 处理自然语言输入
- `call_api_directly(function_name, parameters)`: 直接调用 API 函数
- `get_available_functions()`: 获取可用函数列表
- `get_api_info()`: 获取 API 信息
- `set_api_auth(auth_type, **kwargs)`: 设置 API 认证

#### `OpenAPIParser`

OpenAPI 文档解析器。

**主要方法:**

- `parse()`: 解析 OpenAPI 文档
- `get_function_schemas()`: 获取 Function Calling Schemas
- `get_endpoint_by_function_name(name)`: 根据函数名获取端点
- `export_schemas(output_file)`: 导出函数模式

#### `APICaller`

API 调用器，负责实际的 HTTP 请求。

**主要方法:**

- `call_api(endpoint, parameters)`: 调用 API
- `validate_parameters(endpoint, parameters)`: 验证参数
- `set_auth_headers(headers)`: 设置认证头

#### `LLMClient`

大模型客户端，支持 Function Calling。

**主要方法:**

- `generate_function_call(message, schemas)`: 生成函数调用
- `chat_with_context(messages, schemas)`: 上下文对话
- `validate_api_key()`: 验证 API 密钥

### Web API 接口

启动 Web 服务后，可以通过 HTTP API 调用：

#### `POST /api/process`

处理自然语言输入。

**请求体:**

```json
{
  "message": "获取用户列表",
  "context": {}
}
```

**响应:**

```json
{
  "success": true,
  "function_calls": [...],
  "message": "执行结果",
  "usage": {...}
}
```

#### `POST /api/call`

直接调用函数。

**请求体:**

```json
{
  "function_name": "getUsers",
  "parameters": {
    "page": 1,
    "limit": 10
  }
}
```

#### `GET /api/functions`

获取可用函数列表。

#### `GET /api/info`

获取 API 信息和系统状态。

#### `GET /api/history`

获取对话历史。

#### `DELETE /api/history`

清空对话历史。

## 🎮 命令行工具

### 基本用法

```bash
# 启动交互模式
python cli.py

# 运行测试模式
python cli.py --test

# 列出所有可用函数
python cli.py --list-functions

# 直接调用函数
python cli.py --call getUsers --params '{"page": 1}'

# 使用自定义 OpenAPI 文档
python cli.py --openapi custom.yaml

# 启用调试模式
python cli.py --debug

# 需要用户确认才执行 API 调用
python cli.py --require-confirmation

# 导出函数模式
python cli.py --export-schemas schemas.json
```

### 交互模式命令

在交互模式中，可以使用以下命令：

- `help` - 显示帮助信息
- `functions` - 列出所有可用函数
- `clear` - 清空对话历史
- `status` - 显示系统状态
- `quit/exit` - 退出程序

## 🔧 配置选项

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | 必需 |
| `DEEPSEEK_API_URL` | DeepSeek API 地址 | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | 使用的模型名称 | `deepseek-chat` |
| `OPENAPI_FILE` | OpenAPI 文档路径 | `example_openapi.yaml` |
| `API_BASE_URL` | API 基础 URL | `https://api.example.com/v1` |
| `SHOW_API_CALL_DETAILS` | 执行前显示接口调用详情 | `true` |
| `REQUIRE_USER_CONFIRMATION` | 执行前需要用户确认 | `false` |
| `DEBUG` | 调试模式 | `False` |

### API 认证

支持多种认证方式：

#### Bearer Token

```python
agent.set_api_auth('bearer', token='your_token_here')
```

#### API Key

```python
agent.set_api_auth('apikey', key='your_api_key', header='X-API-Key')
```

## 📁 项目结构

```
swagger-api-agent/
├── openapi_parser.py      # OpenAPI 文档解析器
├── api_caller.py          # API 调用器
├── llm_client.py          # 大模型客户端
├── swagger_api_agent.py   # 主要代理类
├── cli.py                 # 命令行界面
├── web_api.py            # Web API 服务
├── test.py               # 测试脚本
├── config.py             # 配置文件
├── requirements.in       # 依赖列表
├── example_openapi.yaml  # 示例 OpenAPI 文档
├── .env                  # 环境变量配置
└── README.md            # 项目文档
```

## 🧪 测试

### 运行全部测试

```bash
python test.py
```

### 运行特定测试

```bash
# 测试 OpenAPI 解析
python -c "from test import test_openapi_parser; test_openapi_parser()"

# 测试 Agent 功能
python -c "from test import test_swagger_agent; test_swagger_agent()"
```

## 📝 使用示例

### 1. 电商 API 调用

```python
# 搜索产品
result = agent.process_natural_language("搜索价格在100到500之间的电子产品")

# 创建订单
result = agent.process_natural_language(
    "为用户123创建一个订单，包含产品456，数量为2"
)
```

### 2. 用户管理

```python
# 获取用户列表
result = agent.process_natural_language("获取所有管理员用户")

# 更新用户信息
result = agent.process_natural_language("更新用户123的邮箱为new@example.com")

# 删除用户
result = agent.process_natural_language("删除用户456")
```

### 3. 数据查询

```python
# 复杂查询
result = agent.process_natural_language(
    "查找最近创建的10个用户，按创建时间排序"
)

# 统计信息
result = agent.process_natural_language("统计每个角色的用户数量")
```

## 🔍 故障排除

### 常见问题

#### 1. API 密钥错误

```
错误: 大模型调用失败: Invalid API key
```

**解决方案**: 检查 `.env` 文件中的 `DEEPSEEK_API_KEY` 配置。

#### 2. OpenAPI 文档解析失败

```
错误: 解析 OpenAPI 文档失败
```

**解决方案**:

- 检查 OpenAPI 文档格式是否正确
- 使用在线工具验证文档有效性
- 检查文件路径是否正确

#### 3. API 调用超时

```
错误: API 调用超时
```

**解决方案**:

- 检查网络连接
- 验证 API 服务器地址
- 调整超时设置

#### 4. 参数验证失败

```
错误: 参数验证失败
```

**解决方案**:

- 检查参数类型和格式
- 查看 API 文档中的参数要求
- 使用 `--debug` 模式查看详细信息

### 调试模式

启用调试模式可以获得更详细的日志信息：

```bash
python cli.py --debug
```

或者在代码中：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [prance](https://github.com/jfinkhaeuser/prance) - OpenAPI 文档解析
- [OpenAI](https://github.com/openai/openai-python) - Function Calling 支持
- [Pydantic](https://github.com/pydantic/pydantic) - 数据验证
- [Flask](https://github.com/pallets/flask) - Web API 框架

## 📞 联系我们

如有问题或建议，请通过以下方式联系：

- 提交 [Issue](https://github.com/your-repo/swagger-api-agent/issues)
- 发送邮件到: <your-email@example.com>

---

**Swagger API Agent** - 让 API 调用变得智能而简单！ 🚀
