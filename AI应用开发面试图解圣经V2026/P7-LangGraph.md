# Q01 什么是 LangGraph？与 LangChain 的关系

## 🎤 30秒回答版

这道题考察LangGraph工作流，建议先明确状态机概念和节点设计。

## 🎤 1分钟回答版

LangGraph是基于状态机的工作流框架，核心概念包括State、Node、Edge、Condition。支持构建多Agent协作流程。

## 🎤 3分钟深度回答版

**定义**：LangGraph是状态机工作流框架。**核心概念**：State、Node、Edge、Condition、Checkpoint。**特性**：条件路由、持久化、人机交互。**实践**：构建多步骤工作流、多Agent协作。**扩展**：支持异步执行、并行处理、错误重试。**优势**：可视化、可调试、可维护。

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


## Q02 LangGraph 的核心概念

### 2.1 State（状态）

State 是 LangGraph 中最核心的概念。它是一个**贯穿整个图执行过程的共享数据容器**，所有节点都可以读取和更新它。

State 通常使用 `TypedDict` 定义：

```python
from typing import TypedDict, Annotated
from langgraph.graph import add_messages

class AgentState(TypedDict):
    """Agent 的执行状态"""
    messages: Annotated[list, add_messages]  # 消息列表，使用 reducer 合并
    next_action: str                          # 下一步动作
    context: list[str]                        # 检索到的上下文
    iterations: int                           # 迭代次数
```

State 的设计原则：

1. **最小化**：只存储必要的状态信息，避免冗余
2. **类型安全**：使用 TypedDict 或 Pydantic BaseModel 确保类型正确
3. **可合并**：通过 Annotated 标注 Reducer 函数，定义字段的合并策略
4. **不可变性**：节点返回的是状态的**更新**（delta），而不是整个新状态

在执行过程中，State 的生命周期如下：

```
初始状态 ──→ 节点1执行 ──→ 状态更新 ──→ 节点2执行 ──→ 状态更新 ──→ ... ──→ 最终状态
   │              │              │              │
   └── checkpoint └── checkpoint └── checkpoint └── checkpoint
```

每次节点执行前后，LangGraph 都会创建一个检查点（checkpoint），记录当前状态的快照。这使得状态具有**可追溯性**和**可恢复性**。

### 2.2 Node（节点）

节点是图中执行具体计算逻辑的函数单元。每个节点：

- **输入**：当前的 State 对象
- **处理**：执行任意 Python 逻辑（LLM 调用、工具调用、数据处理等）
- **输出**：返回 State 的更新值

```python
def classify_node(state: AgentState) -> dict:
    """分类节点：判断用户意图"""
    messages = state["messages"]
    last_message = messages[-1].content
    
    # 调用 LLM 进行意图分类
    response = llm.invoke([
        SystemMessage(content="你是一个意图分类器..."),
        HumanMessage(content=last_message)
    ])
    
    # 返回状态更新（只返回需要更新的字段）
    return {"next_action": response.content}
```

节点的设计原则：

1. **单一职责**：每个节点只做一件事
2. **幂等性**：相同输入产生相同输出（尽可能）
3. **显式输入输出**：通过 State 类型明确节点的输入输出
4. **可测试性**：节点函数可以独立测试，不需要图的上下文

节点的类型：

- **普通节点**：执行业务逻辑
- **工具节点**：`ToolNode`，专门用于执行工具调用
- **开始节点**：`START`，图的入口
- **结束节点**：`END`，图的出口

### 2.3 Edge（边）

边定义了节点之间的连接关系，决定了执行流从一个节点流向哪个节点。

**普通边（直接连接）**：

```python
# classify 执行完后，无条件跳转到 retrieve
graph.add_edge("classify", "retrieve")
```

**起始边**：

```python
from langgraph.graph import START
graph.add_edge(START, "first_node")  # 等价于 set_entry_point
```

**终止边**：

```python
from langgraph.graph import END
graph.add_edge("last_node", END)  # 等价于 set_finish_point
```

### 2.4 Conditional Edge（条件边）

条件边是 LangGraph 最强大的特性之一。它允许根据**当前状态**动态决定下一步执行哪个节点。

```python
def route_after_classify(state: AgentState) -> str:
    """根据分类结果路由到不同节点"""
    next_action = state["next_action"]
    
    if "查询" in next_action:
        return "retrieve"
    elif "闲聊" in next_action:
        return "chitchat"
    else:
        return "generate"

# 添加条件边
graph.add_conditional_edges(
    "classify",               # 源节点
    route_after_classify,     # 路由函数
    {                         # 路由映射（可选，用于可视化）
        "retrieve": "retrieve",
        "chitchat": "chitchat",
        "generate": "generate"
    }
)
```

条件边的工作原理：

```
                        ┌──────────┐
                        │ classify │
                        └────┬─────┘
                             │
                    ┌────────┴────────┐
                    │  route 函数执行   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ↓              ↓              ↓
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ retrieve │   │ chitchat │   │ generate │
        └──────────┘   └──────────┘   └──────────┘
```

条件边的路由函数必须返回：
- **字符串**：目标节点的名称
- **字符串列表**：多个目标节点（用于并行执行）
- **`Send` 对象**：动态发送状态到目标节点（用于 map-reduce 模式）

### 2.5 Graph（图）

图是所有概念的容器，将 State、Node、Edge 组织成一个完整的执行流程。

```python
from langgraph.graph import StateGraph, START, END

# 1. 创建图，指定状态类型
graph = StateGraph(AgentState)

# 2. 添加节点
graph.add_node("classify", classify_node)
graph.add_node("retrieve", retrieve_node)
graph.add_node("generate", generate_node)

# 3. 添加边
graph.add_edge(START, "classify")
graph.add_conditional_edges("classify", route_after_classify)
graph.add_edge("retrieve", "generate")
graph.add_edge("generate", END)

# 4. 编译图
app = graph.compile()
```

编译（compile）是将图定义转化为可执行对象的过程。编译时会进行以下校验：

1. **连通性检查**：确保从 START 到每个节点都可达
2. **终止性检查**：确保从每个节点都能到达 END（避免死循环）
3. **类型检查**：确保节点的输入输出与 State 类型兼容

编译后的 `app` 对象支持以下调用方式：

```python
# 同步执行
result = app.invoke({"messages": [HumanMessage(content="你好")]})

# 异步执行
result = await app.ainvoke({"messages": [HumanMessage(content="你好")]})

# 流式执行
for event in app.stream({"messages": [HumanMessage(content="你好")]}):
    print(event)
```

**面试加分点**：提到 `CompiledGraph` 的底层实现基于 **Pregel 执行模型**。每个"超步"（superstep）中，所有就绪的节点并行执行，然后通过消息传递更新状态。这意味着 LangGraph 天然支持节点的并行执行（当多个节点没有依赖关系时）。

---

## Q03 LangGraph 的状态管理

### 3.1 TypedDict vs Pydantic BaseModel

LangGraph 支持两种方式定义 State：`TypedDict` 和 Pydantic `BaseModel`。

**TypedDict 方式**：

```python
from typing import TypedDict, Annotated
from langgraph.graph import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    current_step: str
    data: dict
```

**Pydantic BaseModel 方式**：

```python
from pydantic import BaseModel, Field
from typing import Annotated

class AgentState(BaseModel):
    messages: Annotated[list, add_messages] = Field(default_factory=list)
    current_step: str = "init"
    data: dict = Field(default_factory=dict)
```

**核心区别**：

| 维度 | TypedDict | Pydantic BaseModel |
|------|-----------|-------------------|
| **运行时校验** | 无 | 有（自动验证类型） |
| **默认值** | 不支持 | 支持 |
| **序列化** | 原生 dict | 内置序列化/反序列化 |
| **性能** | 更快（无校验开销） | 略慢（校验开销） |
| **IDE 支持** | 类型提示 | 类型提示 + 自动补全 |
| **检查点兼容性** | 完全兼容 | 完全兼容 |
| **适用场景** | 简单状态、性能敏感 | 复杂状态、需要校验 |

**选择建议**：

- **大多数场景用 TypedDict**：LangGraph 官方示例和文档主要使用 TypedDict，社区生态更成熟
- **需要数据校验时用 BaseModel**：当状态中有来自外部的不可信数据时，Pydantic 的校验能力很有价值
- **避免混用**：在一个图中保持一致的选择

```python
# 推荐：使用 TypedDict + Annotated
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import add_messages, StateGraph

class State(TypedDict):
    # messages 使用 add_messages reducer 自动追加
    messages: Annotated[list, add_messages]
    # 自定义字段
    next: str
```

### 3.2 Reducer 函数的作用

Reducer 函数是 LangGraph 状态管理的核心机制。它定义了**当多个节点更新同一个 State 字段时，如何合并这些更新**。

默认情况下（没有 Reducer），State 的更新策略是**覆盖**（replace）：

```python
class State(TypedDict):
    name: str  # 无 Reducer，后续写入直接覆盖
```

```
节点A 返回 {"name": "Alice"}  →  State.name = "Alice"
节点B 返回 {"name": "Bob"}    →  State.name = "Bob"  (覆盖了 Alice)
```

但很多时候我们需要**累积**而非覆盖，比如消息列表。这时就需要 Reducer：

```python
from operator import add
from typing import Annotated

class State(TypedDict):
    # 使用 operator.add 作为 Reducer，新消息追加到列表末尾
    items: Annotated[list, add]
```

```
初始 State.items = []
节点A 返回 {"items": ["a"]}  →  State.items = [] + ["a"] = ["a"]
节点B 返回 {"items": ["b"]}  →  State.items = ["a"] + ["b"] = ["a", "b"]
```

LangGraph 内置了几个常用的 Reducer：

```python
from langgraph.graph import add_messages

class State(TypedDict):
    # add_messages：专门为消息列表设计的 Reducer
    # 支持按 ID 去重、支持 Message 对象的合并
    messages: Annotated[list, add_messages]
```

`add_messages` 与普通 `add` 的区别：

```python
# add_messages 的特殊能力：
# 1. 按消息 ID 去重 —— 同一 ID 的消息不会重复添加
# 2. 支持覆盖 —— 相同 ID 的消息会被更新而非追加
# 3. 类型安全 —— 只接受 BaseMessage 类型

from langchain_core.messages import AIMessage, HumanMessage

# 普通 add：每次都追加
# messages = [HumanMessage("hi"), HumanMessage("hi")]  ← 重复

# add_messages：按 ID 去重
# messages = [HumanMessage("hi")]  ← 自动去重
```

**自定义 Reducer**：

```python
from typing import TypeVar
from langgraph.graph.message import AnyMessage

def reduce_messages(left: list, right: list | str) -> list:
    """自定义消息合并策略"""
    # 如果 right 是字符串，包装为 HumanMessage
    if isinstance(right, str):
        right = [HumanMessage(content=right)]
    # 合并去重
    merged = {msg.id: msg for msg in left}
    for msg in right:
        merged[msg.id] = msg
    return list(merged.values())

class State(TypedDict):
    messages: Annotated[list, reduce_messages]
```

### 3.3 状态的传递和更新机制

理解状态的传递机制对于调试和优化至关重要。

**传递流程**：

```
1. 初始状态 S0 传入图
2. 节点 A 执行，返回更新 ΔA
3. LangGraph 执行状态合并：S1 = merge(S0, ΔA)
4. 检查点记录 S1
5. 节点 B 执行，返回更新 ΔB
6. LangGraph 执行状态合并：S2 = merge(S1, ΔB)
7. ...
```

**合并算法**：

```python
def merge_state(current: dict, update: dict, schema: type) -> dict:
    """状态合并的底层逻辑"""
    result = {}
    for key, value in current.items():
        if key in update:
            # 检查是否有 Reducer
            field_type = schema.__annotations__[key]
            if has_reducer(field_type):
                # 使用 Reducer 合并
                reducer = get_reducer(field_type)
                result[key] = reducer(value, update[key])
            else:
                # 覆盖
                result[key] = update[key]
        else:
            # 未更新，保留原值
            result[key] = value
    return result
```

**并行节点的状态合并**：

当图中存在并行执行的节点时（比如多个检索器同时工作），状态合并变得更加复杂：

```python
class State(TypedDict):
    results: Annotated[list, add]  # 使用 add reducer

# 并行执行
# 节点A 返回 {"results": ["doc1"]}
# 节点B 返回 {"results": ["doc2"]}
# 节点C 返回 {"results": ["doc3"]}
# 合并后：{"results": ["doc1", "doc2", "doc3"]}
```

```
        ┌─→ 节点A ─┐
START ──┼─→ 节点B ─┼──→ 聚合节点 ──→ END
        └─→ 节点C ─┘
```

LangGraph 使用 Fan-out / Fan-in 模式处理并行：

1. **Fan-out**：从一个节点分发到多个并行节点
2. **Fan-in**：等待所有并行节点完成后，使用 Reducer 合并结果

**状态更新的不可变性原则**：

```python
# ❌ 错误：直接修改 state
def bad_node(state: State) -> dict:
    state["messages"].append(HumanMessage(content="bad"))
    return state

# ✅ 正确：返回新的更新
def good_node(state: State) -> dict:
    return {"messages": [HumanMessage(content="good")]}
```

直接修改 state 对象可能导致检查点机制失效或产生不可预期的行为。始终返回更新字典（delta），让 LangGraph 负责合并。

**面试高频追问**：如果多个并行节点同时更新同一个没有 Reducer 的字段会怎样？

答：LangGraph 会抛出 `InvalidUpdateError` 异常。因为没有 Reducer，框架不知道如何合并多个更新——覆盖任何一个都会丢失其他节点的结果。解决方法是为该字段添加合适的 Reducer。

---

## Q04 LangGraph 的图构建模式

### 4.1 线性图（Sequential）

线性图是最简单的模式，节点按顺序依次执行：

```python
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    input: str
    step1_output: str
    step2_output: str
    final_output: str

graph = StateGraph(State)

graph.add_node("step1", lambda s: {"step1_output": process1(s["input"])})
graph.add_node("step2", lambda s: {"step2_output": process2(s["step1_output"])})
graph.add_node("step3", lambda s: {"final_output": process3(s["step2_output"])})

graph.add_edge(START, "step1")
graph.add_edge("step1", "step2")
graph.add_edge("step2", "step3")
graph.add_edge("step3", END)
```

```
START → step1 → step2 → step3 → END
```

**适用场景**：ETL 流水线、文档处理管道、多步 RAG。

### 4.2 分支图（Branching）

分支图根据条件将执行流导向不同路径：

```python
def classify(state: State) -> dict:
    """对输入进行分类"""
    category = llm_classify(state["input"])
    return {"category": category}

def route(state: State) -> str:
    """根据分类结果路由"""
    category = state["category"]
    if category == "technical":
        return "technical_handler"
    elif category == "billing":
        return "billing_handler"
    else:
        return "general_handler"

graph = StateGraph(State)

graph.add_node("classify", classify)
graph.add_node("technical_handler", handle_technical)
graph.add_node("billing_handler", handle_billing)
graph.add_node("general_handler", handle_general)

graph.add_edge(START, "classify")
graph.add_conditional_edges("classify", route)
graph.add_edge("technical_handler", END)
graph.add_edge("billing_handler", END)
graph.add_edge("general_handler", END)
```

```
                  ┌─→ technical_handler ─┐
START → classify ─┼─→ billing_handler ───┼─→ END
                  └─→ general_handler ───┘
```

**Fan-out 并行分支**：当路由函数返回列表时，多个分支并行执行：

```python
def route_parallel(state: State) -> list[str]:
    """同时执行多个处理器"""
    return ["technical_handler", "billing_handler", "general_handler"]
```

### 4.3 循环图（Loop）

循环图是 LangGraph 最强大的模式之一，也是 Agent 的核心运行模式：

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    tool_calls: list

def agent_node(state: AgentState) -> dict:
    """Agent 节点：调用 LLM 决定下一步"""
    response = llm.bind_tools(tools).invoke(state["messages"])
    return {"messages": [response]}

def should_continue(state: AgentState) -> str:
    """判断是否需要继续调用工具"""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"       # 有工具调用，继续执行
    return END               # 无工具调用，结束

graph = StateGraph(AgentState)

graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(tools))

graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue)
graph.add_edge("tools", "agent")  # 工具执行完回到 agent
```

```
START → agent ──→ END
           ↑        ↑
           │        │ (无工具调用)
           │        
           └── tools (有工具调用)
```

**循环的安全性**：LangGraph 提供了多种机制防止无限循环：

```python
# 方法1：设置最大迭代次数
app = graph.compile()
result = app.invoke(input, {"recursion_limit": 10})

# 方法2：在状态中维护迭代计数
class AgentState(TypedDict):
    iterations: int
    # ...

def agent_node(state: AgentState) -> dict:
    if state.get("iterations", 0) >= MAX_ITERATIONS:
        return {"messages": [AIMessage(content="达到最大迭代次数")]}
    return {"messages": [response], "iterations": state.get("iterations", 0) + 1}
```

### 4.4 嵌套图（Subgraph）

当图变得复杂时，可以将子流程抽取为子图：

```python
# 定义子图
def create_retrieval_subgraph():
    """创建检索子图"""
    subgraph = StateGraph(RetrievalState)
    subgraph.add_node("query_rewrite", rewrite_query)
    subgraph.add_node("search", search_docs)
    subgraph.add_node("rerank", rerank_results)
    
    subgraph.add_edge(START, "query_rewrite")
    subgraph.add_edge("query_rewrite", "search")
    subgraph.add_edge("search", "rerank")
    subgraph.add_edge("rerank", END)
    
    return subgraph.compile()

# 在主图中使用子图
main_graph = StateGraph(AgentState)
main_graph.add_node("retrieve", create_retrieval_subgraph())
main_graph.add_node("generate", generate_answer)
# ...
```

子图有两种使用方式：

1. **作为节点**：子图编译后作为一个普通节点添加到主图
2. **共享状态**：子图和主图使用相同或兼容的 State 类型

子图的价值：

- **模块化**：将复杂流程拆分为独立的、可复用的模块
- **团队协作**：不同团队可以并行开发不同的子图
- **独立测试**：子图可以独立测试和验证
- **嵌套深度**：理论上支持任意深度的嵌套，但建议不超过 3 层

```python
# 子图的状态可以与主图不同
class RetrievalState(TypedDict):
    query: str
    documents: list[str]

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    context: list[str]

# 通过 input/output 映射连接不同状态类型的子图
# 主图的 "context" 字段映射到子图的 "query" 字段
# 子图的 "documents" 字段映射回主图的 "context" 字段
```

---

## Q05 LangGraph 中的 Human-in-the-Loop

### 5.1 interrupt_before 和 interrupt_after

Human-in-the-Loop（人机协作）是 LangGraph 的杀手级特性。在企业级应用中，很多场景需要人工审核或干预：

- 敏感操作（如删除数据、发送邮件）前需要人工确认
- 低置信度的决策需要人工判断
- 合规审查需要人工参与

LangGraph 通过 `interrupt` 机制实现人机协作：

```python
from langgraph.checkpoint.memory import MemorySaver

# 创建检查点保存器
checkpointer = MemorySaver()

# 编译图时指定中断点
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["send_email"],  # 在 send_email 节点前中断
    interrupt_after=["draft_reply"],  # 在 draft_reply 节点后中断
)
```

**`interrupt_before`**：在指定节点执行**之前**暂停，等待人工输入

```python
# 执行图
config = {"configurable": {"thread_id": "session-1"}}

# 第一次执行，会在 send_email 前中断
result = app.invoke(input_data, config)

# 检查当前状态
snapshot = app.get_state(config)
print(snapshot.next)  # ("send_email",) —— 显示下一个要执行的节点

# 人工审核后，决定继续执行
app.invoke(None, config)  # 传入 None 表示继续，无需新输入
```

**`interrupt_after`**：在指定节点执行**之后**暂停，允许人工修改结果

```python
# draft_reply 节点执行后中断
result = app.invoke(input_data, config)

# 人工查看草稿，可能需要修改
snapshot = app.get_state(config)
print(snapshot.values["draft"])  # 查看生成的草稿

# 如果需要修改草稿
app.update_state(config, {"draft": "修改后的草稿内容"})

# 继续执行后续流程
app.invoke(None, config)
```

### 5.2 人工审核节点

除了 `interrupt_before/after`，还可以设计专门的**人工审核节点**：

```python
def human_review_node(state: AgentState) -> dict:
    """人工审核节点：在图内部实现人工审核逻辑"""
    # 这个节点通过 interrupt 机制暂停
    # 当用户通过 API 提供审核结果后，节点返回状态更新
    
    # interrupt() 会暂停执行，并将参数传递给调用者
    human_input = interrupt({
        "question": "请审核以下内容：",
        "content": state["draft"],
        "options": ["approve", "reject", "modify"]
    })
    
    # human_input 是用户通过 API 传入的审核结果
    if human_input["decision"] == "approve":
        return {"status": "approved", "reviewer_comment": human_input.get("comment", "")}
    elif human_input["decision"] == "reject":
        return {"status": "rejected", "reviewer_comment": human_input.get("comment", "")}
    else:
        return {"draft": human_input["modified_content"], "status": "needs_review"}
```

`interrupt()` 函数（LangGraph v0.2+）是最新的 API，它允许在节点内部声明中断点，比 `interrupt_before/after` 更灵活：

```python
from langgraph.types import interrupt, Command

def approval_node(state: State) -> dict:
    # interrupt() 会暂停执行，返回值由恢复时的输入决定
    human_decision = interrupt({
        "prompt": "请确认是否执行此操作？",
        "data": state["sensitive_data"]
    })
    
    return {"approved": human_decision["approved"]}
```

恢复执行时使用 `Command`：

```python
# 恢复执行，传入人工输入
from langgraph.types import Command

result = app.invoke(
    Command(resume={"approved": True, "comment": "同意执行"}),
    config
)
```

### 5.3 检查点（Checkpoint）与恢复

检查点是 Human-in-the-Loop 的基础设施。每次节点执行前后，LangGraph 都会创建检查点：

```python
# 检查点的内容
snapshot = app.get_state(config)
# snapshot 包含：
# - values: 当前状态的完整值
# - next: 下一个要执行的节点
# - config: 当前配置
# - metadata: 元数据（如步骤号、时间戳）
# - parent_config: 父检查点的配置（用于时间旅行）
```

**断点续传**的典型工作流程：

```
1. 用户发起请求 → 执行到中断点 → 保存检查点
2. 系统通知人工审核 → 人工查看中间状态
3. 人工做出决策 → 系统恢复执行 → 继续到下一个中断点或完成
4. 如果执行过程中系统崩溃 → 从最近的检查点恢复
```

```python
# 场景：客服系统中的退款审批

# Step 1：Agent 分析退款请求
result = app.invoke(
    {"messages": [HumanMessage(content="我要退款，订单号 12345")]},
    config
)
# 执行到 human_approval 节点时中断

# Step 2：审批人员查看分析结果
snapshot = app.get_state(config)
print(snapshot.values["analysis"])  # Agent 的分析报告
print(snapshot.values["risk_level"])  # 风险等级

# Step 3：审批人员做出决定
if approve:
    app.invoke(Command(resume={"decision": "approve"}), config)
else:
    app.invoke(Command(resume={"decision": "reject", "reason": "超出退款期限"}), config)

# Step 4：系统继续执行，发送退款或拒绝通知
```

---

## Q06 LangGraph 的持久化与检查点

### 6.1 MemorySaver vs SqliteSaver

LangGraph 提供了多种检查点存储后端：

**MemorySaver**（内存存储）：

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
```

- **存储位置**：Python 进程内存
- **持久化**：进程结束后数据丢失
- **性能**：最快（无 I/O 开销）
- **适用场景**：开发测试、不需要持久化的场景
- **并发**：单进程安全

**SqliteSaver**（SQLite 存储）：

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# 方式1：文件存储
checkpointer = SqliteSaver.from_conn_string("checkpoints.db")

# 方式2：内存模式
checkpointer = SqliteSaver.from_conn_string(":memory:")
```

- **存储位置**：SQLite 数据库文件
- **持久化**：进程结束后数据保留
- **性能**：中等（有磁盘 I/O）
- **适用场景**：单机生产环境、需要持久化的场景
- **并发**：支持读并发，写入需要锁

**PostgresSaver**（PostgreSQL 存储）：

```python
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost:5432/langgraph"
)
```

- **存储位置**：PostgreSQL 数据库
- **持久化**：生产级持久化
- **性能**：高（支持索引和查询优化）
- **适用场景**：生产环境、多实例部署
- **并发**：完全支持并发读写

**选择指南**：

```
开发测试 → MemorySaver
单机生产 → SqliteSaver
多机部署 → PostgresSaver
企业级   → PostgresSaver + 备份策略
```

### 6.2 断点续传

断点续传是检查点机制的核心应用场景。当执行中断（人工审核、系统异常、用户主动暂停）后，可以从最近的检查点恢复：

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)

# 配置线程 ID（每个会话唯一）
config = {"configurable": {"thread_id": "user-session-123"}}

# Step 1：开始执行
result = app.invoke({"messages": [HumanMessage(content="分析这份报告")]}, config)

# 系统在 interrupt 点暂停，检查点自动保存

# Step 2：假设进程重启，可以从检查点恢复
# 通过 thread_id 查找之前的检查点
snapshot = app.get_state(config)
print(snapshot.next)  # 显示下一个要执行的节点

# Step 3：恢复执行
result = app.invoke(None, config)  # 传入 None 继续执行
```

**断点续传的实际应用场景**：

1. **长时间运行的任务**：数据分析任务可能运行数小时，中间可以暂停和恢复
2. **分布式系统**：一个实例崩溃后，另一个实例可以从检查点恢复
3. **人工审核流程**：审核可能需要数天，检查点确保状态不丢失
4. **调试和重放**：可以回滚到任意检查点，重新执行

### 6.3 时间旅行（Time Travel）

时间旅行是 LangGraph 的高级特性，允许回溯到历史状态并从任意点重新执行：

```python
# 获取所有检查点历史
history = list(app.get_state_history(config))

for i, snapshot in enumerate(history):
    print(f"Step {i}: {snapshot.metadata['step']}")
    print(f"  Values: {snapshot.values}")
    print(f"  Next: {snapshot.next}")
```

**回滚到历史状态**：

```python
# 假设我们想回滚到第 3 步
target_snapshot = history[3]

# 从第 3 步重新执行
app.update_state(
    config,
    target_snapshot.values,  # 使用历史状态的值
    as_node=target_snapshot.metadata.get("source")  # 从哪个节点重新开始
)
```

**分支探索**（Branching Exploration）：

```python
# 场景：Agent 在第 5 步做了错误决策，我们想从第 4 步开始，选择不同路径

# 1. 获取第 4 步的状态
step4_snapshot = history[4]

# 2. 创建新的分支（使用新的 thread_id）
branch_config = {"configurable": {"thread_id": "user-session-123-branch"}}

# 3. 将第 4 步的状态复制到新分支
app.update_state(branch_config, step4_snapshot.values)

# 4. 从新分支继续执行，但这次用不同的输入
result = app.invoke(
    Command(resume={"alternative_choice": True}),
    branch_config
)
```

时间旅行的应用价值：

- **错误恢复**：发现错误后回滚到正确状态
- **What-if 分析**：在分支上尝试不同的决策路径
- **A/B 测试**：从同一状态出发，比较不同策略的效果
- **调试**：重现问题，逐步检查状态变化

---

## Q07 LangGraph 实现 ReAct Agent

### 7.1 手动构建 ReAct 图

ReAct（Reasoning + Acting）是最经典的 Agent 模式：LLM 先推理（Reasoning），再行动（Acting），观察结果后继续推理，循环往复直到完成任务。

使用 LangGraph 手动构建 ReAct Agent：

```python
from typing import Annotated, TypedDict
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# 1. 定义工具
@tool
def search_web(query: str) -> str:
    """搜索网络获取最新信息"""
    return tavily_search(query)

@tool
def calculator(expression: str) -> str:
    """计算数学表达式"""
    return str(eval(expression))

tools = [search_web, calculator]

# 2. 定义状态
class ReActState(TypedDict):
    messages: Annotated[list, add_messages]

# 3. 定义 Agent 节点
llm = ChatOpenAI(model="gpt-4o").bind_tools(tools)

def agent_node(state: ReActState) -> dict:
    """ReAct Agent 节点：推理 + 决策"""
    messages = state["messages"]
    
    # 添加系统提示
    system_prompt = SystemMessage(content="""你是一个有用的助手。
    使用 ReAct 模式：先思考需要什么信息，然后调用工具获取信息，最后基于信息回答。
    如果已经有足够的信息，直接回答，不需要再调用工具。""")
    
    response = llm.invoke([system_prompt] + messages)
    return {"messages": [response]}

# 4. 定义路由函数
def should_continue(state: ReActState) -> str:
    """判断是否需要继续调用工具"""
    last_message = state["messages"][-1]
    # 如果 LLM 返回了工具调用，去执行工具
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    # 否则结束
    return END

# 5. 构建图
graph = StateGraph(ReActState)
graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(tools))

graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue)
graph.add_edge("tools", "agent")  # 工具执行完回到 agent

app = graph.compile()
```

执行流程：

```
User: "2024年诺贝尔物理学奖得主是谁？他发表了什么论文？论文被引用了多少次？"

第1轮：
  Agent 推理：需要搜索 2024 年诺贝尔物理学奖得主
  → 调用 search_web("2024 Nobel Prize Physics winner")
  → 获得结果："John Hopfield 和 Geoffrey Hinton"

第2轮：
  Agent 推理：已知得主，需要搜索他们的论文
  → 调用 search_web("John Hopfield most cited paper")
  → 调用 search_web("Geoffrey Hinton most cited paper")

第3轮：
  Agent 推理：已有足够的信息
  → 直接生成回答，不调用工具
  → END
```

### 7.2 工具节点的设计

LangGraph 提供了 `ToolNode` 来统一处理工具调用，但在实际项目中往往需要自定义工具节点：

```python
from langgraph.prebuilt import ToolNode

# 方式1：使用内置 ToolNode（推荐）
tool_node = ToolNode(tools)

# 方式2：自定义工具节点
def custom_tool_node(state: ReActState) -> dict:
    """自定义工具节点，添加错误处理和日志"""
    last_message = state["messages"][-1]
    tool_results = []
    
    for tool_call in last_message.tool_calls:
        try:
            # 查找并执行工具
            tool = next(t for t in tools if t.name == tool_call["name"])
            result = tool.invoke(tool_call["args"])
            
            tool_results.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"],
                    name=tool_call["name"]
                )
            )
        except Exception as e:
            # 工具执行失败，返回错误信息让 Agent 决定如何处理
            tool_results.append(
                ToolMessage(
                    content=f"工具执行失败: {type(e).__name__}: {str(e)}",
                    tool_call_id=tool_call["id"],
                    name=tool_call["name"]
                )
            )
    
    return {"messages": tool_results}
```

**工具节点设计的最佳实践**：

1. **错误容错**：工具执行失败不应导致整个图崩溃，而应返回错误信息让 Agent 决定下一步
2. **并行执行**：`ToolNode` 内置支持并行执行多个工具调用
3. **超时控制**：为长时间运行的工具设置超时
4. **重试机制**：对暂时性失败进行自动重试
5. **结果限制**：限制工具返回结果的大小，避免超过 LLM 的上下文窗口

### 7.3 条件路由的实现

条件路由是 ReAct Agent 的关键，它决定了"继续调用工具"还是"生成最终回答"：

```python
from langchain_core.messages import AIMessage

def should_continue(state: ReActState) -> str:
    """核心路由逻辑"""
    last_message = state["messages"][-1]
    
    # 判断1：是否有工具调用
    if isinstance(last_message, AIMessage):
        if last_message.tool_calls:
            return "tools"
    
    # 判断2：是否超过最大轮次
    tool_call_count = sum(
        1 for msg in state["messages"]
        if isinstance(msg, AIMessage) and msg.tool_calls
    )
    if tool_call_count >= MAX_TOOL_CALLS:
        return END  # 强制结束，避免无限循环
    
    return END
```

更复杂的路由逻辑（多 Agent 场景）：

```python
def supervisor_route(state: SupervisorState) -> str:
    """Supervisor 路由：决定将任务分配给哪个 Agent"""
    last_message = state["messages"][-1]
    
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        target = last_message.tool_calls[0]["args"]["next_agent"]
        return target
    
    return END

# 构建多 Agent 图
graph = StateGraph(SupervisorState)
graph.add_node("supervisor", supervisor_node)
graph.add_node("researcher", researcher_agent)
graph.add_node("coder", coder_agent)
graph.add_node("writer", writer_agent)

graph.add_edge(START, "supervisor")
graph.add_conditional_edges("supervisor", supervisor_route, {
    "researcher": "researcher",
    "coder": "coder",
    "writer": "writer",
    END: END
})
# 每个 agent 执行完后回到 supervisor
graph.add_edge("researcher", "supervisor")
graph.add_edge("coder", "supervisor")
graph.add_edge("writer", "supervisor")
```

---

## Q08 LangGraph 实现 Multi-Agent 系统

### 8.1 Supervisor 模式

Supervisor（主管）模式是最常见的多 Agent 协作模式。一个 Supervisor Agent 负责理解任务、分配任务、协调各子 Agent 的执行：

```python
from typing import Annotated, TypedDict, Literal
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.types import Command

# 1. 定义 Supervisor 的路由工具
class RouteToAgent(BaseModel):
    """路由到指定的 Agent"""
    next_agent: Literal["researcher", "analyst", "writer"] = Field(
        description="下一个要执行的 Agent"
    )

# 2. 定义各 Agent 的节点函数
def supervisor_node(state: MessagesState) -> Command[Literal["researcher", "analyst", "writer", "__end__"]]:
    """Supervisor 节点：分析任务并路由到合适的 Agent"""
    messages = [
        SystemMessage(content="""你是一个任务主管。分析当前任务状态，
        决定下一步应该由哪个专家来处理：
        - researcher: 负责信息检索和调研
        - analyst: 负责数据分析和计算
        - writer: 负责文档撰写和润色
        如果任务已经完成，路由到 __end__"""),
    ] + state["messages"]
    
    response = llm.bind_tools([RouteToAgent]).invoke(messages)
    
    if response.tool_calls:
        next_agent = response.tool_calls[0]["args"]["next_agent"]
        return Command(goto=next_agent, update={"messages": [response]})
    
    return Command(goto=END, update={"messages": [response]})

def researcher_node(state: MessagesState) -> Command[Literal["supervisor"]]:
    """研究员节点：执行信息检索"""
    # ... 检索逻辑
    result = retrieval_agent.invoke(state["messages"])
    return Command(
        goto="supervisor",
        update={"messages": [AIMessage(content=result, name="researcher")]}
    )

def analyst_node(state: MessagesState) -> Command[Literal["supervisor"]]:
    """分析师节点：执行数据分析"""
    result = analysis_agent.invoke(state["messages"])
    return Command(
        goto="supervisor",
        update={"messages": [AIMessage(content=result, name="analyst")]}
    )

def writer_node(state: MessagesState) -> Command[Literal["supervisor"]]:
    """撰稿人节点：执行文档撰写"""
    result = writing_agent.invoke(state["messages"])
    return Command(
        goto="supervisor",
        update={"messages": [AIMessage(content=result, name="writer")]}
    )

# 3. 构建图
graph = StateGraph(MessagesState)
graph.add_node("supervisor", supervisor_node)
graph.add_node("researcher", researcher_node)
graph.add_node("analyst", analyst_node)
graph.add_node("writer", writer_node)

graph.add_edge(START, "supervisor")

app = graph.compile()
```

**Supervisor 模式的执行流程**：

```
用户: "分析特斯拉2024年Q3财报，生成研究报告"

Step 1: Supervisor 分析任务
  → 需要先检索财报数据
  → 路由到 researcher

Step 2: Researcher 检索财报数据
  → 返回检索结果
  → 回到 Supervisor

Step 3: Supervisor 分析当前状态
  → 已有数据，需要分析
  → 路由到 analyst

Step 4: Analyst 执行数据分析
  → 返回分析结果
  → 回到 Supervisor

Step 5: Supervisor 分析当前状态
  → 已有分析结果，需要撰写报告
  → 路由到 writer

Step 6: Writer 撰写研究报告
  → 返回报告初稿
  → 回到 Supervisor

Step 7: Supervisor 评估完成度
  → 任务完成
  → 路由到 END
```

### 8.2 Hierarchical 模式

Hierarchical（层级）模式将 Supervisor 组织成多层树状结构，适用于大规模复杂任务：

```python
# 顶层 Supervisor
def top_supervisor(state: State) -> Command:
    """顶层主管：将任务分配给功能域主管"""
    task_type = classify_task(state["messages"][-1])
    
    if task_type == "research":
        return Command(goto="research_supervisor")
    elif task_type == "development":
        return Command(goto="dev_supervisor")
    elif task_type == "operations":
        return Command(goto="ops_supervisor")
    return Command(goto=END)

# 研究域 Supervisor
def research_supervisor(state: State) -> Command:
    """研究域主管：管理研究员、分析师等"""
    # ...

# 开发域 Supervisor
def dev_supervisor(state: State) -> Command:
    """开发域主管：管理前端、后端、测试等"""
    # ...
```

```
                    ┌─────────────────┐
                    │  Top Supervisor  │
                    └────────┬────────┘
              ┌──────────────┼──────────────┐
              ↓              ↓              ↓
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │  Research     │ │  Development │ │  Operations  │
    │  Supervisor   │ │  Supervisor  │ │  Supervisor  │
    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
      ┌────┴────┐     ┌─────┴─────┐    ┌─────┴─────┐
      ↓         ↓     ↓     ↓     ↓    ↓           ↓
  Researcher Analyst Frontend Backend QA  Deploy   Monitor
```

### 8.3 Agent 间通信

多 Agent 系统中，Agent 间通信是核心问题。LangGraph 提供了多种通信机制：

**机制一：共享状态**

```python
class SharedState(TypedDict):
    """所有 Agent 共享的状态"""
    messages: Annotated[list, add_messages]
    research_data: list[str]          # researcher 写入
    analysis_result: dict             # analyst 写入
    draft_document: str               # writer 写入
    feedback: str                     # reviewer 写入
```

所有 Agent 通过读写共享状态进行间接通信。这是最简单也最常用的方式。

**机制二：Command 直接路由**

```python
def researcher_node(state: State) -> Command[Literal["analyst"]]:
    """Researcher 完成后直接路由到 Analyst"""
    data = do_research(state)
    return Command(
        goto="analyst",  # 直接指定下一个 Agent
        update={"research_data": data}
    )
```

**机制三：消息传递**

```python
def researcher_node(state: State) -> dict:
    """通过消息向其他 Agent 传递信息"""
    result = do_research(state)
    # 将结果封装为消息，所有后续节点都可以看到
    return {
        "messages": [
            AIMessage(
                content=f"调研结果：{result}",
                name="researcher"  # 标识消息来源
            )
        ]
    }
```

**通信模式选择**：

| 模式 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 共享状态 | 数据量大、结构化 | 类型安全、清晰 | 状态膨胀 |
| Command 路由 | 明确的执行流 | 简单直接 | 灵活性低 |
| 消息传递 | 对话式协作 | 自然、可追溯 | 消息列表膨胀 |

---

## Q09 LangGraph 的流式输出

### 9.1 Stream Events API

流式输出对于用户体验至关重要——用户不必等待整个 Agent 执行完毕，而是可以实时看到执行进展。

LangGraph 提供了多种流式输出模式：

```python
# 模式1：stream —— 节点级流式输出
for event in app.stream(input_data, config):
    print(event)
    # event 是一个字典，key 是节点名，value 是节点的输出
    # {"agent": {"messages": [AIMessage(...)]}}
    # {"tools": {"messages": [ToolMessage(...)]}}

# 模式2：astream_events —— 细粒度事件流
async for event in app.astream_events(input_data, config, version="v2"):
    if event["event"] == "on_chat_model_stream":
        # Token 级流式输出
        chunk = event["data"]["chunk"]
        print(chunk.content, end="")
```

### 9.2 节点级流式输出

节点级流式输出是最常用的模式，它在每个节点完成时发出事件：

```python
# stream_mode 参数控制输出模式
for event in app.stream(input_data, config, stream_mode="updates"):
    for node_name, node_output in event.items():
        print(f"[{node_name}] 完成")
        print(f"  输出: {node_output}")
```

`stream_mode` 参数：

```python
# "updates"：节点完成后输出更新的状态
for event in app.stream(input_data, config, stream_mode="updates"):
    # {"agent": {"messages": [new_message]}}
    pass

# "values"：节点完成后输出完整的状态
for event in app.stream(input_data, config, stream_mode="values"):
    # {"messages": [all_messages_so_far]}
    pass

# "debug"：输出详细的调试信息
for event in app.stream(input_data, config, stream_mode="debug"):
    # 包含检查点信息、元数据等
    pass

# 多模式组合
for event in app.stream(input_data, config, stream_mode=["updates", "custom"]):
    pass
```

### 9.3 Token 级流式输出

Token 级流式输出让用户实时看到 LLM 生成的文字，体验更好：

```python
from langgraph.graph import StateGraph, MessagesState
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", streaming=True)  # 必须开启 streaming

def agent_node(state: MessagesState):
    """Agent 节点：支持 token 级流式输出"""
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

# 方法1：使用 astream_events
async for event in app.astream_events(input_data, config, version="v2"):
    kind = event["event"]
    
    if kind == "on_chat_model_stream":
        content = event["data"]["chunk"].content
        if content:
            print(content, end="|")
    
    elif kind == "on_tool_start":
        print(f"\n调用工具: {event['name']}")
    
    elif kind == "on_tool_end":
        print(f"\n工具结果: {event['data'].content[:100]}")

# 方法2：使用 stream_mode="messages"（LangGraph v0.2+）
for msg, metadata in app.stream(input_data, config, stream_mode="messages"):
    if msg.content:
        print(msg.content, end="")
```

**流式输出在前端的集成**：

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import json

app_fastapi = FastAPI()

@app_fastapi.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """SSE 流式接口"""
    async def event_generator():
        async for event in graph_app.astream_events(
            {"messages": [HumanMessage(content=request.message)]},
            config={"configurable": {"thread_id": request.session_id}},
            version="v2"
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield f"data: {json.dumps({'content': chunk.content})}\n\n"
            elif event["event"] == "on_tool_start":
                yield f"data: {json.dumps({'type': 'tool_call', 'name': event['name']})}\n\n"
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

## Q10 LangGraph vs Dify vs Coze vs n8n

### 10.1 工作流平台对比

| 维度 | LangGraph | Dify | Coze | n8n |
|------|-----------|------|------|-----|
| **定位** | 开发者框架 | 低代码 AI 平台 | AI Bot 构建平台 | 通用自动化平台 |
| **编程语言** | Python | Python/TypeScript | 配置化 | TypeScript |
| **目标用户** | AI 工程师 | 业务开发者 | 非技术人员 | 自动化工程师 |
| **学习曲线** | 高（需编程） | 中（可视化+少量代码） | 低（拖拽配置） | 中（可视化+少量代码） |
| **灵活性** | 极高 | 中等 | 低 | 高 |
| **AI 能力** | 原生支持 | 深度集成 | 深度集成 | 插件式 |
| **部署方式** | 自部署 | 自部署/SaaS | SaaS | 自部署/SaaS |
| **开源** | 是（MIT） | 是（Apache 2.0） | 否 | 是（Fair Code） |
| **社区生态** | LangChain 生态 | 活跃 | 字节跳动生态 | 活跃 |

### 10.2 适用场景

**LangGraph 适合的场景**：

1. **复杂的 Agent 系统**：需要精细控制执行流程、状态管理、人机协作
2. **多 Agent 协作**：需要 Supervisor、层级等复杂协作模式
3. **需要高度定制**：标准平台无法满足的定制化需求
4. **对性能有要求**：需要精确控制 LLM 调用次数和执行效率
5. **企业级部署**：需要与现有系统深度集成

```python
# LangGraph 的典型使用场景
# 一个复杂的多步骤文档审核流程
graph = StateGraph(ReviewState)
graph.add_node("parse", parse_document)
graph.add_node("classify_risk", classify_risk_level)
graph.add_node("auto_approve", auto_approve_node)
graph.add_node("human_review", human_review_node)
graph.add_node("legal_check", legal_compliance_check)
graph.add_node("notify", notification_node)
# ... 复杂的条件路由和循环
```

**Dify 适合的场景**：

1. **快速原型**：需要快速搭建 AI 应用原型
2. **RAG 应用**：知识库问答、文档对话
3. **简单工作流**：步骤不超过 10 步的线性/分支流程
4. **团队协作**：需要可视化界面让非技术人员参与配置
5. **多模型管理**：需要统一管理多个 LLM 的 API Key

**Coze 适合的场景**：

1. **快速构建 Bot**：面向 C 端的聊天机器人
2. **社交媒体集成**：与飞书、微信等平台集成
3. **插件生态**：利用现成的插件快速扩展能力
4. **非技术团队**：完全没有编程能力的团队

**n8n 适合的场景**：

1. **系统集成**：连接不同的 SaaS 服务和 API
2. **自动化流程**：邮件处理、数据同步、定时任务
3. **非 AI 为主的工作流**：AI 只是流程中的一个环节
4. **已有 n8n 基础设施**：团队已在使用 n8n

### 10.3 技术架构差异

**LangGraph 的技术架构**：

```
┌─────────────────────────────────────────┐
│            LangGraph 应用层              │
│  StateGraph / MessageGraph / CompiledGraph│
├─────────────────────────────────────────┤
│            执行引擎层                     │
│  Pregel 执行模型 / 并行调度 / 检查点      │
├─────────────────────────────────────────┤
│            存储层                        │
│  Memory / SQLite / PostgreSQL           │
├─────────────────────────────────────────┤
│            LangChain 生态                │
│  LLM / Tools / Retrievers / Memory      │
└─────────────────────────────────────────┘
```

核心特点：
- **代码优先**：所有逻辑都在代码中定义，版本可控
- **高度灵活**：可以实现任意复杂的图结构
- **深度集成**：与 LangChain 生态无缝对接

**Dify 的技术架构**：

```
┌─────────────────────────────────────────┐
│            Dify 前端 (React)             │
│  可视化编排 / 工作流画布 / 管理面板       │
├─────────────────────────────────────────┤
│            Dify 后端 (Python/Flask)       │
│  Workflow Engine / Agent Runtime         │
├─────────────────────────────────────────┤
│            基础设施层                     │
│  Celery (任务队列) / Redis / PostgreSQL  │
├─────────────────────────────────────────┤
│            模型适配层                     │
│  OpenAI / Anthropic / 本地模型适配器     │
└─────────────────────────────────────────┘
```

核心特点：
- **可视化优先**：拖拽式编排
- **内置 RAG**：开箱即用的文档处理和检索能力
- **多租户**：支持团队协作和权限管理

**选择建议**：

```
你需要精细控制执行流程？     → LangGraph
你需要快速搭建 AI 应用？     → Dify / Coze
你的团队没有 Python 开发者？  → Coze
你需要连接大量第三方系统？    → n8n
你需要生产级多 Agent 系统？   → LangGraph
```

---

## Q11 LangGraph 的测试与调试

### 11.1 LangSmith 集成

LangSmith 是 LangGraph 的官方可观测性平台，提供 trace、评估、数据集管理等功能。

```python
import os

# 配置 LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-api-key"
os.environ["LANGCHAIN_PROJECT"] = "my-agent-project"

# 之后所有的 LangGraph 执行都会自动被追踪
result = app.invoke(input_data, config)
# 在 LangSmith UI 中可以看到完整的执行 trace
```

**LangSmith 提供的调试能力**：

1. **Trace 查看**：完整的执行链路，包括每个节点的输入输出、耗时、Token 使用量
2. **状态检查**：每个检查点的完整状态快照
3. **错误诊断**：详细的错误堆栈和上下文信息
4. **性能分析**：各节点的执行时间分布、LLM 调用耗时
5. **成本追踪**：Token 使用量和 API 调用费用

```python
# 为节点添加自定义标签
from langsmith import traceable

@traceable(
    name="custom_retrieval",
    tags=["retrieval", "rag"],
    metadata={"version": "v2"}
)
def retrieval_node(state: AgentState) -> dict:
    """带追踪的检索节点"""
    results = vector_store.similarity_search(state["query"])
    return {"documents": results}
```

### 11.2 单元测试策略

LangGraph 的测试策略分为三个层次：

**层次一：节点单元测试**

```python
import pytest
from unittest.mock import Mock, patch

def test_classify_node():
    """测试分类节点"""
    # 准备输入状态
    state = {
        "messages": [HumanMessage(content="我要退款")],
        "category": ""
    }
    
    # 执行节点函数
    result = classify_node(state)
    
    # 验证输出
    assert "category" in result
    assert result["category"] in ["refund", "inquiry", "complaint"]

def test_agent_node_with_mock():
    """使用 Mock 测试 Agent 节点"""
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(
        content="回答",
        tool_calls=[{"name": "search", "args": {"query": "test"}, "id": "1"}]
    )
    
    state = {"messages": [HumanMessage(content="测试问题")]}
    
    with patch("my_agent.llm", mock_llm):
        result = agent_node(state)
    
    assert len(result["messages"]) == 1
    assert result["messages"][0].tool_calls
```

**层次二：图集成测试**

```python
from langgraph.checkpoint.memory import MemorySaver

@pytest.fixture
def test_app():
    """创建用于测试的图应用"""
    checkpointer = MemorySaver()
    graph = build_graph()  # 构建完整的图
    return graph.compile(checkpointer=checkpointer)

def test_simple_conversation(test_app):
    """测试简单对话流程"""
    config = {"configurable": {"thread_id": "test-1"}}
    
    result = test_app.invoke(
        {"messages": [HumanMessage(content="你好")]},
        config
    )
    
    assert len(result["messages"]) >= 2  # 至少有用户消息和 AI 回复
    assert isinstance(result["messages"][-1], AIMessage)

def test_tool_calling_flow(test_app):
    """测试工具调用流程"""
    config = {"configurable": {"thread_id": "test-2"}}
    
    result = test_app.invoke(
        {"messages": [HumanMessage(content="今天天气怎么样？")]},
        config
    )
    
    # 验证工具被调用
    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) >= 1

def test_interrupt_and_resume(test_app):
    """测试中断和恢复"""
    config = {"configurable": {"thread_id": "test-3"}}
    
    # 执行到中断点
    result = test_app.invoke(
        {"messages": [HumanMessage(content="发送邮件给客户")]},
        config
    )
    
    # 验证在正确的位置中断
    snapshot = test_app.get_state(config)
    assert "send_email" in snapshot.next
    
    # 恢复执行
    result = test_app.invoke(None, config)
    assert result["status"] == "email_sent"
```

**层次三：端到端测试**

```python
@pytest.mark.e2e
def test_full_customer_service_flow():
    """端到端测试：完整的客服流程"""
    config = {"configurable": {"thread_id": "e2e-1"}}
    
    # Step 1: 用户提问
    result = app.invoke(
        {"messages": [HumanMessage(content="我的订单 ORD-123 还没收到")]},
        config
    )
    
    # 验证 Agent 正确识别订单号
    assert "ORD-123" in str(result["messages"][-1].content)
    
    # Step 2: 验证工具被正确调用
    snapshot = app.get_state(config)
    assert "order_status" in snapshot.values.get("tool_results", {})
    
    # Step 3: 如果有中断，模拟人工确认
    if snapshot.next:
        result = app.invoke(None, config)
    
    # Step 4: 验证最终回复包含有用信息
    final_message = result["messages"][-1].content
    assert "物流" in final_message or "配送" in final_message
```

### 11.3 常见调试技巧

**技巧一：状态检查法**

```python
# 在任意节点前添加调试节点
def debug_node(state: AgentState) -> dict:
    """调试节点：打印当前状态"""
    import json
    print("=" * 50)
    print("当前状态:")
    for key, value in state.items():
        if key == "messages":
            print(f"  messages ({len(value)} 条):")
            for msg in value[-3:]:  # 只显示最近3条
                print(f"    [{msg.__class__.__name__}] {str(msg.content)[:100]}")
        else:
            print(f"  {key}: {value}")
    print("=" * 50)
    return {}  # 不修改任何状态

graph.add_node("debug", debug_node)
graph.add_edge("node_a", "debug")
graph.add_edge("debug", "node_b")
```

**技巧二：断点调试法**

```python
# 使用 interrupt 在任意点暂停，检查状态
app = graph.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["*"]  # 在每个节点前中断（开发环境使用）
)

# 逐步执行
config = {"configurable": {"thread_id": "debug-session"}}
app.invoke(input_data, config)

while True:
    snapshot = app.get_state(config)
    if not snapshot.next:
        break
    print(f"下一个节点: {snapshot.next}")
    print(f"当前状态: {snapshot.values}")
    input("按 Enter 继续...")
    app.invoke(None, config)
```

**技巧三：LangSmith 回放法**

```python
# 从 LangSmith 获取失败的 trace 进行回放
from langsmith import Client

client = Client()
runs = client.list_runs(
    project_name="my-agent",
    error=True,  # 只看失败的执行
    limit=10
)

for run in runs:
    print(f"Run ID: {run.id}")
    print(f"Error: {run.error}")
    print(f"Inputs: {run.inputs}")
    print(f"Outputs: {run.outputs}")
    
    # 使用相同的输入重新执行
    result = app.invoke(run.inputs, {"configurable": {"thread_id": f"replay-{run.id}"}})
```

**技巧四：日志级别控制**

```python
import logging

# 设置 LangGraph 日志级别
logging.getLogger("langgraph").setLevel(logging.DEBUG)
logging.getLogger("langchain").setLevel(logging.WARNING)  # 减少 LangChain 的噪音

# 结构化日志
import structlog

logger = structlog.get_logger()

def instrumented_node(state: AgentState) -> dict:
    """带日志的节点"""
    logger.info("node_start", node="my_node", input_keys=list(state.keys()))
    
    try:
        result = my_logic(state)
        logger.info("node_end", node="my_node", output_keys=list(result.keys()))
        return result
    except Exception as e:
        logger.error("node_error", node="my_node", error=str(e))
        raise
```

**技巧五：可视化图结构**

```python
# 方法1：Mermaid 图（推荐，在 LangSmith 中自动渲染）
print(app.get_graph().draw_mermaid())

# 方法2：ASCII 图
print(app.get_graph().draw_ascii())

# 方法3：导出为 PNG（需要安装依赖）
# pip install pygraphviz
app.get_graph().draw_png("my_graph.png")
```

---

## Q12 企业级 LangGraph 应用案例

### 12.1 客服工作流

智能客服是 LangGraph 最经典的企业应用场景。一个完整的客服系统需要处理多种意图、调用多种工具、并在关键节点引入人工审核：

```python
from typing import Annotated, TypedDict, Literal
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.types import interrupt, Command
from langgraph.prebuilt import ToolNode

# 1. 定义状态
class CustomerServiceState(TypedDict):
    """客服系统状态"""
    messages: Annotated[list, add_messages]
    customer_id: str
    intent: str                   # 识别的意图
    order_info: dict | None       # 订单信息
    sentiment: str                # 用户情绪
    escalation_level: int         # 升级等级
    resolution: str               # 解决方案

# 2. 定义工具
@tool
def lookup_order(order_id: str) -> dict:
    """查询订单信息"""
    # 调用订单系统 API
    return order_api.get_order(order_id)

@tool
def process_refund(order_id: str, reason: str) -> dict:
    """处理退款"""
    return refund_api.process(order_id, reason)

@tool
def create_ticket(title: str, description: str, priority: str) -> str:
    """创建工单"""
    return ticket_system.create(title, description, priority)

# 3. 定义节点
def intent_classifier(state: CustomerServiceState) -> dict:
    """意图分类节点"""
    llm = ChatOpenAI(model="gpt-4o-mini")
    response = llm.invoke([
        SystemMessage(content="分类用户意图：查询、退款、投诉、建议、其他"),
        state["messages"][-1]
    ])
    return {"intent": response.content}

def sentiment_analyzer(state: CustomerServiceState) -> dict:
    """情绪分析节点"""
    llm = ChatOpenAI(model="gpt-4o-mini")
    response = llm.invoke([
        SystemMessage(content="分析用户情绪：positive/neutral/negative/angry"),
        state["messages"][-1]
    ])
    return {"sentiment": response.content}

def router(state: CustomerServiceState) -> str:
    """路由函数：根据意图和情绪决定下一步"""
    intent = state.get("intent", "other")
    sentiment = state.get("sentiment", "neutral")
    escalation = state.get("escalation_level", 0)
    
    # 情绪极度负面，直接升级到人工
    if sentiment == "angry" and escalation < 2:
        return "escalate_to_human"
    
    # 根据意图路由
    if intent == "查询":
        return "order_lookup"
    elif intent == "退款":
        if sentiment == "negative":
            return "auto_refund"       # 负面情绪自动退款
        return "refund_approval"       # 需要审批
    elif intent == "投诉":
        return "create_ticket"
    else:
        return "general_response"

def refund_approval_node(state: CustomerServiceState) -> dict:
    """退款审批节点（人工审核）"""
    # 使用 interrupt 暂停，等待审批人员
    human_decision = interrupt({
        "type": "refund_approval",
        "order_info": state["order_info"],
        "reason": state["messages"][-1].content,
        "customer_sentiment": state["sentiment"]
    })
    
    if human_decision["approved"]:
        result = process_refund.invoke({
            "order_id": state["order_info"]["id"],
            "reason": human_decision.get("reason", "客户申请")
        })
        return {"resolution": f"退款已处理: {result['refund_id']}"}
    else:
        return {"resolution": human_decision.get("rejection_reason", "退款申请未通过")}

def human_agent_node(state: CustomerServiceState) -> dict:
    """转接人工客服节点"""
    human_response = interrupt({
        "type": "human_handoff",
        "customer_id": state["customer_id"],
        "conversation": state["messages"][-5:],
        "sentiment": state["sentiment"],
        "intent": state["intent"]
    })
    
    return {
        "messages": [AIMessage(content=human_response["response"])],
        "resolution": "已转人工处理"
    }

# 4. 构建图
graph = StateGraph(CustomerServiceState)

graph.add_node("classify_intent", intent_classifier)
graph.add_node("analyze_sentiment", sentiment_analyzer)
graph.add_node("order_lookup", ToolNode([lookup_order]))
graph.add_node("auto_refund", ToolNode([process_refund]))
graph.add_node("refund_approval", refund_approval_node)
graph.add_node("create_ticket", ToolNode([create_ticket]))
graph.add_node("general_response", general_response_node)
graph.add_node("escalate_to_human", human_agent_node)
graph.add_node("generate_reply", generate_reply_node)

graph.add_edge(START, "classify_intent")
graph.add_edge("classify_intent", "analyze_sentiment")
graph.add_conditional_edges("analyze_sentiment", router)
graph.add_edge("order_lookup", "generate_reply")
graph.add_edge("auto_refund", "generate_reply")
graph.add_edge("refund_approval", "generate_reply")
graph.add_edge("create_ticket", "generate_reply")
graph.add_edge("general_response", "generate_reply")
graph.add_edge("escalate_to_human", END)
graph.add_edge("generate_reply", END)

app = graph.compile(
    checkpointer=PostgresSaver.from_conn_string(DB_URL),
    interrupt_before=["refund_approval", "escalate_to_human"]
)
```

**系统架构**：

```
用户消息
   ↓
┌──────────────┐
│ 意图分类      │ → 查询/退款/投诉/其他
└──────┬───────┘
       ↓
┌──────────────┐
│ 情绪分析      │ → positive/neutral/negative/angry
└──────┬───────┘
       ↓
┌──────────────────────────────────────────────┐
│                   路由决策                     │
├──────────┬──────────┬──────────┬──────────────┤
│ 订单查询  │ 自动退款  │ 退款审批  │ 转人工客服   │
└────┬─────┘ └────┬───┘ └────┬───┘ └────┬───────┘
     └───────────┴──────────┴──────────┘
                       ↓
                ┌──────────────┐
                │ 生成回复      │
                └──────────────┘
                       ↓
                   返回用户
```

### 12.2 数据分析 Pipeline

数据分析 Pipeline 是另一个典型的 LangGraph 应用场景。流程包括：需求理解 → 数据获取 → 数据清洗 → 分析 → 可视化 → 报告生成：

```python
class AnalysisState(TypedDict):
    """数据分析状态"""
    messages: Annotated[list, add_messages]
    question: str                 # 用户的分析问题
    data_source: str              # 数据源（数据库、API、文件）
    raw_data: list[dict]          # 原始数据
    cleaned_data: list[dict]      # 清洗后数据
    analysis_result: dict         # 分析结果
    chart_config: dict            # 图表配置
    report: str                   # 最终报告
    sql_query: str                # 生成的 SQL
    error_count: int              # 错误计数

def understand_requirement(state: AnalysisState) -> dict:
    """理解分析需求"""
    llm = ChatOpenAI(model="gpt-4o")
    response = llm.invoke([
        SystemMessage(content="""你是数据分析需求理解专家。
        从用户的问题中提取：
        1. 分析目标
        2. 时间范围
        3. 关键指标
        4. 维度/分组
        输出结构化的分析需求"""),
        state["messages"][-1]
    ])
    return {"question": response.content}

def generate_sql(state: AnalysisState) -> dict:
    """生成 SQL 查询"""
    llm = ChatOpenAI(model="gpt-4o")
    response = llm.invoke([
        SystemMessage(content=f"""根据分析需求生成 SQL 查询。
        数据库表结构：{get_schema_info(state["data_source"])}
        请生成安全、高效的 SQL。"""),
        HumanMessage(content=state["question"])
    ])
    return {"sql_query": response.content}

def execute_query(state: AnalysisState) -> dict:
    """执行查询获取数据"""
    try:
        result = database.execute(state["sql_query"])
        return {"raw_data": result, "error_count": 0}
    except Exception as e:
        return {"raw_data": [], "error_count": state.get("error_count", 0) + 1}

def clean_data(state: AnalysisState) -> dict:
    """数据清洗"""
    df = pd.DataFrame(state["raw_data"])
    
    # 缺失值处理
    df = df.dropna(subset=["key_metric"])
    # 异常值检测
    df = remove_outliers(df, columns=["value"])
    # 数据类型转换
    df["date"] = pd.to_datetime(df["date"])
    
    return {"cleaned_data": df.to_dict("records")}

def analyze(state: AnalysisState) -> dict:
    """执行分析"""
    df = pd.DataFrame(state["cleaned_data"])
    
    analysis = {
        "summary": df.describe().to_dict(),
        "trend": calculate_trend(df),
        "correlation": df.corr().to_dict(),
        "top_items": df.nlargest(10, "value").to_dict("records")
    }
    
    return {"analysis_result": analysis}

def generate_chart(state: AnalysisState) -> dict:
    """生成图表配置"""
    llm = ChatOpenAI(model="gpt-4o")
    response = llm.invoke([
        SystemMessage(content="根据分析结果，生成 ECharts 图表配置 JSON"),
        HumanMessage(content=json.dumps(state["analysis_result"], ensure_ascii=False))
    ])
    return {"chart_config": json.loads(response.content)}

def generate_report(state: AnalysisState) -> dict:
    """生成分析报告"""
    llm = ChatOpenAI(model="gpt-4o")
    response = llm.invoke([
        SystemMessage(content="根据分析结果和图表，生成结构化的数据分析报告"),
        HumanMessage(content=f"""
        分析问题：{state['question']}
        分析结果：{json.dumps(state['analysis_result'], ensure_ascii=False)}
        """)
    ])
    return {"report": response.content}

def check_error(state: AnalysisState) -> str:
    """检查是否有错误需要重试"""
    if state.get("error_count", 0) > 0 and state["error_count"] < 3:
        return "generate_sql"  # 重新生成 SQL
    elif state.get("error_count", 0) >= 3:
        return "error_handler"  # 错误处理
    return "clean_data"

# 构建图
graph = StateGraph(AnalysisState)

graph.add_node("understand", understand_requirement)
graph.add_node("generate_sql", generate_sql)
graph.add_node("execute_query", execute_query)
graph.add_node("clean_data", clean_data)
graph.add_node("analyze", analyze)
graph.add_node("generate_chart", generate_chart)
graph.add_node("generate_report", generate_report)

graph.add_edge(START, "understand")
graph.add_edge("understand", "generate_sql")
graph.add_edge("generate_sql", "execute_query")
graph.add_conditional_edges("execute_query", check_error)
graph.add_edge("clean_data", "analyze")
graph.add_edge("analyze", "generate_chart")
graph.add_edge("generate_chart", "generate_report")
graph.add_edge("generate_report", END)
```

### 12.3 文档审核流程

文档审核是企业合规领域的核心需求，涉及多级审核、法律检查、风险评估等：

```python
class DocumentReviewState(TypedDict):
    """文档审核状态"""
    messages: Annotated[list, add_messages]
    document: str                 # 待审核文档
    document_type: str            # 文档类型
    risk_level: str               # 风险等级: low/medium/high/critical
    review_stages: list[str]      # 需要经过的审核阶段
    current_stage: str            # 当前审核阶段
    review_results: dict          # 各阶段审核结果
    auto_check_passed: bool       # 自动检查是否通过
    final_decision: str           # 最终决定

def parse_document(state: DocumentReviewState) -> dict:
    """解析文档"""
    doc_type = classify_document(state["document"])
    return {"document_type": doc_type}

def auto_compliance_check(state: DocumentReviewState) -> dict:
    """自动合规检查"""
    llm = ChatOpenAI(model="gpt-4o")
    response = llm.invoke([
        SystemMessage(content="""你是合规检查专家。检查文档是否存在以下问题：
        1. 敏感信息泄露（手机号、身份证、银行卡）
        2. 法律风险条款
        3. 数据安全问题
        4. 知识产权问题
        输出检查结果和风险等级"""),
        HumanMessage(content=state["document"][:5000])
    ])
    
    result = parse_review_result(response.content)
    return {
        "risk_level": result["risk_level"],
        "auto_check_passed": result["risk_level"] in ["low"],
        "review_results": {"auto_check": result}
    }

def determine_review_path(state: DocumentReviewState) -> str:
    """确定审核路径"""
    risk = state["risk_level"]
    doc_type = state["document_type"]
    
    if risk == "low" and state["auto_check_passed"]:
        return "auto_approve"
    elif risk == "medium":
        return "manager_review"
    elif risk == "high":
        return "legal_review"
    else:  # critical
        return "committee_review"

def manager_review(state: DocumentReviewState) -> dict:
    """经理审核（人工）"""
    decision = interrupt({
        "type": "manager_review",
        "document_summary": state["document"][:500],
        "risk_level": state["risk_level"],
        "auto_check_result": state["review_results"].get("auto_check", {})
    })
    return {
        "review_results": {**state["review_results"], "manager": decision},
        "final_decision": decision["decision"]
    }

def legal_review(state: DocumentReviewState) -> dict:
    """法务审核（人工）"""
    decision = interrupt({
        "type": "legal_review",
        "document": state["document"],
        "risk_level": state["risk_level"],
        "previous_reviews": state["review_results"]
    })
    return {
        "review_results": {**state["review_results"], "legal": decision},
        "final_decision": decision["decision"]
    }

def committee_review(state: DocumentReviewState) -> dict:
    """委员会审核（多人人工）"""
    # 多人审核，需要全部同意
    decisions = []
    for reviewer in ["legal_head", "ciso", "compliance_officer"]:
        decision = interrupt({
            "type": "committee_review",
            "reviewer": reviewer,
            "document": state["document"],
            "risk_level": state["risk_level"]
        })
        decisions.append(decision)
    
    all_approved = all(d["approved"] for d in decisions)
    return {
        "review_results": {**state["review_results"], "committee": decisions},
        "final_decision": "approved" if all_approved else "rejected"
    }

def send_notification(state: DocumentReviewState) -> dict:
    """发送审核结果通知"""
    notify_stakeholders(
        document_type=state["document_type"],
        decision=state["final_decision"],
        review_results=state["review_results"]
    )
    return {}

# 构建图
graph = StateGraph(DocumentReviewState)

graph.add_node("parse", parse_document)
graph.add_node("auto_check", auto_compliance_check)
graph.add_node("auto_approve", lambda s: {"final_decision": "approved"})
graph.add_node("manager_review", manager_review)
graph.add_node("legal_review", legal_review)
graph.add_node("committee_review", committee_review)
graph.add_node("notify", send_notification)

graph.add_edge(START, "parse")
graph.add_edge("parse", "auto_check")
graph.add_conditional_edges("auto_check", determine_review_path, {
    "auto_approve": "auto_approve",
    "manager_review": "manager_review",
    "legal_review": "legal_review",
    "committee_review": "committee_review"
})
graph.add_edge("auto_approve", "notify")
graph.add_edge("manager_review", "notify")
graph.add_edge("legal_review", "notify")
graph.add_edge("committee_review", "notify")
graph.add_edge("notify", END)

app = graph.compile(
    checkpointer=PostgresSaver.from_conn_string(DB_URL),
    interrupt_before=["manager_review", "legal_review", "committee_review"]
)
```

**文档审核流程图**：

```
文档提交
   ↓
┌──────────────┐
│ 文档解析      │ → 识别文档类型
└──────┬───────┘
       ↓
┌──────────────┐
│ 自动合规检查   │ → 敏感信息/法律风险/数据安全
└──────┬───────┘
       ↓
┌──────────────────────────────────────────────┐
│                   风险评估路由                 │
├──────────┬──────────┬──────────┬──────────────┤
│ 低风险    │ 中风险    │ 高风险    │ 极高风险     │
│ 自动通过  │ 经理审核  │ 法务审核  │ 委员会审核   │
└────┬─────┘ └────┬───┘ └────┬───┘ └────┬───────┘
     └───────────┴──────────┴──────────┘
                       ↓
                ┌──────────────┐
                │ 通知相关方     │
                └──────────────┘
                       ↓
                    审核完成
```

---

# 本章面试重点

## 高频考点总结

| 考点 | 频率 | 核心要点 |
|------|------|---------|
| **LangGraph vs LangChain** | ⭐⭐⭐⭐⭐ | 有状态图 vs 线性链，循环支持，Human-in-the-Loop |
| **State 与 Reducer** | ⭐⭐⭐⭐⭐ | TypedDict 定义，Annotated + Reducer，状态合并机制 |
| **条件边与路由** | ⭐⭐⭐⭐⭐ | conditional_edges，路由函数返回值，Send API |
| **ReAct Agent 构建** | ⭐⭐⭐⭐⭐ | agent → tools 循环，should_continue 路由，ToolNode |
| **Human-in-the-Loop** | ⭐⭐⭐⭐ | interrupt()，Command(resume=)，检查点恢复 |
| **检查点与持久化** | ⭐⭐⭐⭐ | MemorySaver/SqliteSaver/PostgresSaver，thread_id |
| **时间旅行** | ⭐⭐⭐ | get_state_history，update_state，分支探索 |
| **Multi-Agent 模式** | ⭐⭐⭐⭐ | Supervisor 模式，Hierarchical 模式，Command 路由 |
| **流式输出** | ⭐⭐⭐ | stream_mode，astream_events，SSE 集成 |
| **平台对比** | ⭐⭐⭐ | LangGraph vs Dify vs Coze vs n8n 的定位差异 |

## 一页速记版

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph 一页速记                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  核心概念: State + Node + Edge + Graph                       │
│  状态定义: TypedDict + Annotated[类型, Reducer]              │
│  图构建:   StateGraph → add_node → add_edge → compile       │
│                                                             │
│  四种图模式:                                                  │
│  ┌──────────┬──────────┬──────────┬──────────┐              │
│  │ 线性图    │ 分支图    │ 循环图    │ 嵌套图    │              │
│  │ A→B→C   │ A→B/C/D │ A⇄B     │ A→[B→C]  │              │
│  └──────────┴──────────┴──────────┴──────────┘              │
│                                                             │
│  ReAct Agent 模板:                                           │
│  ┌──────┐  tool_calls  ┌──────┐                             │
│  │ agent │ ←────────── │ tools │                             │
│  └──┬───┘              └──────┘                             │
│     │ END                                                   │
│     ↓                                                       │
│  Multi-Agent: Supervisor → [researcher, analyst, writer]    │
│                                                             │
│  Human-in-the-Loop:                                         │
│  - interrupt_before/after: 编译时指定                        │
│  - interrupt(): 节点内部声明中断点                           │
│  - Command(resume=): 恢复执行                                │
│                                                             │
│  检查点: MemorySaver(测试) / SqliteSaver(单机)               │
│         / PostgresSaver(生产)                                │
│                                                             │
│  流式输出:                                                    │
│  - stream(stream_mode="updates") → 节点级                    │
│  - astream_events(version="v2") → Token级                   │
│  - stream(stream_mode="messages") → 消息级                   │
│                                                             │
│  关键 API:                                                   │
│  graph.add_node("name", func)                               │
│  graph.add_edge("a", "b")                                   │
│  graph.add_conditional_edges("a", route_fn)                 │
│  app.invoke(input, config)                                  │
│  app.stream(input, config)                                  │
│  app.get_state(config)                                      │
│  app.update_state(config, values)                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 面试前5分钟冲刺版

**必记 10 个核心知识点**：

1. **LangGraph 是什么**：LangChain 团队的有状态图执行引擎，解决 Chain 无法循环、无状态管理、无人机协作的问题

2. **四大核心概念**：State（共享状态容器）、Node（计算单元）、Edge（连接关系）、Graph（编排容器）

3. **State 定义方式**：`TypedDict` + `Annotated[类型, Reducer]`，Reducer 定义多节点更新同一字段时的合并策略

4. **条件边**：`add_conditional_edges(源节点, 路由函数, 路由映射)`，路由函数返回目标节点名称

5. **ReAct Agent 核心结构**：`START → agent → [tools ↔ agent]* → END`，通过 `should_continue` 判断是否继续

6. **Human-in-the-Loop**：`interrupt()` 暂停 + `Command(resume=)` 恢复，必须配合检查点使用

7. **检查点存储**：MemorySaver（开发）→ SqliteSaver（单机）→ PostgresSaver（生产），`thread_id` 标识会话

8. **Multi-Agent 三种模式**：Supervisor（主管调度）、Hierarchical（层级管理）、共享状态通信

9. **流式输出三种粒度**：节点级 `stream_mode="updates"`、Token 级 `astream_events`、消息级 `stream_mode="messages"`

10. **平台选型**：LangGraph（复杂 Agent）→ Dify（快速原型）→ Coze（C 端 Bot）→ n8n（系统集成）

**面试万能回答框架**：

```
"LangGraph 是 LangChain 生态的图编排引擎，
核心是 StateGraph + 有状态执行 + 条件路由。
它解决了 Chain 的三个痛点：
1) 不支持循环 → LangGraph 原生支持图的循环执行
2) 无状态管理 → 内置 State + Reducer 机制
3) 无人机协作 → interrupt + checkpoint 断点续传

在实际项目中，我用它构建过 [ReAct Agent / Multi-Agent / 客服工作流]，
核心模式是 [agent → tools 循环 / Supervisor 调度 / 条件分支路由]，
通过 [PostgresSaver] 实现生产级持久化，
配合 [LangSmith] 实现全链路可观测性。"
```

---

> **下一章预告**：P8 —— LLM 应用性能优化与生产部署


---

# 🚀 Pro增强版 — P7 LangGraph

## 📄 一页速记版

### 面试前5分钟快速复习

**必背概念TOP5：**
1. State（状态）：TypedDict或Pydantic BaseModel定义的图共享数据结构，所有Node读写同一份State
2. Node（节点）：执行具体逻辑的函数单元，接收State返回更新后的State
3. Edge（边）：节点间的连接关系，支持普通边和条件边（Conditional Edge），实现动态路由
4. Human-in-the-Loop：通过interrupt_before/interrupt_after实现人类审批介入，适合高风险操作
5. Checkpoint（检查点）：PostgresSaver/SqliteSaver持久化图状态，支持时间旅行和故障恢复

**必会对比：**
- LangGraph vs LangChain Chain：Chain是线性流程，Graph是有向图支持循环、分支、并行
- LangGraph vs Dify/Coze：LangGraph是代码级精细控制，Dify/Coze是低代码可视化编排
- StateGraph vs MessageGraph：StateGraph支持自定义复杂状态，MessageGraph仅支持消息列表
- interrupt vs break：interrupt暂停等待人工输入后继续，break终止整个流程

**核心口诀：**
- Graph三要素：State定义数据，Node处理逻辑，Edge决定走向
- 状态图本质：有向图 + 条件边 + 状态共享
- 人工介入：interrupt放Node前，审批后用Command恢复
- 检查点三连：存状态、可回溯、能恢复

---

## ⚡ 面试前5分钟冲刺

**Q: LangGraph是什么？**
30秒答：LangChain团队推出的有状态、可循环的Agent编排框架，用图（State/Node/Edge）替代线性Chain，支持复杂Agent工作流。

**Q: State怎么定义？**
30秒答：用TypedDict或Pydantic BaseModel定义，所有Node共享同一份State，通过Annotated[list, add]实现Reducer自动合并。

**Q: 条件边怎么实现？**
30秒答：在add_conditional_edge中传入路由函数，根据当前State返回字符串决定下一个Node。

**Q: Human-in-the-Loop怎么实现？**
30秒答：compile时设置interrupt_before或interrupt_after，执行到该节点时暂停，人工审批后通过graph.invoke(Command(resume=True))继续。

**Q: 为什么选LangGraph不用Chain？**
30秒答：当Agent需要循环调用工具、多Agent协作、人工审批节点、或复杂条件分支时，Chain的线性模型无法表达，必须用Graph。

**Q: Checkpoint的作用？**
30秒答：持久化图的每一步状态快照，支持：①故障恢复从断点重跑 ②时间旅行查看历史状态 ③Human-in-the-Loop暂停恢复。

---

## 🎯 P7章节适用岗位映射

| 题目 | AI应用开发 | Agent工程师 | AI架构师 | Prompt工程师 | AI平台 |
|------|-----------|------------|---------|-------------|--------|
| State/Node/Edge | ✅ | ✅ | ⬜ | ⬜ | ⬜ |
| 条件路由 | ✅ | ✅ | ⬜ | ⬜ | ⬜ |
| Human-in-the-Loop | ✅ | ✅ | ✅ | ⬜ | ⬜ |
| 检查点持久化 | ⬜ | ✅ | ✅ | ⬜ | ✅ |
| 多Agent编排 | ⬜ | ✅ | ✅ | ⬜ | ⬜ |
| Supervisor模式 | ⬜ | ✅ | ✅ | ⬜ | ⬜ |
| 图调试与可观测性 | ⬜ | ⬜ | ✅ | ⬜ | ✅ |

> ✅ = 高频考察　⬜ = 低频或不考察
