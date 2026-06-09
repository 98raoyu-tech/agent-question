# Q01 企业知识库系统的完整架构设计

## 🎤 30秒回答版

这道题考察核心概念，建议先明确定义和核心原理。

## 🎤 1分钟回答版

这道题需要掌握基本概念、核心原理和典型应用场景，建议从定义入手，说明原理和实际应用。

## 🎤 3分钟深度回答版

这道题适合深入分析，建议从定义、原理、架构、实践、优缺点和优化方案六个维度展开。

## 📈 面试等级

P6-P7

**原因**：核心技术，中级到高级工程师需掌握

## 🔥 面试追问链

基础概念？

↓

核心原理？

↓

实现方式？

↓

优缺点？

↓

企业落地？

## 🏢 企业真实案例

**企业**：某企业

**为什么采用**：业务需求驱动

**解决什么问题**：原有方案无法满足需求

**收益是什么**：效率提升，成本降低

## 🎯 适用岗位

- AI应用开发工程师
- Agent工程师
- RAG工程师
- Workflow工程师
- AI平台工程师
- AI架构师


## Q02 SQL Agent 的架构设计

### 题目背景

> **面试原题**：请设计一个SQL Agent系统，能够将自然语言转换为SQL查询，支持多轮对话、错误自动修正，并保证生产环境的安全性和可靠性。

### 1. Text-to-SQL 技术方案

#### 1.1 技术路线对比

```
┌───────────────────────────────────────────────────────────┐
│                 Text-to-SQL 技术演进                        │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│  阶段        │ 方法         │ 准确率      │ 适用场景         │
├─────────────┼─────────────┼─────────────┼─────────────────┤
│ 传统NLP      │ 模板匹配     │ 30-40%     │ 固定模式查询     │
│ Seq2Seq     │ SQLNet等    │ 50-60%     │ 单表简单查询     │
│ LLM直接生成  │ Prompt工程   │ 65-75%     │ 中等复杂度       │
│ LLM+Agent   │ 多步推理     │ 80-90%     │ 复杂多表关联     │
│ 微调+RAG    │ 领域适配     │ 85-95%     │ 企业专有数据库   │
└─────────────┴─────────────┴─────────────┴─────────────────┘
```

#### 1.2 生产级方案架构

```python
class SQLAgent:
    """SQL Agent 核心架构"""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
        self.schema_linker = SchemaLinker(db_connection)
        self.sql_generator = SQLGenerator()
        self.sql_validator = SQLValidator()
        self.sql_executor = SQLExecutor(db_connection)
        self.error_corrector = ErrorCorrector()
        self.result_formatter = ResultFormatter()

    async def query(self, question: str, context: ConversationContext) -> Answer:
        """自然语言查询主流程"""

        # Step 1: Schema Linking - 识别相关表和列
        schema_context = await self.schema_linker.link(
            question=question,
            history=context.history,
            top_k_tables=5,
        )

        # Step 2: SQL生成 - 多步推理
        sql_result = await self.sql_generator.generate(
            question=question,
            schema=schema_context,
            dialect=self.db.dialect,       # MySQL/PostgreSQL/ClickHouse
            examples=self.get_few_shot_examples(question),
        )

        # Step 3: SQL验证 - 语法检查 + 安全检查
        validation = self.sql_validator.validate(sql_result.sql)
        if not validation.is_valid:
            sql_result = await self.error_corrector.correct(
                sql=sql_result.sql,
                error=validation.error,
                schema=schema_context,
            )

        # Step 4: 执行 + 错误重试
        for attempt in range(3):
            try:
                exec_result = await self.sql_executor.execute(
                    sql=sql_result.sql,
                    timeout=30,
                    max_rows=1000,
                )
                break
            except SQLError as e:
                if attempt == 2:
                    raise
                sql_result = await self.error_corrector.correct(
                    sql=sql_result.sql,
                    error=str(e),
                    schema=schema_context,
                )

        # Step 5: 结果解读 - 用自然语言描述查询结果
        answer = await self.result_formatter.format(
            question=question,
            sql=sql_result.sql,
            result=exec_result,
        )

        return answer
```

### 2. Schema Linking 和数据库理解

#### 2.1 Schema Linking 策略

Schema Linking 是 Text-to-SQL 的关键环节，目标是从自然语言问题中识别出相关的数据库表和列。

```
用户问题："上个月销售额最高的前10个产品是什么？"

Schema Linking 过程：
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  实体识别     │     │  关系匹配     │     │  Schema裁剪  │
│              │     │              │     │              │
│ "销售额"     │────▶│ orders表     │────▶│ orders       │
│ "产品"       │     │ products表   │     │ products     │
│ "上个月"     │     │ 时间字段      │     │ (裁剪其他表) │
│ "前10"       │     │ 聚合函数      │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
```

```python
class SchemaLinker:
    """Schema Linking 引擎"""

    def __init__(self, db_connection):
        self.db = db_connection
        self.schema_cache = {}  # Schema元数据缓存
        self.column_index = None  # 列名向量索引

    async def initialize(self):
        """初始化 - 加载并索引数据库Schema"""
        schema = await self.db.get_full_schema()
        self.schema_cache = schema

        # 为所有列名创建向量索引（用于语义匹配）
        column_descriptions = []
        for table in schema.tables:
            for column in table.columns:
                desc = f"{table.name}.{column.name}: {column.comment or column.name}"
                column_descriptions.append(desc)

        embeddings = await embed_batch(column_descriptions)
        self.column_index = VectorIndex(embeddings, column_descriptions)

    async def link(self, question: str, history: list, top_k_tables: int = 5):
        """链接问题到相关表和列"""
        # 1. 向量检索相关列
        question_embedding = await embed(question)
        matched_columns = self.column_index.search(question_embedding, top_k=20)

        # 2. 提取相关表
        related_tables = set()
        for col_match in matched_columns:
            table_name = col_match.split(".")[0]
            related_tables.add(table_name)

        # 3. 补充关联表（外键关系）
        extended_tables = set(related_tables)
        for table in related_tables:
            for fk in self.schema_cache.get_foreign_keys(table):
                extended_tables.add(fk.referenced_table)

        # 4. 构建裁剪后的Schema上下文
        selected_tables = list(extended_tables)[:top_k_tables]
        schema_context = self.build_schema_context(selected_tables)

        return SchemaContext(
            tables=schema_context,
            matched_columns=matched_columns,
            confidence=self.calculate_confidence(matched_columns, question),
        )

    def build_schema_context(self, tables: list) -> str:
        """构建Schema描述文本"""
        parts = []
        for table in tables:
            t = self.schema_cache.get_table(table)
            ddl = f"CREATE TABLE {t.name} (\n"
            for col in t.columns:
                ddl += f"  {col.name} {col.type}"
                if col.comment:
                    ddl += f"  -- {col.comment}"
                ddl += ",\n"
            # 添加外键关系
            for fk in t.foreign_keys:
                ddl += f"  -- FK: {fk.columns} → {fk.referenced_table}.{fk.referenced_columns}\n"
            ddl += ");\n"
            # 添加示例数据
            ddl += f"-- 示例数据: {t.sample_rows}\n"
            parts.append(ddl)
        return "\n".join(parts)
```

#### 2.2 Few-Shot 示例管理

```python
class FewShotExampleManager:
    """Few-Shot示例管理器 - 动态选择最相关的示例"""

    def __init__(self):
        self.examples = []  # 预定义的示例库
        self.example_index = None

    async def initialize(self, examples_path: str):
        """加载示例库并建立索引"""
        self.examples = load_yaml(examples_path)
        descriptions = [ex["question"] for ex in self.examples]
        embeddings = await embed_batch(descriptions)
        self.example_index = VectorIndex(embeddings, self.examples)

    async def select(self, question: str, top_k: int = 5) -> list:
        """动态选择与当前问题最相关的示例"""
        question_embedding = await embed(question)
        similar = self.example_index.search(question_embedding, top_k=top_k)
        return [
            {
                "question": ex["question"],
                "sql": ex["sql"],
                "explanation": ex.get("explanation", ""),
            }
            for ex in similar
        ]
```

### 3. 多轮查询与错误修正

#### 3.1 多轮对话上下文管理

```python
class ConversationContext:
    """多轮SQL对话上下文管理"""

    def __init__(self, max_history: int = 10):
        self.history = []
        self.max_history = max_history
        self.referenced_entities = {}  # 跟踪引用的实体

    def add_turn(self, question: str, sql: str, result: Any):
        """添加一轮对话"""
        self.history.append({
            "question": question,
            "sql": sql,
            "result_summary": self._summarize_result(result),
            "timestamp": datetime.now(),
        })
        # 保持历史窗口
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        # 提取并缓存实体引用
        self._extract_entity_references(question, sql)

    def resolve_references(self, question: str) -> str:
        """解析指代和省略"""
        # "再按地区分组" → "将上一条SQL的结果按地区分组"
        # "把时间范围改成今年" → 修改上一条SQL的时间条件
        resolved = question
        for entity, value in self.referenced_entities.items():
            if entity in resolved:
                resolved = resolved.replace(entity, value)
        return resolved
```

#### 3.2 错误自动修正机制

```
SQL执行错误修正流程：

┌──────────────┐
│  SQL执行失败  │
└──────┬───────┘
       │
       ▼
┌──────────────┐    语法错误    ┌────────────────────┐
│  错误分类     │──────────────▶│  LLM修正语法       │
│              │              │  (提供错误信息+DDL)  │
│              │  类型错误     ┌────────────────────┐
│              │──────────────▶│  类型转换/CAST修正  │
│              │              └────────────────────┘
│              │  列名/表名错误 ┌────────────────────┐
│              │──────────────▶│  模糊匹配修正       │
│              │              │  (编辑距离+语义)     │
│              │  空结果       ┌────────────────────┐
│              │──────────────▶│  放宽条件/检查数据  │
└──────────────┘              └────────────────────┘
       │
       ▼
┌──────────────┐
│  重新执行验证  │──── 成功 → 返回结果
│              │──── 失败 → 人工兜底
└──────────────┘
```

### 4. 安全性设计

#### 4.1 SQL注入防护

```python
class SQLValidator:
    """SQL安全验证器"""

    DANGEROUS_KEYWORDS = [
        "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE",
        "INSERT", "UPDATE", "GRANT", "REVOKE", "EXEC",
    ]

    def validate(self, sql: str) -> ValidationResult:
        """多层安全验证"""
        # 1. 解析SQL AST
        ast = sqlparse.parse(sql)

        # 2. 检查语句类型 - 只允许SELECT
        for statement in ast:
            if statement.get_type() != "SELECT":
                return ValidationResult(
                    is_valid=False,
                    error=f"禁止非SELECT语句: {statement.get_type()}",
                )

        # 3. 检查危险关键词
        sql_upper = sql.upper()
        for keyword in self.DANGEROUS_KEYWORDS:
            if keyword in sql_upper:
                return ValidationResult(
                    is_valid=False,
                    error=f"包含危险关键词: {keyword}",
                )

        # 4. 检查子查询深度（防止无限嵌套）
        nesting_depth = self._check_nesting_depth(sql)
        if nesting_depth > 3:
            return ValidationResult(
                is_valid=False,
                error=f"子查询嵌套过深: {nesting_depth}层",
            )

        # 5. 检查是否访问授权表
        tables = self._extract_tables(sql)
        unauthorized = self._check_table_access(tables)
        if unauthorized:
            return ValidationResult(
                is_valid=False,
                error=f"无权访问表: {unauthorized}",
            )

        return ValidationResult(is_valid=True)
```

#### 4.2 权限控制体系

```
权限控制四层模型：

Layer 1: 用户身份认证
    └── SSO / OAuth2 / API Key

Layer 2: 数据库连接隔离
    └── 每个用户组使用不同的数据库账号
    └── 只读权限，限制查询资源（CPU/内存/时间）

Layer 3: 表级权限控制
    └── 用户 → 角色 → 可访问表列表
    └── 敏感表（如salary）需额外审批

Layer 4: 行级权限控制
    └── 自动追加WHERE条件
    └── 如：AND department_id IN (用户可见部门列表)
```

### 5. 生产环境最佳实践

#### 5.1 查询优化

```python
class QueryOptimizer:
    """生产环境查询优化器"""

    def optimize(self, sql: str, db_type: str) -> str:
        """SQL执行前优化"""
        # 1. 强制添加LIMIT（防止全表扫描返回）
        if "LIMIT" not in sql.upper():
            sql = f"{sql.rstrip(';')} LIMIT 1000"

        # 2. EXPLAIN预检查
        explain_result = self.db.explain(sql)
        if self._is_full_table_scan(explain_result):
            # 提示LLM添加索引条件或优化查询
            raise QueryOptimizationError("查询可能触发全表扫描，请优化")

        # 3. 设置查询超时
        sql = f"SET statement_timeout = '30s'; {sql}"

        # 4. 添加只读事务
        sql = f"BEGIN READ ONLY; {sql}; COMMIT;"

        return sql
```

#### 5.2 可观测性设计

```
SQL Agent 监控指标：

┌──────────────┬────────────────────┬────────────┐
│  指标类别     │  具体指标           │  告警阈值   │
├──────────────┼────────────────────┼────────────┤
│  准确性       │ SQL一次通过率       │ < 70%      │
│              │ 修正后通过率         │ < 90%      │
│              │ 结果准确率(人工评估)  │ < 85%      │
├──────────────┼────────────────────┼────────────┤
│  性能         │ Text-to-SQL延迟    │ > 5s       │
│              │ SQL执行延迟         │ > 30s      │
│              │ 端到端延迟          │ > 10s      │
├──────────────┼────────────────────┼────────────┤
│  安全         │ SQL注入拦截次数     │ 持续监控   │
│              │ 无权限访问尝试       │ > 0 告警   │
└──────────────┴────────────────────┴────────────┘
```

### 6. 面试加分点

- **多数据库方言支持**：同一Agent适配MySQL/PostgreSQL/ClickHouse等不同SQL方言
- **查询缓存**：相同语义查询复用已生成的SQL（语义哈希匹配）
- **渐进式返回**：先返回SQL和简要说明，异步执行后推送结果
- **自我反思机制**：Agent在生成SQL后自行审查，检查是否遗漏条件

---

## Q03 客服Agent的完整系统设计

### 题目背景

> **面试原题**：请设计一个智能客服Agent系统，支持多轮对话、意图识别、知识库检索和人机协作，能够处理售前咨询、售后服务、投诉处理等多种场景。

### 1. 多轮对话管理

#### 1.1 对话状态机设计

```
                    ┌───────────┐
                    │  对话开始   │
                    └─────┬─────┘
                          │
                          ▼
                   ┌─────────────┐
              ┌────│  意图识别    │────┐
              │    └─────────────┘    │
              │                       │
         ┌────▼────┐           ┌─────▼─────┐
         │ 售前咨询  │           │  售后服务   │
         └────┬────┘           └─────┬─────┘
              │                       │
         ┌────▼────┐           ┌─────▼─────┐
         │ 产品介绍  │           │  问题诊断   │
         └────┬────┘           └─────┬─────┘
              │                       │
         ┌────▼────┐           ┌─────▼─────┐
         │ 方案推荐  │           │  解决方案   │
         └────┬────┘           └─────┬─────┘
              │                       │
              └───────────┬───────────┘
                          │
                   ┌──────▼──────┐
              ┌────│  满意度评估  │────┐
              │    └─────────────┘    │
              │                       │
         ┌────▼────┐           ┌─────▼─────┐
         │ 继续服务  │           │  对话结束   │
         └─────────┘           └───────────┘
```

#### 1.2 对话上下文管理器

```python
class DialogueContextManager:
    """对话上下文管理器 - 维护完整对话状态"""

    def __init__(self):
        self.sessions: Dict[str, DialogueSession] = {}

    def get_or_create_session(self, session_id: str, user_id: str) -> DialogueSession:
        if session_id not in self.sessions:
            self.sessions[session_id] = DialogueSession(
                session_id=session_id,
                user_id=user_id,
                created_at=datetime.now(),
            )
        return self.sessions[session_id]

    def get_context_window(self, session_id: str, max_turns: int = 10) -> list:
        """获取滑动窗口内的对话历史"""
        session = self.sessions.get(session_id)
        if not session:
            return []

        history = session.history[-max_turns:]
        # 压缩早期对话为摘要
        if len(session.history) > max_turns:
            summary = session.get_early_summary()
            return [{"role": "system", "content": f"之前的对话摘要：{summary}"}] + history
        return history


class DialogueSession:
    """单次对话会话"""

    def __init__(self, session_id: str, user_id: str, created_at: datetime):
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = created_at
        self.history = []
        self.state = DialogueState.INIT
        self.intent = None
        self.entities = {}  # 提取的实体
        self.sentiment = None  # 情感倾向
        self.turn_count = 0
        self.metadata = {}

    def add_turn(self, role: str, content: str, metadata: dict = None):
        """添加对话轮次"""
        self.turn_count += 1
        self.history.append({
            "role": role,
            "content": content,
            "turn_id": self.turn_count,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        })

    def get_early_summary(self) -> str:
        """生成早期对话的摘要"""
        early_history = self.history[:-10]
        if not early_history:
            return ""
        # 使用LLM生成摘要（异步预计算缓存）
        return self._cached_summary or self._generate_summary(early_history)
```

### 2. 意图识别与路由

#### 2.1 多层意图识别架构

```python
class IntentRouter:
    """意图识别与路由引擎"""

    # 意图层级定义
    INTENT_TREE = {
        "售前": {
            "产品咨询": ["功能介绍", "价格咨询", "对比分析"],
            "方案推荐": ["需求分析", "方案匹配", "报价生成"],
            "试用申请": ["开通试用", "试用指导"],
        },
        "售后": {
            "技术支持": ["使用指导", "故障排查", "Bug反馈"],
            "订单服务": ["订单查询", "退换货", "发票"],
            "投诉建议": ["投诉受理", "建议收集"],
        },
    }

    async def route(self, message: str, context: DialogueContext) -> RouteResult:
        """意图路由"""
        # Layer 1: 规则匹配（快速路径，处理确定性意图）
        rule_result = self.rule_match(message)
        if rule_result.confidence > 0.95:
            return rule_result

        # Layer 2: 分类模型（轻量级，处理常见意图）
        model_result = await self.classifier.classify(
            text=message,
            context=context.get_context_window(max_turns=3),
            labels=list(self.INTENT_TREE.keys()),
        )
        if model_result.confidence > 0.85:
            # 进一步细分
            sub_intent = await self.classifier.classify(
                text=message,
                labels=list(self.INTENT_TREE[model_result.label].keys()),
            )
            return RouteResult(
                intent=model_result.label,
                sub_intent=sub_intent.label,
                confidence=min(model_result.confidence, sub_intent.confidence),
            )

        # Layer 3: LLM推理（兜底，处理复杂/模糊意图）
        llm_result = await self.llm_router.classify(
            message=message,
            context=context.get_context_window(),
            intent_tree=self.INTENT_TREE,
        )
        return llm_result
```

#### 2.2 意图识别优化策略

```
意图识别准确率提升策略：

1. 意图消歧
   问题："我想退" → 退货？退款？退出登录？
   方案：结合上下文 + 追问确认

2. 多意图处理
   问题："产品怎么用？另外我想退货"
   方案：意图拆分 → 分别处理 → 合并回复

3. 意图切换检测
   场景：用户从"产品咨询"突然切换到"投诉"
   方案：实时情感分析 + 话题切换检测

4. 拒识处理
   问题：超出客服范围的输入
   方案：置信度阈值 + 兜底话术 + 转人工
```

### 3. 知识库检索 + LLM生成

#### 3.1 客服知识库设计

```
客服知识库分层结构：

┌────────────────────────────────────────────────┐
│  L1: FAQ知识库（结构化）                         │
│  ├── 问题-答案对，精确匹配                       │
│  ├── 覆盖率：60-70%的常见问题                    │
│  └── 响应时间：< 100ms                          │
├────────────────────────────────────────────────┤
│  L2: 产品知识库（半结构化）                       │
│  ├── 产品手册、功能文档、操作指南                  │
│  ├── RAG检索 + LLM生成                          │
│  └── 覆盖率：20-25%的专业问题                    │
├────────────────────────────────────────────────┤
│  L3: 工单知识库（非结构化）                       │
│  ├── 历史工单、解决方案记录                       │
│  ├── 相似工单推荐                               │
│  └── 覆盖率：5-10%的复杂问题                     │
└────────────────────────────────────────────────┘
```

```python
class CustomerServiceRetriever:
    """客服专用检索引擎"""

    async def retrieve(self, query: str, intent: str, context: DialogueContext):
        """分层检索"""
        # L1: FAQ精确匹配
        faq_result = await self.faq_store.match(query, threshold=0.9)
        if faq_result:
            return RetrievalResult(source="faq", content=faq_result, confidence=0.95)

        # L2: 产品知识库RAG检索
        # 根据意图调整检索策略
        retrieval_config = self.get_intent_config(intent)
        rag_result = await self.rag_retriever.retrieve(
            query=query,
            collection=retrieval_config.knowledge_base,
            top_k=retrieval_config.top_k,
        )

        # L3: 相似工单推荐
        similar_tickets = await self.ticket_store.find_similar(
            query=query,
            status="resolved",
            limit=3,
        )

        return RetrievalResult(
            source="rag",
            content=rag_result,
            similar_tickets=similar_tickets,
            confidence=rag_result.score,
        )
```

### 4. 人机协作（Human-in-the-Loop）

#### 4.1 转人工触发机制

```python
class HumanHandoffManager:
    """人机协作管理器"""

    # 转人工触发条件
    TRANSFER_TRIGGERS = {
        "explicit_request": {
            "keywords": ["转人工", "人工客服", "找人"],
            "auto_transfer": True,
        },
        "sentiment_negative": {
            "threshold": -0.7,           # 情感得分阈值
            "consecutive_turns": 2,       # 连续负面轮次
            "auto_transfer": False,       # 需确认
        },
        "intent_out_of_scope": {
            "confidence_threshold": 0.3,  # 意图置信度低于阈值
            "auto_transfer": False,
        },
        "repeated_failure": {
            "max_no_answer": 3,           # 连续无法回答次数
            "auto_transfer": True,
        },
        "high_value_customer": {
            "vip_levels": ["SVIP", "VIP3"],
            "auto_transfer": False,       # 提供VIP通道选项
        },
    }

    async def should_transfer(self, session: DialogueSession) -> TransferDecision:
        """判断是否需要转人工"""
        for trigger_name, config in self.TRANSFER_TRIGGERS.items():
            if self._check_trigger(session, trigger_name, config):
                return TransferDecision(
                    should_transfer=True,
                    reason=trigger_name,
                    priority=self._calculate_priority(session, trigger_name),
                    summary=self._generate_handoff_summary(session),
                )

        return TransferDecision(should_transfer=False)

    def _generate_handoff_summary(self, session: DialogueSession) -> str:
        """生成转人工摘要 - 让人工客服快速了解上下文"""
        return {
            "user_intent": session.intent,
            "conversation_summary": session.get_early_summary(),
            "key_entities": session.entities,
            "sentiment_trend": session.get_sentiment_trend(),
            "attempted_solutions": session.get_tried_solutions(),
            "turn_count": session.turn_count,
        }
```

#### 4.2 人机协作模式

```
三种人机协作模式：

模式1: AI为主，人工兜底
┌──────┐  ┌──────┐  ┌──────┐
│ 用户  │──│  AI  │──│ 结果  │
└──────┘  └──┬───┘  └──────┘
             │ 置信度低/转人工请求
             ▼
         ┌──────┐
         │ 人工  │
         └──────┘

模式2: 人工为主，AI辅助
┌──────┐  ┌──────┐  ┌──────┐
│ 用户  │──│ 人工  │──│ 结果  │
└──────┘  └──┬───┘  └──────┘
             │ AI提供建议
             ▼
         ┌──────┐
         │  AI  │ → 推荐回复 / 知识检索 / 情感分析
         └──────┘

模式3: 人机并行
┌──────┐  ┌──────┐
│ 用户  │──│  AI  │──→ AI实时生成建议
└──────┘  └──────┘
              ↓ (建议)
         ┌──────┐
         │ 人工  │──→ 人工审核/修改后发送
         └──────┘
```

### 5. 满意度评估与持续优化

#### 5.1 多维评估体系

```python
class SatisfactionEvaluator:
    """客服质量评估器"""

    async def evaluate(self, session: DialogueSession) -> EvaluationResult:
        """多维度评估对话质量"""
        evaluations = await asyncio.gather(
            # 1. 隐式满意度（行为指标）
            self._evaluate_implicit(session),
            # 2. 显式满意度（用户反馈）
            self._evaluate_explicit(session),
            # 3. AI自动评估（LLM打分）
            self._evaluate_by_ai(session),
        )

        return EvaluationResult(
            implicit_score=evaluations[0],
            explicit_score=evaluations[1],
            ai_score=evaluations[2],
            composite_score=self._weighted_average(evaluations),
            issues=self._identify_issues(session, evaluations),
        )

    async def _evaluate_implicit(self, session: DialogueSession) -> float:
        """隐式满意度评估"""
        score = 1.0
        # 对话时长过长扣分
        if session.duration > timedelta(minutes=15):
            score -= 0.2
        # 多次转人工扣分
        if session.handoff_count > 1:
            score -= 0.3
        # 重复提问扣分
        if self._has_repeated_questions(session):
            score -= 0.2
        # 问题未解决（用户未确认解决）扣分
        if not session.resolved:
            score -= 0.3
        return max(0, score)
```

#### 5.2 持续优化闭环

```
持续优化闭环流程：

数据收集 → 效果评估 → 问题发现 → 优化实施 → 效果验证
    │           │           │           │           │
    ▼           ▼           ▼           ▼           ▼
对话日志     准确率      Bad Case    知识补充     A/B测试
用户反馈     满意度      意图误判    Prompt优化   灰度发布
转化率       解决率      检索失败    模型微调     效果对比

周度优化清单：
├── Top 20 Bad Case 分析与修复
├── 未覆盖意图的知识补充
├── Prompt模板调优
├── 检索策略参数调整
└── 新增FAQ入库
```

### 6. 面试加分点

- **情绪安抚话术**：检测到负面情绪时，AI自动生成安抚话术
- **多语言支持**：实时翻译支持，全球化客服场景
- **工单自动生成**：对话结束后自动总结生成工单
- **知识库自更新**：从成功对话中自动提取新FAQ

---

## Q04 AI Workflow平台设计

### 题目背景

> **面试原题**：请设计一个AI Workflow平台，支持可视化工作流编排、多种节点类型、运行时管理和监控，能够对标Dify、Coze等主流平台。

### 1. 工作流引擎设计

#### 1.1 核心概念模型

```
┌──────────────────────────────────────────────────────┐
│                   AI Workflow 核心概念                  │
├──────────────┬───────────────────────────────────────┤
│  Workflow    │ 工作流实例，包含节点和边的DAG定义         │
│  Node        │ 工作流中的执行单元（LLM/工具/条件/循环）  │
│  Edge        │ 节点之间的连接关系，携带条件表达式        │
│  Variable    │ 节点间传递的数据，支持类型约束             │
│  Execution   │ 一次工作流运行实例，维护运行时状态         │
│  Connector   │ 外部系统连接器（API/数据库/消息队列）     │
└──────────────┴───────────────────────────────────────┘
```

#### 1.2 工作流引擎核心实现

```python
class WorkflowEngine:
    """工作流执行引擎"""

    def __init__(self):
        self.node_registry = NodeRegistry()
        self.state_store = StateStore()
        self.event_bus = EventBus()

    async def execute(self, workflow: Workflow, inputs: dict) -> ExecutionResult:
        """执行工作流"""
        execution = Execution(
            id=generate_id(),
            workflow_id=workflow.id,
            inputs=inputs,
            status=ExecutionStatus.RUNNING,
        )

        try:
            # 拓扑排序获取执行顺序
            execution_order = self.topological_sort(workflow.graph)

            # 构建执行上下文
            context = ExecutionContext(
                execution=execution,
                variables={"inputs": inputs},
            )

            # 逐步执行节点
            for node_id in execution_order:
                node = workflow.get_node(node_id)

                # 获取节点输入（从上游节点输出获取）
                node_inputs = self.resolve_inputs(node, context)

                # 执行节点
                node_executor = self.node_registry.get_executor(node.type)
                result = await node_executor.execute(node, node_inputs, context)

                # 保存节点输出到上下文
                context.set_output(node_id, result)

                # 发送执行事件（用于实时监控）
                await self.event_bus.publish(NodeCompletedEvent(
                    execution_id=execution.id,
                    node_id=node_id,
                    result=result,
                ))

                # 处理条件分支
                if node.type == NodeType.CONDITION:
                    next_nodes = self.evaluate_condition(node, result, workflow.graph)
                    execution_order = self.adjust_order(execution_order, next_nodes)

            execution.status = ExecutionStatus.COMPLETED
            execution.outputs = context.get_final_outputs()

        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)

        finally:
            await self.state_store.save(execution)

        return ExecutionResult(execution=execution)

    def topological_sort(self, graph: Graph) -> list:
        """拓扑排序 - 确定节点执行顺序"""
        in_degree = {node: 0 for node in graph.nodes}
        for edge in graph.edges:
            in_degree[edge.target] += 1

        queue = deque([node for node, deg in in_degree.items() if deg == 0])
        order = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for edge in graph.get_outgoing_edges(node):
                in_degree[edge.target] -= 1
                if in_degree[edge.target] == 0:
                    queue.append(edge.target)

        if len(order) != len(graph.nodes):
            raise WorkflowError("工作流存在循环依赖")

        return order
```

### 2. 可视化编排器

#### 2.1 前端架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    可视化编排器架构                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ 画布区域   │  │ 节点面板  │  │ 属性面板  │  │ 调试面板│ │
│  │ (Canvas)  │  │ (Palette)│  │ (Props)  │  │(Debug) │ │
│  │           │  │          │  │          │  │        │ │
│  │ React Flow│  │ 节点分类  │  │ 选中节点  │  │ 运行日志│ │
│  │ 拖拽/连线  │  │ 拖拽到画布│  │ 参数编辑  │  │ 断点调试│ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │              状态管理层 (Zustand)                  │  │
│  │  nodes / edges / selectedNode / executionState   │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │              数据层 (API + WebSocket)              │  │
│  │  保存/加载工作流 / 实时执行状态推送                  │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

#### 2.2 工作流数据模型

```typescript
/** 工作流定义 */
interface WorkflowDefinition {
  id: string;
  name: string;
  description: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  variables: VariableDefinition[];
  metadata: WorkflowMetadata;
}

/** 工作流节点 */
interface WorkflowNode {
  id: string;
  type: NodeType;
  label: string;
  position: { x: number; y: number };
  config: NodeConfig;
  inputs: PortDefinition[];
  outputs: PortDefinition[];
}

/** 节点类型枚举 */
enum NodeType {
  LLM = "llm",           // LLM推理节点
  TOOL = "tool",          // 工具调用节点
  CONDITION = "condition", // 条件分支节点
  LOOP = "loop",          // 循环节点
  INPUT = "input",        // 输入节点
  OUTPUT = "output",      // 输出节点
  CODE = "code",          // 自定义代码节点
  KNOWLEDGE = "knowledge", // 知识库检索节点
  TRANSFORM = "transform", // 数据转换节点
  HUMAN = "human",         // 人工审核节点
}
```

### 3. 节点类型设计

#### 3.1 LLM节点

```python
class LLMNodeExecutor(NodeExecutor):
    """LLM推理节点执行器"""

    async def execute(self, node: WorkflowNode, inputs: dict, context: ExecutionContext):
        config = node.config

        # 构建Prompt - 支持模板变量替换
        prompt = self.render_template(
            template=config.prompt_template,
            variables={**inputs, **context.variables},
        )

        # 调用LLM
        response = await self.llm_client.chat(
            model=config.model,
            messages=[
                {"role": "system", "content": config.system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            response_format=config.output_format,  # JSON Mode支持
        )

        # 解析输出
        if config.output_format == "json":
            output = self.parse_json_output(response.content, config.output_schema)
        else:
            output = {"text": response.content}

        return NodeOutput(
            data=output,
            token_usage=response.usage,
            latency=response.latency,
        )
```

#### 3.2 工具节点

```python
class ToolNodeExecutor(NodeExecutor):
    """工具调用节点执行器"""

    async def execute(self, node: WorkflowNode, inputs: dict, context: ExecutionContext):
        config = node.config

        # 根据工具类型分发
        tool_type = config.tool_type

        if tool_type == "http_request":
            result = await self.execute_http(config, inputs)
        elif tool_type == "database_query":
            result = await self.execute_db_query(config, inputs)
        elif tool_type == "code_execution":
            result = await self.execute_code(config, inputs)
        elif tool_type == "connector":
            result = await self.execute_connector(config, inputs)
        else:
            raise NodeExecutionError(f"未知工具类型: {tool_type}")

        return NodeOutput(data=result)

    async def execute_http(self, config, inputs):
        """HTTP请求执行"""
        url = self.render_template(config.url, inputs)
        headers = self.render_template(config.headers, inputs)
        body = self.render_template(config.body, inputs)

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=config.method,
                url=url,
                headers=headers,
                json=body,
                timeout=aiohttp.ClientTimeout(total=config.timeout),
            ) as response:
                return await response.json()
```

#### 3.3 条件节点

```python
class ConditionNodeExecutor(NodeExecutor):
    """条件分支节点执行器"""

    async def execute(self, node: WorkflowNode, inputs: dict, context: ExecutionContext):
        config = node.config

        # 支持多种条件表达式
        condition_result = self.evaluate_conditions(
            conditions=config.conditions,
            variables={**inputs, **context.variables},
        )

        # 返回匹配的分支
        return NodeOutput(
            data={"matched_branch": condition_result.branch},
            routing=condition_result.next_nodes,  # 指定下一个执行的节点
        )

    def evaluate_conditions(self, conditions: list, variables: dict) -> ConditionResult:
        """条件表达式求值"""
        for condition in conditions:
            expression = condition["expression"]
            # 安全表达式求值（沙箱环境）
            result = safe_eval(expression, variables)
            if result:
                return ConditionResult(
                    branch=condition["branch"],
                    next_nodes=condition["next_nodes"],
                )

        # 默认分支
        return ConditionResult(
            branch="default",
            next_nodes=conditions[-1].get("default_next_nodes", []),
        )
```

#### 3.4 循环节点

```python
class LoopNodeExecutor(NodeExecutor):
    """循环节点执行器 - 执行子图"""

    async def execute(self, node: WorkflowNode, inputs: dict, context: ExecutionContext):
        config = node.config
        loop_variable = inputs.get(config.input_key, [])
        results = []

        # 循环策略
        if config.loop_type == "foreach":
            # 遍历列表
            for i, item in enumerate(loop_variable):
                if i >= config.max_iterations:
                    break

                # 创建子执行上下文
                sub_context = context.create_child_context(
                    variables={"item": item, "index": i},
                )

                # 执行子图（循环体内的节点）
                sub_result = await self.execute_subgraph(
                    config.sub_graph, sub_context,
                )
                results.append(sub_result)

        elif config.loop_type == "while":
            # 条件循环
            iteration = 0
            while iteration < config.max_iterations:
                # 检查循环条件
                condition = safe_eval(config.condition, context.variables)
                if not condition:
                    break

                sub_context = context.create_child_context()
                sub_result = await self.execute_subgraph(config.sub_graph, sub_context)
                results.append(sub_result)
                context.update_variables(sub_context.variables)
                iteration += 1

        elif config.loop_type == "parallel":
            # 并行循环 - 并发执行所有迭代
            tasks = []
            for i, item in enumerate(loop_variable[:config.max_iterations]):
                sub_context = context.create_child_context(
                    variables={"item": item, "index": i},
                )
                tasks.append(self.execute_subgraph(config.sub_graph, sub_context))
            results = await asyncio.gather(*tasks)

        return NodeOutput(data={"results": results, "count": len(results)})
```

### 4. 运行时管理与监控

#### 4.1 执行状态管理

```python
class ExecutionManager:
    """运行时执行管理器"""

    def __init__(self):
        self.state_store = StateStore()
        self.checkpoint_store = CheckpointStore()

    async def execute_with_checkpoint(self, workflow: Workflow, inputs: dict):
        """带检查点的执行 - 支持断点续跑"""
        execution = Execution(workflow_id=workflow.id, inputs=inputs)

        # 检查是否有未完成的执行（断点续跑）
        checkpoint = await self.checkpoint_store.get_latest(workflow.id)
        if checkpoint:
            execution = checkpoint.execution
            start_node = checkpoint.next_node
        else:
            start_node = workflow.get_start_node()

        # 执行并定期保存检查点
        try:
            result = await self.run_from(
                execution=execution,
                start_node=start_node,
                on_node_complete=lambda node: self.save_checkpoint(execution, node),
            )
            return result
        except ExecutionPausedException as e:
            # 人工审核节点暂停
            await self.state_store.save(execution, status="paused")
            raise
```

#### 4.2 监控与告警

```
Workflow 运行时监控指标：

┌──────────────┬────────────────────────┬────────────┐
│  指标类别     │  具体指标               │  告警阈值   │
├──────────────┼────────────────────────┼────────────┤
│  执行指标     │ 成功率                  │ < 95%      │
│              │ 平均执行时长             │ > 30s      │
│              │ 节点级超时率             │ > 5%       │
├──────────────┼────────────────────────┼────────────┤
│  资源指标     │ 并发执行数              │ > 1000     │
│              │ LLM Token消耗           │ 日预算80%   │
│              │ 队列积压                │ > 100      │
├──────────────┼────────────────────────┼────────────┤
│  质量指标     │ LLM输出质量评分         │ < 0.7      │
│              │ 工具调用失败率           │ > 10%      │
│              │ 人工干预率              │ > 20%      │
└──────────────┴────────────────────────┴────────────┘
```

### 5. Dify / Coze / n8n 架构分析

#### 5.1 三大平台对比

```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│   维度       │   Dify      │   Coze      │   n8n       │
├─────────────┼─────────────┼─────────────┼─────────────┤
│ 定位        │ AI应用开发   │ AI Bot构建   │ 通用自动化   │
│ 核心能力     │ RAG+Workflow│ Bot+Plugin  │ 200+集成     │
│ 工作流引擎   │ ✅ 核心      │ ✅ 核心      │ ✅ 核心      │
│ 可视化编排   │ ✅ Canvas    │ ✅ Canvas    │ ✅ Canvas    │
│ LLM集成     │ ✅ 多模型    │ ✅ 豆包为主   │ ✅ 插件式    │
│ RAG能力     │ ✅ 内置      │ ✅ 内置      │ ❌ 需开发    │
│ 开源        │ ✅ Apache   │ ❌ 闭源      │ ✅ FairCode  │
│ 适用场景     │ 企业AI应用   │ C端Bot      │ 业务自动化   │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

#### 5.2 Dify架构核心设计

```
Dify技术架构分析：

┌─────────────────────────────────────────────────┐
│                  前端 (Next.js)                   │
│  Canvas编排 / Prompt IDE / 数据集管理 / 监控       │
└──────────────────────┬──────────────────────────┘
                       │ API
┌──────────────────────▼──────────────────────────┐
│               后端 (Flask/Python)                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ App引擎   │ │ RAG引擎  │ │ Workflow引擎     │ │
│  │ (Chat/   │ │ (索引/   │ │ (DAG执行/       │ │
│  │  Agent)  │ │  检索)   │ │  节点调度)       │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ 模型层    │ │ 工具层   │ │ 插件层           │ │
│  │ (多模型   │ │ (API    │ │ (自定义          │ │
│  │  适配)   │ │  调用)   │ │  扩展)           │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│               基础设施层                          │
│  PostgreSQL / Redis / Weaviate / Celery / S3    │
└─────────────────────────────────────────────────┘

核心亮点：
1. 声明式Workflow定义（JSON/YAML）
2. 多模型统一适配层
3. 插件化工具系统
4. 可观测性内置
```

### 6. 面试加分点

- **DAG vs 状态机**：说明为什么选择DAG而非状态机（声明式、可视化友好）
- **错误恢复策略**：检查点续跑、超时重试、降级兜底
- **节点沙箱隔离**：代码执行节点的安全沙箱设计
- **版本管理**：工作流版本化、回滚、灰度发布

---

## Q05 RAG系统的生产级架构

### 题目背景

> **面试原题**：请设计一个生产级RAG系统，支持多路召回、重排序、查询改写，并具备完整的评估和持续优化机制。

### 1. 多路召回策略

#### 1.1 召回架构总览

```
                    用户查询
                       │
           ┌───────────┼───────────┐
           │           │           │
     ┌─────▼─────┐ ┌──▼───┐ ┌────▼────┐
     │ 向量召回   │ │BM25  │ │ 知识图谱 │
     │ (Dense)   │ │召回   │ │ 召回    │
     │           │ │(Sparse)│ │(Graph) │
     └─────┬─────┘ └──┬───┘ └────┬────┘
           │           │          │
           └───────────┼──────────┘
                       │
                  ┌────▼────┐
                  │  融合排序 │  RRF / 加权融合
                  └────┬────┘
                       │
                  ┌────▼────┐
                  │  ReRank │  Cross-Encoder
                  └────┬────┘
                       │
                  ┌────▼────┐
                  │ Top-K   │  最终候选集
                  └─────────┘
```

#### 1.2 向量召回（Dense Retrieval）

```python
class DenseRetriever:
    """向量召回器"""

    def __init__(self, vector_store, embed_model):
        self.vector_store = vector_store
        self.embed_model = embed_model

    async def retrieve(self, query: str, top_k: int = 20,
                       filters: dict = None) -> list:
        """向量相似度检索"""
        query_embedding = await self.embed_model.embed(query)

        results = await self.vector_store.search(
            vector=query_embedding,
            top_k=top_k,
            filter_expr=self._build_filter(filters),
            output_fields=["text", "metadata", "doc_id"],
        )

        return [SearchResult(
            text=r.text,
            score=r.distance,
            source="dense",
            metadata=r.metadata,
        ) for r in results]
```

#### 1.3 稀疏召回（Sparse Retrieval - BM25）

```python
class SparseRetriever:
    """BM25稀疏召回器"""

    def __init__(self, index_path: str):
        self.index = self._load_index(index_path)
        self.tokenizer = jieba  # 中文分词

    async def retrieve(self, query: str, top_k: int = 20,
                       filters: dict = None) -> list:
        """BM25关键词检索"""
        tokens = self.tokenizer.cut(query)
        scores = self.index.get_scores(tokens)

        # 按分数排序取top_k
        top_indices = sorted(range(len(scores)),
                            key=lambda i: scores[i], reverse=True)[:top_k]

        return [SearchResult(
            text=self.index.get_doc(idx),
            score=scores[idx],
            source="sparse",
            metadata=self.index.get_metadata(idx),
        ) for idx in top_indices]
```

#### 1.4 融合策略 - RRF（Reciprocal Rank Fusion）

```python
class RRFFuser:
    """RRF融合排序器"""

    def __init__(self, k: int = 60):
        self.k = k  # RRF常数

    def fuse(self, result_lists: list[list[SearchResult]],
             weights: list[float] = None) -> list:
        """多路召回结果融合"""
        if weights is None:
            weights = [1.0] * len(result_lists)

        score_map = {}  # doc_id → accumulated_score

        for results, weight in zip(result_lists, weights):
            for rank, result in enumerate(results):
                doc_id = result.metadata["doc_id"]
                rrf_score = weight / (self.k + rank + 1)

                if doc_id not in score_map:
                    score_map[doc_id] = {
                        "score": 0,
                        "result": result,
                        "sources": [],
                    }
                score_map[doc_id]["score"] += rrf_score
                score_map[doc_id]["sources"].append(result.source)

        # 按融合分数排序
        sorted_results = sorted(
            score_map.values(), key=lambda x: x["score"], reverse=True,
        )

        return [SearchResult(
            text=item["result"].text,
            score=item["score"],
            source="+".join(item["sources"]),
            metadata=item["result"].metadata,
        ) for item in sorted_results]
```

### 2. ReRank重排序

#### 2.1 Cross-Encoder重排序

```python
class CrossEncoderReranker:
    """Cross-Encoder重排序器"""

    def __init__(self, model_name: str = "bge-reranker-v2-m3"):
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    async def rerank(self, query: str, documents: list,
                     top_k: int = 5) -> list:
        """重排序 - 对(query, doc)对进行相关性打分"""
        pairs = [(query, doc.text) for doc in documents]

        # 批量编码
        inputs = self.tokenizer(
            pairs, padding=True, truncation=True,
            max_length=512, return_tensors="pt",
        )

        # 计算相关性分数
        with torch.no_grad():
            scores = self.model(**inputs).logits.squeeze(-1)

        # 排序并取top_k
        scored_docs = list(zip(documents, scores.tolist()))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return [SearchResult(
            text=doc.text,
            score=score,
            source=doc.source,
            metadata=doc.metadata,
        ) for doc, score in scored_docs[:top_k]]
```

#### 2.2 重排序效果对比

```
重排序效果对比（内部测试集）：

                    Recall@5   Recall@10  NDCG@5
仅向量检索            72.3%      81.5%     0.65
向量+BM25(RRF融合)    78.1%      85.2%     0.71
融合+Cross-Encoder    85.6%      91.3%     0.82
融合+Rerank+LLM筛选   88.2%      93.1%     0.86

结论：每增加一层精排，准确率提升约5-8个百分点
     但延迟也相应增加（50ms → 200ms → 1500ms）
```

### 3. 查询改写与扩展

#### 3.1 多策略查询改写

```python
class QueryRewriter:
    """查询改写引擎"""

    async def rewrite(self, query: str, strategy: str = "auto") -> list:
        """查询改写 - 返回多个改写后的查询"""
        strategies = {
            "hyde": self._hyde_rewrite,
            "step_back": self._step_back_rewrite,
            "decompose": self._decompose_rewrite,
            "expand": self._expand_rewrite,
        }

        if strategy == "auto":
            # 自动选择最佳策略
            strategy = await self._select_strategy(query)

        rewrites = await strategies[strategy](query)
        return [query] + rewrites  # 始终保留原始查询

    async def _hyde_rewrite(self, query: str) -> list:
        """HyDE - 假设性文档嵌入
        生成一个假设性的回答文档，用其向量去检索
        """
        hypothetical_doc = await self.llm.generate(
            prompt=f"请写一段可能回答以下问题的文档片段：\n{query}",
            max_tokens=200,
        )
        return [hypothetical_doc]

    async def _step_back_rewrite(self, query: str) -> list:
        """Step-Back - 回退到更高层次的问题
        将具体问题泛化，获取更广泛的上下文
        """
        step_back = await self.llm.generate(
            prompt=f"将以下问题泛化为一个更高层次的问题：\n{query}",
            max_tokens=100,
        )
        return [step_back]

    async def _decompose_rewrite(self, query: str) -> list:
        """问题分解 - 将复杂问题拆解为子问题
        """
        decomposed = await self.llm.generate(
            prompt=f"将以下复杂问题分解为2-4个简单的子问题：\n{query}",
            max_tokens=200,
        )
        return decomposed.split("\n")

    async def _expand_rewrite(self, query: str) -> list:
        """同义词扩展 - 生成语义等价的不同表述
        """
        expanded = await self.llm.generate(
            prompt=f"用3种不同的方式重新表述以下问题：\n{query}",
            max_tokens=200,
        )
        return expanded.split("\n")
```

#### 3.2 查询改写策略选择

```
查询改写策略选择指南：

┌──────────────────┬─────────────────┬────────────────┐
│  查询类型         │  推荐策略        │  原因           │
├──────────────────┼─────────────────┼────────────────┤
│  简单事实查询      │  原始查询        │  无需改写       │
│  模糊/口语化查询   │  HyDE           │  生成假设文档   │
│  复杂多跳查询      │  Decompose      │  分解为子问题   │
│  专业领域术语      │  Expand         │  同义词扩展     │
│  高层次抽象问题    │  Step-Back      │  泛化检索范围   │
└──────────────────┴─────────────────┴────────────────┘
```

### 4. 评估指标体系

#### 4.1 RAG评估四大维度

```python
class RAGEvaluator:
    """RAG系统评估器"""

    async def evaluate(self, test_set: list) -> EvaluationReport:
        """全面评估RAG系统"""
        results = {
            "retrieval": await self._evaluate_retrieval(test_set),
            "generation": await self._evaluate_generation(test_set),
            "end_to_end": await self._evaluate_e2e(test_set),
        }
        return EvaluationReport(**results)

    async def _evaluate_retrieval(self, test_set):
        """检索质量评估"""
        metrics = {
            "recall_at_5": [],    # Top-5召回率
            "recall_at_10": [],   # Top-10召回率
            "precision_at_5": [], # Top-5精确率
            "mrr": [],            # 平均倒数排名
            "ndcg_at_5": [],      # NDCG@5
        }
        for item in test_set:
            retrieved = await self.retriever.retrieve(item["query"])
            relevant_ids = set(item["relevant_doc_ids"])
            retrieved_ids = [r.metadata["doc_id"] for r in retrieved[:5]]

            metrics["recall_at_5"].append(
                len(set(retrieved_ids) & relevant_ids) / len(relevant_ids)
            )
            metrics["precision_at_5"].append(
                len(set(retrieved_ids) & relevant_ids) / len(retrieved_ids)
            )
            # ... 其他指标计算

        return {k: sum(v)/len(v) for k, v in metrics.items()}

    async def _evaluate_generation(self, test_set):
        """生成质量评估"""
        metrics = {
            "faithfulness": [],    # 忠实度 - 回答是否基于检索内容
            "answer_relevance": [], # 相关性 - 回答是否切题
            "hallucination_rate": [], # 幻觉率
        }
        for item in test_set:
            answer = await self.rag_system.answer(item["query"])

            # 使用LLM评估忠实度
            faithfulness = await self.llm.evaluate(
                prompt=f"""评估以下回答是否忠实于提供的上下文：
                上下文：{answer.sources}
                回答：{answer.text}
                评分1-5，5表示完全忠实""",
            )
            metrics["faithfulness"].append(faithfulness)

        return {k: sum(v)/len(v) for k, v in metrics.items()}
```

#### 4.2 评估指标详解

```
RAG评估指标矩阵：

┌──────────────┬──────────────┬──────────────────────────────┐
│  维度         │  指标         │  说明                        │
├──────────────┼──────────────┼──────────────────────────────┤
│  检索质量     │  Recall@K    │  相关文档是否被检索到          │
│              │  Precision@K │  检索结果中有多少是相关的       │
│              │  MRR         │  第一个相关结果的排名           │
│              │  NDCG        │  检索结果的排序质量             │
├──────────────┼──────────────┼──────────────────────────────┤
│  生成质量     │  Faithfulness│  回答是否忠实于检索内容         │
│              │  Relevance   │  回答是否切题                  │
│              │  Completeness│  回答是否完整                  │
│              │  Hallucination│ 幻觉率（编造信息的比例）       │
├──────────────┼──────────────┼──────────────────────────────┤
│  端到端      │  Accuracy    │  最终回答正确率（人工标注）      │
│              │  User Sat.   │  用户满意度评分                │
│              │  Latency     │  端到端响应延迟                │
└──────────────┴──────────────┴──────────────────────────────┘
```

### 5. 持续优化闭环

#### 5.1 RAG优化飞轮

```
RAG持续优化闭环：

    ┌─────────┐
    │  数据    │
    │  收集    │←── 用户反馈 / Bad Case / 查询日志
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │  分析    │──→ 检索失败分析 / 幻觉分析 / 性能分析
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │  优化    │──→ 切片策略调整 / Embedding微调 / Prompt优化
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │  评估    │──→ 自动化评估 / A/B测试 / 人工抽检
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │  上线    │──→ 灰度发布 / 全量上线 / 监控告警
    └────┬────┘
         │
         └────→ 回到「数据收集」
```

#### 5.2 优化手段清单

```
RAG系统优化手段矩阵：

┌──────────────┬──────────────────────────────┬──────────┐
│  优化阶段     │  优化手段                     │  效果提升  │
├──────────────┼──────────────────────────────┼──────────┤
│  索引优化     │  语义切分替代固定切分          │  +5-10%  │
│              │  chunk附加上下文摘要           │  +3-5%   │
│              │  多粒度索引(句子+段落+文档)    │  +5-8%   │
│              │  元数据过滤优化               │  +3-5%   │
├──────────────┼──────────────────────────────┼──────────┤
│  检索优化     │  多路召回融合                 │  +8-12%  │
│              │  ReRank重排序                │  +5-10%  │
│              │  查询改写(HyDE/分解)          │  +5-8%   │
│              │  Embedding模型微调            │  +10-15% │
├──────────────┼──────────────────────────────┼──────────┤
│  生成优化     │  Prompt工程优化               │  +5-10%  │
│              │  上下文压缩                   │  +3-5%   │
│              │  幻觉检测与过滤               │  减少错误 │
│              │  引用标注                     │  可追溯性 │
└──────────────┴──────────────────────────────┴──────────┘
```

### 6. 面试加分点

- **多模态RAG**：图片、表格、图表的索引与检索
- **自适应检索**：根据查询复杂度动态调整检索策略
- **引用溯源**：回答中精确引用原文位置（段落、页码）
- **知识图谱增强**：Graph RAG，利用实体关系提升检索质量

---

## Q06 多模态AI应用架构设计

### 题目背景

> **面试原题**：请设计一个多模态AI应用架构，支持图文理解、视频分析和多模态RAG检索。

### 1. 图文理解系统

#### 1.1 图文理解架构

```
多模态图文理解系统架构：

┌─────────────────────────────────────────────────┐
│                    输入层                         │
│  图片上传 / URL / 文档(PDF含图) / 截图            │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│                  理解层                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ OCR识别   │ │ 图像理解  │ │ 表格/图表解析    │ │
│  │ (PaddleOCR│ │ (GPT-4o  │ │ (结构化提取)     │ │
│  │  /Tesseract)│ │  /Qwen-VL)│ │                │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│                  融合层                           │
│  多模态特征融合 / 跨模态对齐 / 统一表征            │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│                  应用层                           │
│  图文问答 / 文档理解 / 图表分析 / 内容审核         │
└─────────────────────────────────────────────────┘
```

#### 1.2 图文理解实现

```python
class MultimodalUnderstandingService:
    """多模态理解服务"""

    async def understand_image(self, image: ImageInput,
                                query: str = None) -> UnderstandingResult:
        """图片理解 - 支持多种理解模式"""
        # Step 1: 图片预处理
        processed = await self.preprocess(image)

        # Step 2: 并行执行多种理解任务
        tasks = {
            "ocr": self.ocr_service.extract(processed),
            "vlm": self.vlm_service.understand(processed, query),
            "objects": self.detection_service.detect(processed),
        }
        results = await asyncio.gather(*tasks.values())
        result_map = dict(zip(tasks.keys(), results))

        # Step 3: 结果融合
        return UnderstandingResult(
            text_content=result_map["ocr"],
            semantic_understanding=result_map["vlm"],
            detected_objects=result_map["objects"],
        )

    async def understand_document_page(self, page_image: ImageInput) -> dict:
        """文档页面理解 - 提取结构化内容"""
        # 使用多模态大模型一次性理解整个页面
        response = await self.vlm_service.analyze(
            image=page_image,
            prompt="""分析这个文档页面，提取以下结构化信息：
            1. 主要文本内容
            2. 表格数据（以Markdown格式输出）
            3. 图表描述（描述图表类型、标题、关键数据点）
            4. 页面布局描述
            请以JSON格式输出。""",
        )
        return response
```

### 2. 视频分析系统

#### 2.1 视频分析架构

```
视频分析系统架构：

┌──────────────┐
│  视频输入     │
└──────┬───────┘
       │
       ▼
┌──────────────┐    关键帧提取（场景变化检测）
│  视频预处理   │───▶ 音频提取（Whisper转录）
│              │───▶ 字幕提取（OCR/ASS解析）
└──────┬───────┘
       │
  ┌────┼────┐
  │    │    │
  ▼    ▼    ▼
┌────┐┌────┐┌────┐
│视觉││音频││文本│   ← 三路并行处理
│分析││分析││分析│
└─┬──┘└─┬──┘└─┬──┘
  │     │     │
  └─────┼─────┘
        │
        ▼
┌──────────────┐
│  多模态融合   │   时空对齐 + 跨模态关联
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  应用输出     │   视频摘要 / 问答 / 检索 / 标签
└──────────────┘
```

#### 2.2 视频处理Pipeline

```python
class VideoAnalysisPipeline:
    """视频分析流水线"""

    async def analyze(self, video_path: str, query: str = None) -> VideoAnalysis:
        # Step 1: 视频预处理
        frames = await self.extract_keyframes(video_path, strategy="scene_change")
        audio = await self.extract_audio(video_path)
        transcript = await self.transcribe(audio)  # Whisper

        # Step 2: 视觉分析 - 对关键帧进行理解
        visual_analyses = await asyncio.gather(*[
            self.vlm_service.understand(frame, "描述这个画面的内容")
            for frame in frames
        ])

        # Step 3: 多模态融合
        fused = self.fuse_modalities(
            visual=visual_analyses,
            audio=transcript,
            timestamps=frames.timestamps,
        )

        # Step 4: 应用输出
        if query:
            # 视频问答
            answer = await self.answer_about_video(query, fused)
            return VideoAnalysis(summary=answer, transcript=transcript)

        # 视频摘要
        summary = await self.generate_summary(fused)
        return VideoAnalysis(summary=summary, transcript=transcript)

    async def extract_keyframes(self, video_path: str,
                                 strategy: str = "scene_change") -> list:
        """关键帧提取"""
        if strategy == "scene_change":
            # 基于场景变化的关键帧提取
            return self._scene_change_detection(video_path, threshold=30)
        elif strategy == "uniform":
            # 均匀采样
            return self._uniform_sampling(video_path, fps=1)
```

### 3. 多模态RAG

#### 3.1 多模态索引设计

```python
class MultimodalRAGIndexer:
    """多模态RAG索引器"""

    async def index_document(self, document: Document):
        """多模态文档索引"""
        # 1. 提取文本内容
        text_chunks = await self.text_chunker.split(document.text)

        # 2. 提取并理解图片
        image_descriptions = []
        for image in document.images:
            desc = await self.vlm_service.describe(image)
            image_descriptions.append({
                "image_id": image.id,
                "description": desc,
                "page_number": image.page,
                "image_type": image.type,  # photo/chart/diagram/screenshot
            })

        # 3. 提取并理解表格
        table_descriptions = []
        for table in document.tables:
            desc = await self.table_parser.describe(table)
            table_descriptions.append({
                "table_id": table.id,
                "markdown": table.to_markdown(),
                "description": desc,
                "page_number": table.page,
            })

        # 4. 统一向量化
        all_items = (
            [(c.text, {"type": "text", "chunk_id": c.id}) for c in text_chunks] +
            [(d["description"], {"type": "image", **d}) for d in image_descriptions] +
            [(d["description"], {"type": "table", **d}) for d in table_descriptions]
        )

        texts, metadatas = zip(*all_items)
        embeddings = await self.embedder.batch_embed(list(texts))

        await self.vector_store.insert(
            vectors=embeddings,
            texts=list(texts),
            metadata=list(metadatas),
        )
```

### 4. 技术挑战与解决方案

```
多模态AI应用核心挑战：

┌──────────────────┬───────────────────────────────────┐
│  挑战             │  解决方案                          │
├──────────────────┼───────────────────────────────────┤
│  模态对齐         │  CLIP式跨模态编码器                 │
│  （图文关联）     │  统一Embedding空间                  │
├──────────────────┼───────────────────────────────────┤
│  信息密度差异     │  多粒度索引（全局摘要+局部细节）     │
│  （图vs文）      │  自适应检索策略                     │
├──────────────────┼───────────────────────────────────┤
│  计算成本高       │  分级处理（小图OCR→大图VLM）        │
│  （视频分析）     │  关键帧提取减少冗余                 │
├──────────────────┼───────────────────────────────────┤
│  长视频处理       │  分段处理+全局摘要                  │
│                  │  层级化索引（场景→镜头→帧）          │
├──────────────────┼───────────────────────────────────┤
│  表格理解         │  结构化解析+Markdown表征             │
│                  │  表格专用Embedding模型               │
└──────────────────┴───────────────────────────────────┘
```

### 5. 面试加分点

- **实时视频流处理**：摄像头实时分析架构（帧采样+滑动窗口）
- **多模态Agent**：结合视觉理解的自主Agent（截图→操作→验证循环）
- **图文一致性检查**：检测文档中图表与文字描述是否矛盾

---

## Q07 AI应用的可观测性设计

### 题目背景

> **面试原题**：请设计一个AI应用的可观测性系统，覆盖日志、链路追踪、指标监控和成本优化。

### 1. 日志体系设计

#### 1.1 结构化日志规范

```python
class AILogger:
    """AI应用专用日志器"""

    def log_request(self, request_id: str, user_id: str, query: str,
                    metadata: dict):
        """记录请求日志"""
        logger.info("ai_request", extra={
            "request_id": request_id,
            "user_id": user_id,
            "query": query[:500],  # 截断长文本
            "query_length": len(query),
            "model": metadata.get("model"),
            "temperature": metadata.get("temperature"),
            "max_tokens": metadata.get("max_tokens"),
            "timestamp": datetime.utcnow().isoformat(),
            "service": "ai-gateway",
            "environment": os.getenv("ENV"),
        })

    def log_retrieval(self, request_id: str, query: str,
                      results: list, latency_ms: float):
        """记录检索日志"""
        logger.info("retrieval_result", extra={
            "request_id": request_id,
            "query": query[:200],
            "retrieved_count": len(results),
            "top_score": results[0].score if results else 0,
            "sources": [r.metadata["source"] for r in results[:5]],
            "latency_ms": latency_ms,
            "strategy": "hybrid_search",
        })

    def log_generation(self, request_id: str, prompt_tokens: int,
                       completion_tokens: int, latency_ms: float,
                       model: str):
        """记录生成日志"""
        logger.info("llm_generation", extra={
            "request_id": request_id,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "latency_ms": latency_ms,
            "tokens_per_second": completion_tokens / (latency_ms / 1000),
            "estimated_cost_usd": self._calculate_cost(
                model, prompt_tokens, completion_tokens),
        })

    def log_error(self, request_id: str, error_type: str,
                  error_message: str, stack_trace: str):
        """记录错误日志"""
        logger.error("ai_error", extra={
            "request_id": request_id,
            "error_type": error_type,
            "error_message": error_message,
            "stack_trace": stack_trace[:2000],
            "severity": self._classify_severity(error_type),
        })
```

#### 1.2 日志架构

```
AI应用日志架构：

┌─────────────────────────────────────────────┐
│              应用服务集群                      │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐  │
│  │API服务│ │RAG服务│ │Agent │ │Embedding │  │
│  └──┬───┘ └──┬───┘ └──┬───┘ └────┬─────┘  │
└─────┼────────┼────────┼──────────┼─────────┘
      │        │        │          │
      ▼        ▼        ▼          ▼
┌─────────────────────────────────────────────┐
│           日志收集层 (Fluentd/Filebeat)       │
└──────────────────────┬──────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │  ELK     │ │  ClickHouse│ │  S3/OSS │
    │ (全文搜索)│ │ (分析查询) │ │ (冷存储) │
    └──────────┘ └──────────┘ └──────────┘
```

### 2. 链路追踪

#### 2.1 AI请求链路追踪

```python
class AITracer:
    """AI应用链路追踪器"""

    async def trace_request(self, request_id: str, query: str):
        """AI请求全链路追踪"""
        with tracer.start_as_current_span("ai_request") as root_span:
            root_span.set_attribute("request_id", request_id)
            root_span.set_attribute("user_query", query[:200])

            # Span 1: 查询理解
            with tracer.start_as_current_span("query_understanding"):
                rewritten = await self.query_rewriter.rewrite(query)

            # Span 2: 权限检查
            with tracer.start_as_current_span("permission_check"):
                permissions = await self.auth_service.check(request_id)

            # Span 3: 检索
            with tracer.start_as_current_span("retrieval") as retrieval_span:
                results = await self.retriever.retrieve(rewritten)
                retrieval_span.set_attribute("result_count", len(results))
                retrieval_span.set_attribute("top_score", results[0].score)

            # Span 4: 重排序
            with tracer.start_as_current_span("reranking"):
                reranked = await self.reranker.rerank(query, results)

            # Span 5: LLM生成
            with tracer.start_as_current_span("llm_generation") as llm_span:
                answer = await self.llm.generate(query, reranked)
                llm_span.set_attribute("model", answer.model)
                llm_span.set_attribute("tokens", answer.total_tokens)

            # Span 6: 后处理
            with tracer.start_as_current_span("post_processing"):
                final = await self.post_processor.process(answer)

            return final
```

#### 2.2 链路可视化

```
AI请求链路追踪可视化示例：

Request ID: req_abc123
Total Duration: 2847ms

├── ai_request [2847ms]
│   ├── query_understanding [156ms]        ████
│   ├── permission_check [23ms]            ▏
│   ├── retrieval [387ms]                  ██████████
│   │   ├── vector_search [198ms]          █████
│   │   ├── bm25_search [89ms]            ██
│   │   └── rrf_fusion [12ms]             ▏
│   ├── reranking [234ms]                  ██████
│   ├── llm_generation [1823ms]            ██████████████████████████████████████████
│   │   ├── ttft (首Token延迟) [423ms]     ██████████
│   │   └── token_generation [1400ms]      ██████████████████████████████
│   └── post_processing [67ms]             ██
```

### 3. 指标监控

#### 3.1 核心指标体系

```
AI应用指标监控体系（四层模型）：

Layer 1: 用户体验指标
├── TTFT (Time to First Token)     目标: < 1s
├── TPS (Tokens Per Second)        目标: > 30 tokens/s
├── 端到端延迟                      目标: < 5s
├── 答案准确率                      目标: > 85%
└── 用户满意度                      目标: > 4.0/5.0

Layer 2: 系统性能指标
├── QPS / RPS (请求吞吐)
├── P50 / P95 / P99 延迟
├── 错误率 (4xx / 5xx)
├── 缓存命中率
└── 重试率

Layer 3: AI质量指标
├── 检索召回率 (Recall@K)
├── 检索精确率 (Precision@K)
├── 幻觉率 (Hallucination Rate)
├── LLM输出质量评分
└── 意图识别准确率

Layer 4: 资源指标
├── GPU利用率
├── Token消耗速率
├── 向量数据库QPS
├── 存储使用量
└── 网络带宽
```

#### 3.2 Prometheus监控配置

```yaml
# AI应用Prometheus监控规则
groups:
  - name: ai_application
    rules:
      # 延迟告警
      - alert: HighLatencyP99
        expr: histogram_quantile(0.99, ai_request_duration_seconds_bucket) > 10
        for: 5m
        labels:
          severity: warning

      # 错误率告警
      - alert: HighErrorRate
        expr: rate(ai_request_errors_total[5m]) / rate(ai_request_total[5m]) > 0.05
        for: 3m
        labels:
          severity: critical

      # LLM服务不可用
      - alert: LLMServiceDown
        expr: up{job="llm-service"} == 0
        for: 1m
        labels:
          severity: critical

      # Token消耗异常
      - alert: TokenBurnRateHigh
        expr: rate(ai_tokens_consumed_total[1h]) > 100000
        for: 10m
        labels:
          severity: warning
```

### 4. 成本监控与优化

#### 4.1 成本模型

```python
class CostMonitor:
    """AI应用成本监控器"""

    # 模型定价表（USD per 1M tokens）
    MODEL_PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
        "qwen2.5-72b": {"input": 0.50, "output": 1.50},
    }

    def calculate_cost(self, model: str, prompt_tokens: int,
                       completion_tokens: int) -> float:
        """计算单次请求成本"""
        pricing = self.MODEL_PRICING.get(model, {"input": 0, "output": 0})
        cost = (prompt_tokens * pricing["input"] +
                completion_tokens * pricing["output"]) / 1_000_000
        return cost

    async def get_daily_cost_report(self) -> CostReport:
        """生成每日成本报告"""
        # 按模型聚合
        model_costs = await self.db.query("""
            SELECT model, SUM(prompt_tokens) as total_prompt,
                   SUM(completion_tokens) as total_completion,
                   SUM(cost_usd) as total_cost,
                   COUNT(*) as request_count
            FROM ai_usage_logs
            WHERE date = CURRENT_DATE
            GROUP BY model
        """)

        # 按用户/部门聚合
        user_costs = await self.db.query("""
            SELECT user_id, department, SUM(cost_usd) as total_cost
            FROM ai_usage_logs
            WHERE date = CURRENT_DATE
            GROUP BY user_id, department
            ORDER BY total_cost DESC
            LIMIT 20
        """)

        return CostReport(model_costs=model_costs, user_costs=user_costs)
```

#### 4.2 成本优化策略

```
AI应用成本优化策略：

┌──────────────────┬────────────────────────────┬───────────┐
│  策略             │  说明                       │  节省比例  │
├──────────────────┼────────────────────────────┼───────────┤
│  模型路由         │ 简单任务用小模型             │  40-60%   │
│  语义缓存         │ 相似查询复用结果             │  15-25%   │
│  Prompt压缩       │ 减少无效Token               │  10-20%   │
│  批量处理         │ 合并请求降低开销             │  10-15%   │
│  自部署模型       │ 高频场景自建推理服务          │  50-70%   │
│  Token预算控制    │ 用户/部门级配额管理          │  防失控   │
└──────────────────┴────────────────────────────┴───────────┘
```

### 5. 面试加分点

- **实时异常检测**：基于指标时序数据的异常检测（3-sigma / ML异常检测）
- **成本归因分析**：精确到功能级别的成本分摊（RAG vs Agent vs 直接对话）
- **SLO管理**：定义AI应用的SLI/SLO/SLA，并建立错误预算机制

---

## Q08 AI应用的A/B测试与灰度发布

### 题目背景

> **面试原题**：请设计一个AI应用的A/B测试与灰度发布系统，支持Prompt版本管理、模型切换策略和效果评估。

### 1. Prompt版本管理

#### 1.1 Prompt管理架构

```python
class PromptManager:
    """Prompt版本管理器"""

    def __init__(self, store: PromptStore):
        self.store = store
        self.cache = LRUCache(maxsize=1000)

    async def get_prompt(self, prompt_key: str,
                         version: str = "latest") -> PromptTemplate:
        """获取Prompt模板（支持版本控制）"""
        cache_key = f"{prompt_key}:{version}"

        # 缓存命中
        if cache_key in self.cache:
            return self.cache[cache_key]

        # 从存储获取
        if version == "latest":
            prompt = await self.store.get_latest(prompt_key)
        else:
            prompt = await self.store.get_version(prompt_key, version)

        self.cache[cache_key] = prompt
        return prompt

    async def create_version(self, prompt_key: str, content: str,
                              variables: list, metadata: dict) -> str:
        """创建新版本"""
        current = await self.store.get_latest(prompt_key)
        new_version = self._increment_version(current.version)

        await self.store.save(PromptTemplate(
            key=prompt_key,
            version=new_version,
            content=content,
            variables=variables,
            metadata={
                **metadata,
                "created_at": datetime.now().isoformat(),
                "parent_version": current.version,
                "change_description": metadata.get("description", ""),
            },
        ))

        # 使缓存失效
        self.cache.pop(f"{prompt_key}:latest", None)

        return new_version

    async def rollback(self, prompt_key: str, target_version: str):
        """回滚到指定版本"""
        await self.store.set_active_version(prompt_key, target_version)
        self.cache.clear()
```

#### 1.2 Prompt版本数据模型

```typescript
/** Prompt模板版本 */
interface PromptVersion {
  key: string;              // 唯一标识，如 "customer_service_qa"
  version: string;          // 语义版本号 "v1.2.3"
  content: string;          // Prompt内容（支持变量占位符）
  system_prompt: string;    // System Prompt
  variables: VariableDef[]; // 变量定义
  model_config: {
    model: string;
    temperature: number;
    max_tokens: number;
    response_format?: string;
  };
  metadata: {
    author: string;
    created_at: string;
    change_description: string;
    parent_version: string;
    evaluation_score?: number;  // 评估分数
    tags: string[];
  };
  status: "draft" | "testing" | "active" | "deprecated";
}
```

### 2. 模型切换策略

#### 2.1 智能路由网关

```python
class ModelRouter:
    """模型智能路由网关"""

    def __init__(self):
        self.routing_rules = []
        self.circuit_breakers = {}  # 熔断器
        self.cost_tracker = CostTracker()

    async def select_model(self, request: AIRequest) -> ModelConfig:
        """智能模型选择"""
        # 1. 检查是否有明确的实验分流
        experiment_model = await self.experiment_service.get_variant(
            user_id=request.user_id,
            experiment_key="model_comparison",
        )
        if experiment_model:
            return experiment_model

        # 2. 基于规则的路由
        for rule in self.routing_rules:
            if rule.matches(request):
                return rule.model_config

        # 3. 基于成本的路由
        if await self.cost_tracker.is_over_budget(request.user_id):
            return ModelConfig(model="gpt-4o-mini")  # 降级到低成本模型

        # 4. 基于负载的路由
        available_models = self._get_healthy_models()
        return self._select_by_load(available_models)

    async def _check_circuit_breaker(self, model: str) -> bool:
        """检查熔断器状态"""
        breaker = self.circuit_breakers.get(model)
        if not breaker:
            return True  # 未设置熔断器，允许通过

        if breaker.state == "open":
            # 熔断中，检查是否可以半开
            if time.time() - breaker.opened_at > breaker.timeout:
                breaker.state = "half_open"
                return True
            return False

        return True
```

#### 2.2 熔断降级策略

```
模型熔断降级链路：

请求 → 主模型(GPT-4o)
          │
          ├─ 成功 → 返回结果
          │
          ├─ 超时/错误 → 熔断计数 +1
          │                │
          │                ├─ 未达阈值 → 重试（最多2次）
          │                │
          │                └─ 达到阈值 → 触发熔断
          │                              │
          │                              ▼
          │                     降级模型(GPT-4o-mini)
          │                              │
          │                              ├─ 成功 → 返回结果
          │                              │
          │                              └─ 也失败 → 兜底响应
          │                                          │
          │                                          ▼
          │                                    "抱歉，服务暂时不可用"
          │
          └─ 熔断恢复：30秒后进入半开状态，尝试少量请求

熔断配置：
- 错误率阈值：50%（窗口内）
- 最小请求数：10次
- 熔断持续时间：30秒
- 半开请求数：3次
```

### 3. 灰度发布流程

#### 3.1 灰度发布架构

```
AI应用灰度发布流程：

阶段1: 内部测试 (0-1%)
┌──────────┐
│ 开发团队  │──→ 集成测试 / 回归测试
└──────────┘

阶段2: 小流量灰度 (1-5%)
┌──────────┐
│ 种子用户  │──→ 收集反馈 / 监控指标
└──────────┘

阶段3: 扩大灰度 (5-20%)
┌──────────┐
│ 分桶实验  │──→ A/B测试 / 统计显著性
└──────────┘

阶段4: 全量发布 (100%)
┌──────────┐
│ 全部用户  │──→ 持续监控 / 快速回滚
└──────────┘

每阶段准入条件：
├── 阶段1→2: 集成测试通过率 100%
├── 阶段2→3: 核心指标无回归，用户反馈正向
├── 阶段3→4: A/B测试统计显著（p < 0.05），效果正向
└── 任何阶段可一键回滚
```

#### 3.2 灰度发布实现

```python
class GradualRolloutManager:
    """灰度发布管理器"""

    async def get_rollout_config(self, feature_key: str,
                                  user_id: str) -> RolloutConfig:
        """获取灰度配置"""
        rollout = await self.store.get_rollout(feature_key)

        if not rollout or rollout.status != "active":
            return RolloutConfig(use_new=False, reason="no_active_rollout")

        # 用户分桶
        bucket = self._get_user_bucket(user_id, feature_key)

        # 检查是否在灰度范围内
        if bucket < rollout.percentage:
            return RolloutConfig(
                use_new=True,
                variant=rollout.variant,
                reason=f"bucket_{bucket}_in_{rollout.percentage}",
                metadata={"experiment_id": rollout.experiment_id},
            )

        return RolloutConfig(use_new=False, reason=f"bucket_{bucket}_out")

    def _get_user_bucket(self, user_id: str, feature_key: str) -> int:
        """用户分桶 - 基于一致性哈希"""
        hash_input = f"{user_id}:{feature_key}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()
        return int(hash_value[:8], 16) % 100

    async def emergency_rollback(self, feature_key: str, reason: str):
        """紧急回滚"""
        await self.store.update_rollout(feature_key, {
            "status": "rolled_back",
            "rolled_back_at": datetime.now().isoformat(),
            "rollback_reason": reason,
        })
        # 通知所有服务实例
        await self.event_bus.publish(RollbackEvent(feature_key=feature_key))
```

### 4. 效果评估指标

#### 4.1 A/B测试评估框架

```python
class ABTestEvaluator:
    """A/B测试效果评估器"""

    async def evaluate(self, experiment_id: str) -> ExperimentResult:
        """评估A/B测试结果"""
        # 1. 获取实验数据
        control_data = await self.get_group_data(experiment_id, "control")
        treatment_data = await self.get_group_data(experiment_id, "treatment")

        # 2. 计算各指标
        metrics = {}
        for metric_name, metric_fn in self.metric_functions.items():
            control_value = metric_fn(control_data)
            treatment_value = metric_fn(treatment_data)

            # 3. 统计显著性检验
            p_value = self._t_test(control_data[metric_name],
                                   treatment_data[metric_name])

            # 4. 计算置信区间
            ci = self._confidence_interval(
                control_data[metric_name],
                treatment_data[metric_name],
            )

            metrics[metric_name] = {
                "control": control_value,
                "treatment": treatment_value,
                "lift": (treatment_value - control_value) / control_value,
                "p_value": p_value,
                "significant": p_value < 0.05,
                "confidence_interval": ci,
            }

        # 5. 综合结论
        return ExperimentResult(
            experiment_id=experiment_id,
            metrics=metrics,
            recommendation=self._make_recommendation(metrics),
            sample_sizes={
                "control": len(control_data),
                "treatment": len(treatment_data),
            },
        )
```

#### 4.2 评估指标体系

```
AI应用A/B测试核心评估指标：

┌──────────────┬──────────────────┬──────────────────┐
│  指标类别     │  具体指标         │  计算方式         │
├──────────────┼──────────────────┼──────────────────┤
│  质量指标     │  答案准确率       │  人工标注正确数/总数│
│              │  幻觉率          │  编造信息数/总数    │
│              │  引用准确率       │  正确引用数/总引用  │
├──────────────┼──────────────────┼──────────────────┤
│  效率指标     │  任务完成率       │  一次解决数/总数    │
│              │  平均对话轮数     │  总轮数/总会话数    │
│              │  人工转接率       │  转人工数/总会话数  │
├──────────────┼──────────────────┼──────────────────┤
│  体验指标     │  用户满意度(CSAT) │  满意数/评价总数    │
│              │  NPS净推荐值      │  推荐者%-贬损者%   │
│              │  留存率          │  次日/7日/30日留存  │
├──────────────┼──────────────────┼──────────────────┤
│  成本指标     │  单次请求成本     │  Token单价×消耗量  │
│              │  单位价值成本     │  总成本/成功解决数  │
└──────────────┴──────────────────┴──────────────────┘

统计显著性要求：
- 最小样本量：每组 ≥ 1000次请求
- 置信水平：95%（p < 0.05）
- 最小可检测效应(MDE)：5%
- 实验周期：≥ 7天（覆盖工作日和周末）
```

### 5. 面试加分点

- **多臂老虎机（MAB）**：替代传统A/B测试，动态分配流量到表现更好的变体
- **交叉实验设计**：同时测试多个因素（模型×Prompt×检索策略），减少实验次数
- **护栏指标**：定义安全底线指标，任何实验变更不能导致护栏指标恶化
- **实验平台设计**：完整的实验管理后台，支持实验创建、审核、监控、分析

---

# 本章面试重点

## 高频考点总结

### 必答考点（出现率 > 80%）

```
1. RAG系统设计：多路召回、ReRank、查询改写的完整链路
   → 展示对检索增强生成的深度理解

2. 向量数据库选型：Milvus vs Qdrant vs PGVector的对比
   → 展示技术选型的权衡能力

3. AI应用的性能优化：缓存、分层检索、模型路由
   → 展示工程落地能力

4. LLM幻觉问题处理：检测、预防、后处理
   → 展示对AI局限性的认知
```

### 加分考点（出现率 50-80%）

```
5. 工作流引擎设计：DAG调度、节点类型、错误恢复
   → 展示系统架构能力

6. AI应用可观测性：日志、链路追踪、指标监控
   → 展示生产运维意识

7. A/B测试与灰度发布：Prompt版本管理、模型切换
   → 展示数据驱动思维

8. 安全性设计：权限控制、注入防护、数据隔离
   → 展示安全意识
```

### 超纲考点（区分度最高）

```
9. 多模态AI系统：图文理解、视频分析
   → 展示技术广度

10. 成本优化：Token预算、模型路由、自部署策略
    → 展示商业意识

11. 持续优化闭环：Bad Case分析、Embedding微调
    → 展示产品思维
```

---

# 一页速记版

```
┌─────────────────────────────────────────────────────────────┐
│                   AI系统设计 一页速记                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  【知识库/ RAG】                                             │
│  离线：文档解析→语义切片→向量化→存入向量数据库                  │
│  在线：查询改写→多路召回(向量+BM25)→RRF融合→ReRank→LLM生成    │
│  选型：Milvus(大规模) / Qdrant(中规模) / BGE-M3(Embedding)   │
│  优化：语义缓存 / 分层检索 / HyDE改写 / chunk上下文摘要        │
│                                                             │
│  【SQL Agent】                                               │
│  流程：NL问题→Schema Linking→SQL生成→验证→执行→结果解读        │
│  安全：AST解析 / 只允许SELECT / 表权限控制 / 行级过滤          │
│  纠错：错误分类→LLM修正→模糊匹配→重试(最多3次)                │
│                                                             │
│  【客服Agent】                                               │
│  对话：状态机管理 / 滑动窗口+摘要压缩 / 意图层级树              │
│  路由：规则匹配(快速) → 分类模型(中速) → LLM推理(兜底)         │
│  协作：转人工触发(显式/隐式/失败/情感) / 三种人机模式           │
│                                                             │
│  【Workflow平台】                                            │
│  引擎：DAG拓扑排序 / 节点注册表 / 事件总线 / 检查点续跑         │
│  节点：LLM / 工具(HTTP/DB/代码) / 条件 / 循环 / 人工审核       │
│  对标：Dify(AI应用) / Coze(C端Bot) / n8n(通用自动化)          │
│                                                             │
│  【多模态】                                                  │
│  图文：OCR + VLM(GPT-4o/Qwen-VL) + 目标检测 → 融合理解        │
│  视频：关键帧提取 + Whisper转录 + 视觉分析 → 多模态融合         │
│  RAG：文本+图片描述+表格 描述 → 统一Embedding → 多模态检索     │
│                                                             │
│  【可观测性】                                                │
│  日志：结构化JSON / ELK+ClickHouse / 全链路request_id         │
│  追踪：OpenTelemetry / Span树 / 可视化延迟分布                 │
│  指标：四层(体验/性能/质量/资源) / Prometheus+Grafana           │
│  成本：Token计费模型 / 按模型/用户/功能分摊 / 预算控制          │
│                                                             │
│  【A/B测试】                                                 │
│  Prompt：版本管理(draft→testing→active) / 语义版本号           │
│  路由：一致性哈希分桶 / 智能模型路由 / 熔断降级                 │
│  发布：内部测试→小流量→扩大灰度→全量 / 每阶段有准入条件         │
│  评估：t检验显著性 / 多维指标(质量/效率/体验/成本) / 护栏指标    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# 面试前5分钟冲刺版

```
🔥 AI系统设计 - 5分钟冲刺清单 🔥

□ RAG核心链路：解析→切片→向量化→多路召回→ReRank→生成
□ 向量数据库三选一：Milvus(大)/Qdrant(中)/PGVector(轻)
□ Embedding首选：BGE-M3（多语言、多粒度、效果好）
□ 查询改写三板斧：HyDE(假设文档)、Decompose(分解)、Expand(扩展)
□ 融合排序：RRF融合 → Cross-Encoder精排 → 效果提升17%+
□ SQL Agent安全：AST解析 + 只读账号 + 行级权限 + 查询超时
□ 客服Agent路由：规则→分类模型→LLM三层递进
□ 转人工四大触发：显式请求/情感负面/意图超纲/重复失败
□ Workflow引擎：DAG拓扑排序 + 检查点续跑 + 事件驱动
□ 灰度发布四阶段：内部→种子用户→分桶实验→全量
□ A/B测试底线：每组≥1000样本、p<0.05、≥7天
□ 成本优化：模型路由 + 语义缓存 + Prompt压缩 + 自部署
□ 可观测性四层：体验指标/性能指标/质量指标/资源指标
□ 幻觉处理：引用溯源 + 事实校验 + 置信度标注

💡 面试口诀：
  设计先聊需求 → 选型要比方案 → 架构画图说话
  优化要量化 → 安全不能忘 → 监控要具体
```

---

> **下一章预告**：P13将深入探讨**AI Agent高级设计模式**，包括ReAct、Plan-and-Execute、Multi-Agent协作等前沿架构模式，以及如何在生产环境中实现可靠的Agent系统。
---

# 🚀 Pro增强版 — P12 AI系统设计

## 📄 一页速记版

### 面试前5分钟快速复习

**必背概念TOP10：**
1. 企业知识库系统：文档解析→分块→向量化→检索→生成，五层架构
2. SQL Agent：Text-to-SQL + Schema Linking + 自修正循环，NL2SQL准确率是核心指标
3. 客服Agent：意图识别→路由→RAG检索→回复生成→兜底策略，多轮对话状态管理是难点
4. Workflow平台：DAG编排引擎 + 节点类型体系 + 可视化编辑器 + 运行时管理
5. RAG生产级架构：混合检索（向量+关键词+重排序）> 纯向量检索
6. 多模态架构：统一Embedding空间 + 跨模态检索 + 多模态LLM融合
7. 可观测性四层：体验指标（用户满意度）→ 质量指标（准确率/幻觉率）→ 性能指标（延迟/吞吐）→ 资源指标（GPU/CPU）
8. A/B测试：每组≥1000样本、p<0.05、运行≥7天，分桶实验避免辛普森悖论
9. 灰度发布四阶段：内部测试→种子用户→分桶实验→全量上线
10. 成本优化三角：模型路由（大小模型分流）+ 语义缓存 + Prompt压缩

**核心架构图（企业知识库）：**
```
用户请求 → API Gateway → 权限校验 → 意图路由
  ├→ 简单查询 → 语义缓存命中? → 直接返回
  ├→ 知识问答 → Query改写 → 混合检索 → 重排序 → LLM生成 → 引用溯源
  └→ 复杂分析 → 多步推理 → 工具调用 → 结果整合
```

**核心架构图（SQL Agent）：**
```
自然语言问题 → 意图解析 → Schema Linking → SQL生成
  → SQL校验/安全检查 → 执行 → 结果格式化 → 自然语言总结
  ↻ 失败? → 错误分析 → 自修正（最多2次）→ 兜底
```

**核心口诀：**
- 系统设计五步法：需求分析→架构设计→技术选型→关键难点→量化指标
- RAG三板斧：检索准（混合检索）、生成稳（引用溯源）、成本低（缓存+路由）
- Agent设计三要素：工具调用 + 记忆管理 + 异常兜底

---

## ⚡ 面试前5分钟冲刺

**Q: 企业知识库系统的核心架构？**
30秒答：五层——文档处理层（解析/分块）、向量索引层（Embedding/存储）、检索层（混合检索+重排序）、生成层（LLM+引用溯源）、应用层（API/权限/监控）。

**Q: RAG和微调怎么选？**
30秒答：知识频繁更新、需要引用溯源选RAG；任务固定、需要风格一致性选微调；生产环境通常RAG+微调组合。

**Q: SQL Agent怎么保证SQL正确性？**
30秒答：三层保障——Schema Linking减少幻觉、SQL语法校验+安全白名单、执行失败自修正循环（最多2次）。

**Q: 客服Agent的多轮对话怎么管理？**
30秒答：对话状态机 + Slot Filling + 上下文窗口管理。关键变量（订单号、问题类型）跨轮次传递，超时自动降级。

**Q: AI应用的可观测性怎么做？**
30秒答：四层指标——用户体验（满意度/首次解决率）、质量（准确率/幻觉率）、性能（P50/P99延迟）、资源（GPU利用率/Token成本）。

**Q: 如何做AI应用的A/B测试？**
30秒答：分桶实验，样本量≥1000/组，p<0.05显著性，运行≥7天消除周期效应。指标分护栏指标（不退步）和实验指标（需提升）。

**Q: 多模态AI应用的核心挑战？**
30秒答：跨模态对齐（图文Embedding统一空间）、模态缺失处理（只有文本/只有图片）、推理成本（多模态模型Token消耗大）。

**Q: AI应用成本优化的核心手段？**
30秒答：模型路由（简单用小模型、复杂用大模型）+ 语义缓存（相似问题直接命中）+ Prompt压缩（减少Token）+ 自部署开源模型。

---

## 🎯 P12章节适用岗位映射

| 题目 | AI应用开发 | Agent工程师 | AI架构师 | Prompt工程师 | AI平台 |
|------|-----------|------------|---------|-------------|--------|
| 企业知识库架构 | ✅ | ✅ | ✅ | ⬜ | ✅ |
| SQL Agent设计 | ✅ | ✅ | ✅ | ⬜ | ✅ |
| 客服Agent设计 | ✅ | ✅ | ✅ | ✅ | ✅ |
| Workflow平台设计 | ✅ | ✅ | ✅ | ⬜ | ✅ |
| RAG生产级架构 | ✅ | ✅ | ✅ | ⬜ | ✅ |
| 多模态架构 | ✅ | ⬜ | ✅ | ⬜ | ✅ |
| 可观测性设计 | ✅ | ✅ | ✅ | ⬜ | ✅ |
| A/B测试与灰度 | ✅ | ⬜ | ✅ | ⬜ | ✅ |
