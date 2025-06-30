# 项目重构迁移指南

## 概述

Swagger API Agent 项目已经从平铺式结构重构为标准的 Python 包结构。这个迁移指南将帮助您了解变化并更新您的使用方式。

## 主要变化

### 1. 目录结构变化

**之前 (平铺式)**:
```
swagger-api-agent/
├── swagger_api_agent.py      # 主类
├── api_caller.py             # API 调用器
├── cli.py                    # CLI
├── config.py                 # 配置
├── llm_client.py             # LLM 客户端
├── openapi_parser.py         # OpenAPI 解析器
├── web_api.py                # Web API
├── example_openapi.yaml      # 示例文档
├── mock_server.py            # Mock 服务器
└── requirements.txt          # 依赖
```

**现在 (标准包结构)**:
```
swagger-api-agent/
├── src/swagger_api_agent/    # 源代码包
│   ├── __init__.py           # 包初始化
│   ├── agent.py              # 主类 (重命名)
│   ├── api_caller.py         # API 调用器
│   ├── cli.py                # CLI
│   ├── config.py             # 配置
│   ├── llm_client.py         # LLM 客户端
│   ├── openapi_parser.py     # OpenAPI 解析器
│   └── web_api.py            # Web API
├── examples/                 # 示例文件
│   └── example_openapi.yaml  # 示例文档
├── scripts/                  # 脚本文件
│   └── mock_server.py        # Mock 服务器
├── tests/                    # 测试文件
├── docs/                     # 文档
├── swagger-api-agent         # CLI 入口
├── swagger-web-api          # Web API 入口
├── pyproject.toml           # 现代项目配置
└── setup.py                 # 安装脚本
```

### 2. 导入方式变化

**之前**:
```python
# 直接导入
from swagger_api_agent import SwaggerAPIAgent

# 运行 CLI
python cli.py

# 运行 Web API  
python web_api.py
```

**现在**:
```python
# 包导入 (推荐)
from swagger_api_agent import SwaggerAPIAgent

# 或者
import swagger_api_agent
agent = swagger_api_agent.SwaggerAPIAgent()

# 运行 CLI
./swagger-api-agent
# 或 python swagger-api-agent

# 运行 Web API
./swagger-web-api  
# 或 python swagger-web-api
```

### 3. 安装方式变化

**之前**:
```bash
# 只能从源码运行
git clone <repo>
cd swagger-api-agent
pip install -r requirements.txt
python cli.py
```

**现在**:
```bash
# 方式 1: 从源码安装 (推荐)
git clone <repo>
cd swagger-api-agent
pip install -e .

# 方式 2: 将来可以从 PyPI 安装
pip install swagger-api-agent

# 方式 3: 开发模式安装
pip install -e ".[dev]"
```

### 4. 配置文件路径变化

**之前**:
```python
# config.py
OPENAPI_FILE = "example_openapi.yaml"
```

**现在**:
```python
# src/swagger_api_agent/config.py  
DEFAULT_OPENAPI_FILE = "examples/example_openapi.yaml"
```

## 迁移步骤

### 1. 更新环境

如果您之前克隆了项目：

```bash
cd swagger-api-agent
git pull origin main  # 获取最新代码

# 重新安装
pip install -e .
```

### 2. 更新脚本

如果您有自定义脚本使用了旧的导入方式：

**更新前**:
```python
# 可能需要添加路径
import sys
sys.path.append('/path/to/swagger-api-agent')
from swagger_api_agent import SwaggerAPIAgent
```

**更新后**:
```python
# 直接导入 (如果已安装)
from swagger_api_agent import SwaggerAPIAgent
```

### 3. 更新 OpenAPI 文档路径

**更新前**:
```bash
python cli.py --openapi example_openapi.yaml
```

**更新后**:
```bash
swagger-api-agent --openapi examples/example_openapi.yaml
```

### 4. 更新环境变量

如果您使用了环境变量，请检查 `.env` 文件：

```env
# 更新 OpenAPI 文件路径
OPENAPI_FILE=examples/example_openapi.yaml

# 其他配置保持不变
API_BASE_URL=http://localhost:8080
DEEPSEEK_API_KEY=your_key_here
```

## 新功能

重构后，您可以享受以下新功能：

### 1. 标准入口点

```bash
# 全局可用的命令 (安装后)
swagger-api-agent --help
swagger-web-api --help
```

### 2. Make 任务

```bash
make help          # 显示所有可用命令
make install-dev   # 安装开发依赖
make test          # 运行测试
make format        # 代码格式化
make lint          # 代码检查
```

### 3. 包分发

```bash
make build         # 构建分发包
```

### 4. 更好的项目结构

- 清晰的关注点分离
- 标准的测试结构
- 完整的文档组织
- 现代化的配置管理

## 故障排除

### 问题 1: 导入错误

**错误**: `ModuleNotFoundError: No module named 'swagger_api_agent'`

**解决**: 
```bash
pip install -e .
```

### 问题 2: OpenAPI 文件未找到

**错误**: `OpenAPI 文档文件不存在: example_openapi.yaml`

**解决**:
```bash
# 使用正确的路径
swagger-api-agent --openapi examples/example_openapi.yaml

# 或设置环境变量
export OPENAPI_FILE=examples/example_openapi.yaml
```

### 问题 3: CLI 命令未找到

**错误**: `swagger-api-agent: command not found`

**解决**:
```bash
# 确保已安装项目
pip install -e .

# 或直接使用 Python 模块
python swagger-api-agent
```

## 兼容性

- ✅ 所有原有功能保持兼容
- ✅ 配置选项保持不变  
- ✅ API 接口保持一致
- ✅ 支持 Python 3.8+

## 获得帮助

如果您在迁移过程中遇到问题：

1. 查看 [项目文档](docs/)
2. 运行 `make help` 查看可用命令
3. 使用 `--help` 参数查看命令帮助
4. 检查 [示例文件](examples/)

新的项目结构将为项目的长期维护和发展提供更好的基础。
