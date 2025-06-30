# Swagger API Agent Makefile

.PHONY: help install install-dev test lint format clean build upload docs poetry-install poetry-shell poetry-update

help:  ## 显示帮助信息
	@echo "可用命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

poetry-install:  ## 安装 Poetry (如果尚未安装)
	@which poetry > /dev/null || (echo "安装 Poetry..." && curl -sSL https://install.python-poetry.org | python3 -)
	@echo "Poetry 已安装: $$(poetry --version)"

install: poetry-install  ## 安装项目依赖
	poetry install

install-dev: poetry-install  ## 安装开发依赖
	poetry install --with dev,test

poetry-shell:  ## 进入 Poetry 虚拟环境
	poetry shell

poetry-update:  ## 更新依赖
	poetry update

poetry-show:  ## 显示依赖信息
	poetry show

poetry-check:  ## 检查 Poetry 配置
	poetry check

test:  ## 运行测试
	poetry run pytest tests/ -v --cov=swagger_api_agent --cov-report=html --cov-report=term

lint:  ## 代码检查
	poetry run flake8 src/ tests/

type-check:  ## 类型检查
	poetry run mypy src/swagger_api_agent

lint-all: lint type-check  ## 完整的代码检查（包含类型检查）

format:  ## 代码格式化
	poetry run black src/ tests/
	poetry run isort src/ tests/

clean:  ## 清理构建文件
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build:  ## 构建分发包
	poetry build

upload:  ## 上传到 PyPI
	poetry publish

docs:  ## 生成文档
	@echo "文档位于 docs/ 目录"
	@echo "API 文档: http://localhost:5000 (启动 swagger-web-api)"

run-cli:  ## 运行 CLI
	poetry run swagger-api-agent

run-web:  ## 运行 Web API
	poetry run swagger-web-api --host 0.0.0.0 --port 5000

run-mock:  ## 运行 Mock 服务器
	poetry run python scripts/mock_server.py

demo:  ## 运行演示
	@echo "启动 Mock 服务器..."
	poetry run python scripts/mock_server.py &
	@sleep 2
	@echo "运行 CLI 演示..."
	poetry run swagger-api-agent --api-url http://localhost:8080

stop-all:  ## 停止所有服务
	pkill -f "mock_server.py" || true
	pkill -f "swagger-web-api" || true

# 传统 pip 方式的兼容命令 (不推荐)
install-pip:  ## 使用 pip 安装 (兼容性)
	pip install -e .

install-dev-pip:  ## 使用 pip 安装开发依赖 (兼容性)
	pip install -e ".[dev,test]"

test-pip:  ## 使用 pip 环境运行测试 (兼容性)
	python -m pytest tests/ -v --cov=swagger_api_agent --cov-report=html --cov-report=term

lint-pip:  ## 使用 pip 环境进行代码检查 (兼容性)
	python -m flake8 src/ tests/
	python -m mypy src/swagger_api_agent

format-pip:  ## 使用 pip 环境进行代码格式化 (兼容性)
	python -m black src/ tests/
	python -m isort src/ tests/

# Docker 相关命令
docker-build:  ## 构建 Docker 镜像
	./docker.sh build

docker-run-cli:  ## 运行 Docker CLI 模式
	./docker.sh run-cli

docker-run-web:  ## 运行 Docker Web API 模式
	./docker.sh run-web

docker-run-mock:  ## 运行 Docker Mock 服务器
	./docker.sh run-mock

docker-compose-up:  ## 使用 docker-compose 启动所有服务
	./docker.sh compose

docker-compose-down:  ## 停止 docker-compose 服务
	./docker.sh stop

docker-clean:  ## 清理 Docker 资源
	./docker.sh clean

docker-help:  ## 显示 Docker 帮助信息
	./docker.sh help
