# 项目架构概览

## 项目结构说明

Swagger API Agent 现在采用标准的 Python 项目结构，符合 PEP 518 和现代 Python 开发规范。

### 目录结构

```
swagger-api-agent/
├── src/swagger_api_agent/     # 主要源代码包
│   ├── __init__.py           # 包初始化，导出主要接口
│   ├── agent.py              # 核心 Agent 类，整合所有功能
│   ├── api_caller.py         # API 调用器，负责 HTTP 请求
│   ├── cli.py                # 命令行界面实现
│   ├── config.py             # 配置管理和环境变量
│   ├── llm_client.py         # 大语言模型客户端
│   ├── openapi_parser.py     # OpenAPI 文档解析器
│   └── web_api.py            # Flask Web API 服务
├── tests/                    # 测试代码
│   ├── conftest.py          # 测试配置和夹具
│   ├── test_agent.py        # Agent 核心功能测试
│   └── test_config.py       # 配置模块测试
├── examples/                 # 示例和演示
│   └── example_openapi.yaml  # 示例 OpenAPI 文档
├── scripts/                  # 实用脚本
│   ├── mock_server.py        # Mock API 服务器
│   └── *.sh                  # Shell 脚本
├── docs/                     # 项目文档
│   └── mock-server.md        # Mock 服务器文档
├── swagger-api-agent         # CLI 入口脚本
├── swagger-web-api          # Web API 入口脚本
├── pyproject.toml           # Poetry 项目配置和依赖管理
├── setup.py                 # 向后兼容的安装脚本
├── Makefile                 # 开发任务自动化
├── MANIFEST.in              # 包文件清单
└── README.md                # 项目说明
```

## 核心组件说明

### 1. Agent (agent.py)

- 主要的协调类，整合所有功能
- 管理对话历史和状态
- 提供统一的接口调用入口

### 2. OpenAPI Parser (openapi_parser.py)  

- 解析 OpenAPI/Swagger 文档
- 生成函数模式 (Function Schemas)
- 验证参数类型和约束

### 3. LLM Client (llm_client.py)

- DeepSeek API 客户端
- Function Calling 支持
- 自然语言理解和处理

### 4. API Caller (api_caller.py)

- HTTP 请求封装
- 认证处理
- 错误处理和重试

### 5. CLI (cli.py)

- 命令行界面
- 交互模式和直接调用模式
- 彩色输出和用户友好界面

### 6. Web API (web_api.py)

- Flask REST API 服务
- JWT 认证保护
- 支持用户登录和token验证
- JSON 格式的请求和响应

## 认证系统

项目采用 JWT (JSON Web Token) 认证机制：

### 后端认证
- 用户名密码配置在 `config.py` 中
- `/api/login` 端点用于用户登录，返回JWT token
- 所有API端点（除了 `/health` 和 `/api/login`）都需要JWT认证
- Token 默认有效期为24小时

### 前端认证
- 登录页面收集用户凭据
- 自动存储JWT token到localStorage
- 所有API请求自动添加Authorization头
- Token过期时自动跳转到登录页面

## 配置管理

配置采用环境变量优先的策略：

1. 环境变量 (.env 文件)
2. 命令行参数
3. 默认配置值

主要配置项：

- `DEEPSEEK_API_KEY`: DeepSeek API 密钥
- `OPENAPI_FILE`: OpenAPI 文档路径
- `API_BASE_URL`: 目标 API 基础 URL
- `REQUIRE_USER_CONFIRMATION`: 是否需要用户确认
- `SHOW_API_CALL_DETAILS`: 是否显示调用详情
- `WEB_API_USERNAME`: Web界面登录用户名 (默认: admin)
- `WEB_API_PASSWORD`: Web界面登录密码 (默认: admin123)
- `JWT_SECRET_KEY`: JWT签名密钥
- `JWT_EXPIRATION_HOURS`: JWT过期时间（小时，默认: 24）

## 入口点

### CLI 入口

```bash
./swagger-api-agent
# 或
python -m swagger_api_agent.cli
```

### Web API 入口  

```bash
./swagger-web-api
# 或
python -m swagger_api_agent.web_api
```

### 程序化使用

```python
from swagger_api_agent import SwaggerAPIAgent
agent = SwaggerAPIAgent()
```

## 开发工作流

1. **安装开发依赖**: `make install-dev`
2. **代码格式化**: `make format`
3. **代码检查**: `make lint`
4. **运行测试**: `make test`
5. **构建包**: `make build`

## 部署方式

### 开发部署

```bash
pip install -e .
```

### 生产部署

```bash
pip install swagger-api-agent
```

### Docker 部署

```dockerfile
FROM python:3.10-slim
COPY . /app
WORKDIR /app
RUN pip install .
CMD ["swagger-web-api", "--host", "0.0.0.0"]
```

这个新的项目结构提供了：

- ✅ 标准的 Python 包结构
- ✅ 清晰的关注点分离
- ✅ 易于测试和维护
- ✅ 支持现代 Python 工具链
- ✅ 便于分发和部署
