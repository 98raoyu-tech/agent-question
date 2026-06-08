# =============================================================================
# 企业级 AI 工作流操作系统 - Makefile 常用命令
# 使用方式：make <command>
# =============================================================================

# 默认 Shell
SHELL := /bin/bash

# 项目配置
APP_NAME := ai-workflow-os
PYTHON := python
POETRY := poetry
DOCKER_COMPOSE := docker compose
UVICORN_HOST := 0.0.0.0
UVICORN_PORT := 8000

# =============================================================================
# 环境初始化
# =============================================================================

.PHONY: help
help: ## 显示所有可用命令
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: init
init: ## 初始化项目（安装依赖 + 拷贝环境变量）
	@echo ">>> 初始化项目环境..."
	@test -f .env || cp .env.example .env
	@echo ">>> 已生成 .env 文件，请填写实际配置值"
	$(POETRY) install
	@echo ">>> 项目初始化完成"

.PHONY: install
install: ## 安装项目依赖
	$(POETRY) install

.PHONY: install-dev
install-dev: ## 安装包含开发依赖的完整依赖
	$(POETRY) install --with dev

# =============================================================================
# 开发运行
# =============================================================================

.PHONY: dev
dev: ## 启动开发服务器（热重载）
	$(POETRY) run uvicorn app.main:app \
		--host $(UVICORN_HOST) \
		--port $(UVICORN_PORT) \
		--reload

.PHONY: dev-debug
dev-debug: ## 启动调试模式开发服务器
	$(POETRY) run uvicorn app.main:app \
		--host $(UVICORN_HOST) \
		--port $(UVICORN_PORT) \
		--reload \
		--log-level debug

.PHONY: run
run: ## 启动生产服务器
	$(POETRY) run uvicorn app.main:app \
		--host $(UVICORN_HOST) \
		--port $(UVICORN_PORT) \
		--workers 4

# =============================================================================
# 代码质量
# =============================================================================

.PHONY: lint
lint: ## 运行 Ruff 代码检查
	$(POETRY) run ruff check src/ app/ tests/

.PHONY: format
format: ## 运行 Ruff 代码格式化
	$(POETRY) run ruff format src/ app/ tests/

.PHONY: format-check
format-check: ## 检查代码格式是否符合规范
	$(POETRY) run ruff format --check src/ app/ tests/

.PHONY: typecheck
typecheck: ## 运行 MyPy 类型检查
	$(POETRY) run mypy src/ app/

.PHONY: check
check: lint format-check typecheck ## 运行全部代码质量检查（lint + 格式检查 + 类型检查）

# =============================================================================
# 测试
# =============================================================================

.PHONY: test
test: ## 运行全部测试
	$(POETRY) run pytest tests/ -v

.PHONY: test-cov
test-cov: ## 运行测试并生成覆盖率报告
	$(POETRY) run pytest tests/ -v --cov=src --cov-report=html --cov-report=term

.PHONY: test-watch
test-watch: ## 运行测试（监听文件变化自动重跑）
	$(POETRY) run pytest-watch tests/ -v

# =============================================================================
# Docker 基础设施
# =============================================================================

.PHONY: up
up: ## 启动全部基础设施服务（后台运行）
	$(DOCKER_COMPOSE) up -d

.PHONY: up-all
up-all: ## 启动全部服务（含应用服务）
	$(DOCKER_COMPOSE) --profile all up -d --build

.PHONY: down
down: ## 停止全部服务
	$(DOCKER_COMPOSE) down

.PHONY: down-volumes
down-volumes: ## 停止全部服务并删除数据卷（⚠️ 会清除所有数据）
	$(DOCKER_COMPOSE) down -v
	@echo ">>> 警告：所有持久化数据已删除"

.PHONY: build
build: ## 构建应用镜像
	$(DOCKER_COMPOSE) build --no-cache app

.PHONY: logs
logs: ## 查看全部服务日志
	$(DOCKER_COMPOSE) logs -f

.PHONY: logs-app
logs-app: ## 查看应用服务日志
	$(DOCKER_COMPOSE) logs -f app

.PHONY: ps
ps: ## 查看服务运行状态
	$(DOCKER_COMPOSE) ps

.PHONY: restart
restart: ## 重启全部服务
	$(DOCKER_COMPOSE) restart

# =============================================================================
# Temporal 工作流
# =============================================================================

.PHONY: temporal-setup
temporal-setup: ## 初始化 Temporal 命名空间
	$(DOCKER_COMPOSE) exec temporal-admin-tools \
		tctl namespace register default || true
	@echo ">>> Temporal 命名空间初始化完成"

.PHONY: temporal-list
temporal-list: ## 列出 Temporal 工作流
	$(DOCKER_COMPOSE) exec temporal-admin-tools \
		tctl workflow list

# =============================================================================
# 数据库
# =============================================================================

.PHONY: db-shell
db-shell: ## 连接 PostgreSQL 数据库终端
	$(DOCKER_COMPOSE) exec postgres psql -U postgres -d ai_workflow_os

.PHONY: redis-cli
redis-cli: ## 连接 Redis 终端
	$(DOCKER_COMPOSE) exec redis redis-cli

.PHONY: neo4j-shell
neo4j-shell: ## 连接 Neo4j Cypher Shell
	$(DOCKER_COMPOSE) exec neo4j cypher-shell -u neo4j -p neo4j_password

# =============================================================================
# 清理
# =============================================================================

.PHONY: clean
clean: ## 清理项目临时文件和缓存
	@echo ">>> 清理 Python 缓存..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .mypy_cache .pytest_cache .ruff_cache htmlcov .coverage
	@echo ">>> 清理完成"

.PHONY: clean-all
clean-all: clean down-volumes ## 清理全部（临时文件 + Docker 数据卷）
	@echo ">>> 全部清理完成"
