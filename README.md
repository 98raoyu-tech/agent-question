# 企业级 AI 工作流操作系统

基于多智能体架构的企业级 AI 工作流平台，支持 Agent 编排、工作流管理、知识库、可观测性等核心能力。

## 前置要求

- Docker & Docker Compose v2
- Python 3.11+
- Node.js 20+（前端开发）
- Poetry（Python 依赖管理）

## 快速启动

### 1. 克隆项目

```bash
git clone <repository-url>
cd enterprise-ai-workflow-os-multi-agent
```

### 2. 初始化环境

```bash
# 复制环境变量模板
cp .env.example .env

# 安装后端依赖
make init
```

### 3. 启动基础设施

```bash
# 启动 PostgreSQL、Redis、Neo4j、Kafka、Temporal
make up
```

### 4. 启动后端服务

```bash
# 开发模式（热重载）
make dev

# 或使用 Docker 启动
make up-all
```

### 5. 启动前端服务

```bash
cd frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

访问 http://localhost:5173 查看前端界面。

## 常用命令

| 命令 | 说明 |
|------|------|
| `make help` | 显示所有可用命令 |
| `make init` | 初始化项目（安装依赖 + 拷贝环境变量） |
| `make dev` | 启动开发服务器（热重载） |
| `make up` | 启动全部基础设施服务 |
| `make up-all` | 启动全部服务（含应用服务） |
| `make down` | 停止全部服务 |
| `make logs` | 查看全部服务日志 |
| `make test` | 运行全部测试 |
| `make lint` | 运行代码检查 |
| `make format` | 运行代码格式化 |

## 项目结构

```
├── app/                    # 应用入口
├── src/                    # 后端源代码
│   └── ai_workflow_os/     # 核心业务模块
│       ├── agents/         # Agent 实现
│       ├── api/            # API 路由
│       ├── core/           # 核心配置
│       ├── memory/         # 记忆系统
│       ├── observability/  # 可观测性
│       ├── platform/       # 平台功能模块
│       ├── runtime/        # 运行时引擎
│       ├── security/       # 安全模块
│       ├── tools/          # 工具系统
│       └── workflow/       # 工作流引擎
├── frontend/               # 前端源代码
│   ├── src/                # Vue 3 源代码
│   └── dist/               # 构建产物（已忽略）
├── docker-compose.yml      # Docker 编排配置
├── Makefile                # 常用命令集合
├── pyproject.toml          # Python 项目配置
└── .env.example            # 环境变量模板
```

## 环境变量

复制 `.env.example` 为 `.env` 并填写实际配置值：

```bash
cp .env.example .env
```

主要配置项：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接字符串 | `postgresql+asyncpg://postgres:postgres@localhost:5432/ai_workflow_os` |
| `REDIS_URL` | Redis 连接字符串 | `redis://localhost:6379/0` |
| `NEO4J_URI` | Neo4j 连接地址 | `bolt://localhost:7687` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka 服务地址 | `localhost:9092` |
| `TEMPORAL_ADDRESS` | Temporal 服务地址 | `localhost:7233` |
| `JWT_SECRET_KEY` | JWT 密钥 | 需要修改 |
| `FEISHU_APP_ID` | 飞书应用 ID | 需要配置 |
| `FEISHU_APP_SECRET` | 飞书应用密钥 | 需要配置 |

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| 后端 API | 8000 | FastAPI 应用 |
| 前端 | 5173 | Vue 开发服务器 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 |
| Neo4j | 7474/7687 | 图数据库 |
| Kafka | 9092 | 消息队列 |
| Temporal | 7233/8233 | 工作流引擎 |

## 开发指南

### 代码质量检查

```bash
# 运行全部检查
make check

# 单独运行
make lint        # 代码检查
make format      # 代码格式化
make typecheck   # 类型检查
```

### 运行测试

```bash
make test        # 运行测试
make test-cov    # 运行测试并生成覆盖率报告
```

### 数据库操作

```bash
make db-shell    # 连接 PostgreSQL
make redis-cli   # 连接 Redis
make neo4j-shell # 连接 Neo4j
```

## 常见问题

### 1. 端口被占用

检查端口占用情况并停止冲突服务：

```bash
# Windows
netstat -ano | findstr :5432

# Linux/Mac
lsof -i :5432
```

### 2. Docker 容器启动失败

查看日志排查问题：

```bash
make logs
```

### 3. 依赖安装失败

清理缓存后重试：

```bash
make clean
make init
```

## 许可证

[待定]