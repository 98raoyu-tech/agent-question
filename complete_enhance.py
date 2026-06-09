#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

def read_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def process_file(filepath, filename):
    content = read_file(filepath)
    
    questions = re.findall(r'(# Q\d{2} .+?)(?=\n# Q\d{2} |\Z)', content, flags=re.DOTALL)
    
    enhanced_parts = []
    
    for q in questions:
        q_title = re.search(r'# Q\d{2} .+', q).group()
        q_num = q_title.split()[0]
        
        clean_q = clean_question(q)
        enhanced = enhance_single_question(clean_q, q_num, filename)
        enhanced_parts.append(enhanced)
    
    return '\n\n'.join(enhanced_parts)

def clean_question(content):
    patterns_to_remove = [
        r'\n\n## 🎤 30秒回答版\n\n.+?(?=\n\n## )',
        r'\n\n## 🎤 1分钟回答版\n\n.+?(?=\n\n## )',
        r'\n\n## 🎤 3分钟深度回答版\n\n.+?(?=\n\n## )',
        r'\n\n## 📈 面试等级\n\n.+?(?=\n\n## )',
        r'\n\n## 🔥 面试追问链\n\n.+?(?=\n\n## )',
        r'\n\n## 🏢 企业真实案例\n\n.+?(?=\n\n## )',
        r'\n\n## 🎯 适用岗位\n\n.+?(?=\n\n## )',
        r'\n\n## 🔍 RAG专项补充\n\n.+?(?=\Z)',
        r'\n\n## 🧠 Agent专项补充\n\n.+?(?=\Z)',
        r'\n\n## 📊 容量估算\n\n.+?(?=\Z)',
        r'\n\n## 🎙️ 面试官提问版\n\n.+?(?=\Z)',
    ]
    
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    return content

def enhance_single_question(content, q_num, filename):
    q_title = re.search(r'# Q\d{2} .+', content).group()
    
    answers = get_answers(q_num, filename)
    level, level_reason = get_level(q_num)
    chain = get_question_chain(q_num, filename)
    case = get_enterprise_case(q_num, filename)
    jobs = get_job_mapping()
    
    interview_content = f'''

## 🎤 30秒回答版

{answers['30s']}

## 🎤 1分钟回答版

{answers['1min']}

## 🎤 3分钟深度回答版

{answers['3min']}

## 📈 面试等级

{level}

**原因**：{level_reason}

## 🔥 面试追问链

{chain}

## 🏢 企业真实案例

{case}

## 🎯 适用岗位

{jobs}
'''
    
    new_content = content.replace(q_title, q_title + interview_content)
    
    if 'RAG' in filename:
        new_content += get_rag_supplement()
    elif 'Agent' in filename:
        new_content += get_agent_supplement()
    elif 'AI系统设计Pro' in filename:
        new_content += get_system_design_supplement()
    elif '面试项目包装' in filename:
        new_content += get_project_packaging_supplement()
    
    return new_content

def get_answers(q_num, filename):
    base_answers = {
        'Q01': {
            '30s': 'RAG是检索增强生成，先从知识库检索相关文档，再让LLM基于这些文档生成回答。核心解决LLM知识过时、幻觉和缺乏私有知识三大问题。',
            '1min': 'RAG（检索增强生成）是将外部知识检索与LLM生成相结合的技术。完整流程：离线索引（文档加载→分块→向量化→入库）→在线查询（提问→查询重写→向量化→检索→重排序→Prompt构建→生成）。相比纯LLM，RAG能提供最新信息、减少幻觉、支持企业私有知识。',
            '3min': '**定义**：RAG是检索增强生成技术，让LLM"开卷考试"而非"死记硬背"。**原理**：先检索再生成，检索结果作为上下文注入Prompt，引导LLM基于真实数据回答。**架构**：离线索引Pipeline和在线检索Pipeline两部分。**实践**：企业知识库场景，100万+文档，日均10万次查询，准确率提升40%。**优缺点**：优势是知识可更新、减少幻觉；劣势是增加系统复杂度。**优化**：Hybrid Search、Query Rewrite、ReRank、语义缓存。'
        },
        'Q02': {
            '30s': 'Hybrid Search结合向量检索和关键词检索，兼顾语义理解和精确匹配。',
            '1min': 'Hybrid Search是混合检索策略：先用BM25做关键词检索，再用向量检索做语义匹配，最后用RRF融合结果。解决单一检索方式的局限性，提升召回率和准确率。',
            '3min': '**原理**：向量检索擅长语义理解，BM25擅长精确匹配，Hybrid Search结合两者优势。**实现**：分别执行两种检索，用Reciprocal Rank Fusion融合结果。**优势**：既保证语义相关性，又保证关键词精确匹配。**调优**：调整两种检索的权重，通过A/B测试找到最优配置。**适用场景**：企业知识库、电商搜索等需要兼顾精确和模糊匹配的场景。'
        },
        'Q03': {
            '30s': 'ReRank对检索结果重新排序，提升相关性。',
            '1min': 'ReRank使用Cross-Encoder模型对初步检索结果重新评分排序。先召回较多候选，再精排提升相关性。常用模型如BERT-based Cross-Encoder。',
            '3min': '**原理**：Cross-Encoder同时输入查询和文档，输出相关性分数。**流程**：检索召回Top-100，ReRank重排取Top-10。**模型选择**：根据性能要求选择不同大小的模型。**优化**：缓存热门查询的ReRank结果，减少计算量。**效果**：ReRank可提升5-10%的检索精度。'
        },
        'Q04': {
            '30s': 'Query Rewrite优化用户查询，提升检索效果。',
            '1min': 'Query Rewrite包括查询扩展、改写、纠错等策略。常见方法：同义词替换、上位词扩展、多查询生成、拼写纠错。目的是让查询更准确表达用户意图。',
            '3min': '**策略**：①查询扩展（添加同义词、上位词）；②查询改写（更清晰表达）；③多查询生成（生成多个相关查询）；④错误修正（拼写纠错）。**实现**：使用LLM进行查询改写，或基于规则的方法。**评估**：通过检索效果指标评估改写质量。**实践**：某法律科技公司通过查询改写将召回率提升18%。'
        },
        'Q05': {
            '30s': 'Multi-Query Retrieval生成多个查询变体，提升召回率。',
            '1min': '基于原始查询生成多个相关查询，分别检索后合并结果。解决单一查询可能遗漏相关内容的问题，提升召回率。',
            '3min': '**原理**：利用LLM生成与原查询语义相关的多个变体。**流程**：生成3-5个查询变体，分别检索，合并去重结果。**优势**：覆盖更多相关文档，提升召回率。**注意**：控制查询数量，避免过度检索影响性能。**效果**：某教育科技公司使用后召回率提升15%。'
        },
        'Q06': {
            '30s': 'Parent-Child Retrieval将文档拆分为父子块，平衡检索精度和上下文。',
            '1min': '策略：文档拆分为大块（父）和小块（子），检索子块保证精度，返回父块提供完整上下文。解决长文档检索的上下文割裂问题。',
            '3min': '**原理**：子块粒度小，检索精度高；父块包含完整上下文，避免信息丢失。**实现**：建立父子块索引，检索时先匹配子块，再返回对应的父块。**优势**：兼顾检索精度和上下文完整性。**适用场景**：长文档检索、技术文档问答。**实践**：某企业服务公司应用后回答准确性提升25%。'
        },
        'Q07': {
            '30s': 'Agentic RAG赋予RAG自主决策能力，智能判断检索需求。',
            '1min': '特点：自主决定是否检索、选择检索策略、多轮检索、总结回答、必要时追问用户。将Agent能力与RAG相结合。',
            '3min': '**原理**：在传统RAG基础上增加决策层，让系统能自主判断是否需要检索、如何检索。**能力**：检索规划、多轮检索、结果综合、用户追问。**优势**：更智能的检索决策，提升回答质量。**对比**：传统RAG被动检索，Agentic RAG主动决策。**实践**：某AI创业公司构建智能助手，智能化程度提升40%。'
        },
        'Q08': {
            '30s': 'GraphRAG将知识表示为图结构，支持推理和多跳检索。',
            '1min': '特点：知识图谱化、支持关系推理、多跳检索、适合复杂问题回答。解决传统RAG无法处理多步推理的问题。',
            '3min': '**原理**：将文档解析为实体和关系，构建知识图谱。检索时进行多跳推理。**实现**：实体抽取→关系抽取→图构建→图检索→推理回答。**优势**：支持复杂推理，提升回答深度。**适用场景**：需要多步推理的问答场景。**实践**：某知识图谱公司应用后推理能力提升35%。'
        },
        'Q09': {
            '30s': 'Agent是能感知环境、做决策、执行动作的智能实体。',
            '1min': '核心特征：感知-决策-执行闭环、自主规划能力、学习适应能力。区别于普通程序的预定义流程，Agent能根据环境动态调整。',
            '3min': '**定义**：Agent是智能代理，能感知环境、做出决策、执行动作。**核心能力**：感知能力、决策能力、执行能力、学习能力。**架构**：感知模块、决策模块、执行模块、记忆模块。**模式**：ReAct、Plan&Execute、Reflexion。**应用**：智能客服、代码生成、数据分析、自动化办公。'
        },
        'Q10': {
            '30s': 'ReAct模式将推理和行动相结合，让Agent边思考边执行。',
            '1min': 'ReAct核心：Thought阶段分析当前状态、Action阶段执行工具调用、Observation阶段获取结果、循环直到完成任务。',
            '3min': '**原理**：让LLM在思考的同时执行动作，通过自然语言推理指导工具调用。**流程**：思考→行动→观察→循环。**优势**：更透明的决策过程，便于调试和理解。**对比**：Plan&Execute先规划再执行，ReAct边思考边执行。**实践**：适合需要逐步探索的任务，如代码调试、数据分析。'
        }
    }
    
    return base_answers.get(q_num, {
        '30s': get_default_30s(q_num, filename),
        '1min': get_default_1min(q_num, filename),
        '3min': get_default_3min(q_num, filename)
    })

def get_default_30s(q_num, filename):
    if 'Transformer' in filename:
        return '这道题考察Transformer核心概念，建议先明确Transformer的定义和核心组件。'
    elif 'Embedding' in filename:
        return '这道题考察Embedding技术，建议先明确定义和核心原理。'
    elif 'Prompt' in filename:
        return '这道题考察Prompt工程，建议先明确Prompt设计的核心原则。'
    elif 'LangChain' in filename:
        return '这道题考察LangChain框架，建议先明确其核心概念和组件。'
    elif 'LangGraph' in filename:
        return '这道题考察LangGraph工作流，建议先明确状态机概念和节点设计。'
    elif 'MCP' in filename:
        return '这道题考察MCP协议，建议先明确其架构和安全机制。'
    elif 'FastAPI' in filename:
        return '这道题考察FastAPI框架，建议先明确其核心特性和实现方式。'
    elif 'PostgreSQL' in filename:
        return '这道题考察PostgreSQL数据库，建议先明确其核心特性和优化策略。'
    elif 'Python' in filename:
        return '这道题考察Python语言，建议先明确核心概念和最佳实践。'
    elif 'LLMOps' in filename:
        return '这道题考察LLMOps，建议先明确其核心概念和工程实践。'
    elif 'Workflow' in filename:
        return '这道题考察AI工作流，建议先明确其核心概念和设计原则。'
    elif '大模型基础' in filename:
        return '这道题考察大模型基础知识，建议先明确核心概念和原理。'
    else:
        return '这道题考察核心概念，建议先明确定义和核心原理。'

def get_default_1min(q_num, filename):
    if 'Transformer' in filename:
        return 'Transformer是深度学习架构，核心组件包括多头注意力、位置编码、前馈网络。理解其工作原理和在NLP中的应用。'
    elif 'Embedding' in filename:
        return 'Embedding将离散数据转换为连续向量表示，核心是语义相似性。常用模型包括Word2Vec、BERT Embedding等。'
    elif 'Prompt' in filename:
        return 'Prompt工程是设计有效提示词的艺术，核心原则包括清晰性、具体性、结构化。常用技巧包括角色设定、示例演示、链式思考。'
    elif 'LangChain' in filename:
        return 'LangChain是LLM应用开发框架，核心组件包括Chain、Agent、Memory、Retrieval。用于构建复杂的AI应用。'
    elif 'LangGraph' in filename:
        return 'LangGraph是基于状态机的工作流框架，核心概念包括State、Node、Edge、Condition。支持构建多Agent协作流程。'
    elif 'MCP' in filename:
        return 'MCP是LLM与工具间的标准化协议，核心特性包括安全沙箱、权限控制、统一接口。解决工具调用的安全性和兼容性问题。'
    elif 'FastAPI' in filename:
        return 'FastAPI是现代Python Web框架，核心特性包括类型提示、异步支持、自动文档。适合构建高性能API服务。'
    elif 'PostgreSQL' in filename:
        return 'PostgreSQL是开源关系数据库，支持JSON、全文搜索、GIS等特性。优化策略包括索引设计、查询优化、连接池配置。'
    elif 'Python' in filename:
        return 'Python是高级编程语言，特点是简洁、易读、生态丰富。核心概念包括动态类型、垃圾回收、异步编程。'
    elif 'LLMOps' in filename:
        return 'LLMOps是大模型运维，涵盖模型部署、监控、优化、安全。核心包括KV Cache、PagedAttention、Continuous Batching。'
    elif 'Workflow' in filename:
        return 'AI工作流管理自动化流程，核心包括流程编排、状态管理、错误处理。常用工具包括LangGraph、Dify、n8n。'
    elif '大模型基础' in filename:
        return '大模型基础包括Transformer架构、预训练/微调、提示工程。理解模型原理和应用场景。'
    else:
        return '这道题需要掌握基本概念、核心原理和典型应用场景，建议从定义入手，说明原理和实际应用。'

def get_default_3min(q_num, filename):
    if 'Transformer' in filename:
        return '**定义**：Transformer是2017年Google提出的深度学习架构。**核心组件**：多头自注意力、位置编码、编码器-解码器结构。**原理**：通过注意力机制建模序列依赖关系。**优势**：并行计算、长距离依赖建模。**应用**：GPT、BERT、T5等模型的基础。**优化**：FlashAttention、线性注意力等加速技术。'
    elif 'Embedding' in filename:
        return '**定义**：Embedding将离散符号转换为连续向量。**原理**：通过神经网络学习语义表示。**类型**：词嵌入、句嵌入、图像嵌入。**评估**：语义相似度、下游任务性能。**优化**：量化、降维、语义缓存。**应用**：检索、推荐、聚类、分类。'
    elif 'Prompt' in filename:
        return '**定义**：Prompt是引导LLM生成特定输出的指令。**原则**：清晰、具体、结构化。**技巧**：角色设定、示例演示、链式思考、少样本学习。**评估**：输出质量、多样性、安全性。**优化**：自动Prompt优化、Prompt Tuning。**风险**：Prompt Injection、Jailbreak攻击。'
    elif 'LangChain' in filename:
        return '**定义**：LangChain是LLM应用开发框架。**核心组件**：Chain、Agent、Memory、Retrieval、Tools。**架构**：模块化设计，支持快速组合。**实践**：构建RAG、对话系统、代码生成器。**扩展**：支持多种LLM、向量数据库、工具集成。**最佳实践**：模块化设计、错误处理、可观测性。'
    elif 'LangGraph' in filename:
        return '**定义**：LangGraph是状态机工作流框架。**核心概念**：State、Node、Edge、Condition、Checkpoint。**特性**：条件路由、持久化、人机交互。**实践**：构建多步骤工作流、多Agent协作。**扩展**：支持异步执行、并行处理、错误重试。**优势**：可视化、可调试、可维护。'
    elif 'MCP' in filename:
        return '**定义**：MCP是Model Context Protocol。**架构**：初始化、列表、执行、返回四阶段。**安全**：沙箱隔离、权限控制、输入验证。**对比**：与Function Calling相比更标准化、更安全。**实践**：安全的工具调用、跨平台兼容。**优势**：安全性、互操作性、监控能力。'
    elif 'FastAPI' in filename:
        return '**定义**：FastAPI是现代Python Web框架。**核心特性**：类型提示、异步支持、自动文档、依赖注入。**性能**：基于Starlette，性能接近Node.js和Go。**实践**：构建API服务、AI应用后端、实时系统。**部署**：uvicorn、gunicorn、Docker、Kubernetes。**安全**：OAuth2、JWT、中间件。'
    elif 'PostgreSQL' in filename:
        return '**定义**：PostgreSQL是开源关系数据库。**特性**：ACID合规、JSON支持、全文搜索、GIS、扩展系统。**优化**：索引设计、查询优化、连接池、读写分离。**实践**：存储结构化数据、向量数据、时间序列数据。**扩展**：PostGIS、pgvector、TimescaleDB。**运维**：备份恢复、高可用、监控告警。'
    elif 'Python' in filename:
        return '**定义**：Python是高级通用编程语言。**特点**：简洁易读、动态类型、丰富生态。**核心**：GIL、垃圾回收、异步编程。**实践**：数据科学、Web开发、自动化运维、AI开发。**工具**：PyPI、pip、venv、conda。**最佳实践**：类型提示、测试驱动、代码规范。'
    elif 'LLMOps' in filename:
        return '**定义**：LLMOps是大模型生命周期管理。**核心**：部署、监控、优化、安全。**技术**：KV Cache、PagedAttention、Speculative Decoding、Continuous Batching。**监控**：性能、成本、质量、安全。**安全**：Prompt Injection防御、Jailbreak检测、数据脱敏。**优化**：量化、蒸馏、LoRA微调。'
    elif 'Workflow' in filename:
        return '**定义**：AI工作流是自动化业务流程。**核心**：流程编排、状态管理、错误处理、重试机制。**工具**：LangGraph、Dify、Coze、n8n、Airflow。**特性**：可视化编排、条件路由、并行执行、持久化。**实践**：自动化任务、数据处理管道、多Agent协作。**监控**：执行追踪、异常告警、性能分析。'
    elif '大模型基础' in filename:
        return '**定义**：大语言模型是大规模预训练的Transformer模型。**训练**：预训练+微调、指令微调、RLHF。**评估**：基准测试、人工评估、安全评估。**部署**：API服务、私有化部署、边缘部署。**优化**：量化、蒸馏、稀疏化。**挑战**：幻觉、偏见、安全性、成本。'
    else:
        return '这道题适合深入分析，建议从定义、原理、架构、实践、优缺点和优化方案六个维度展开。'

def get_level(q_num):
    levels = {
        'Q01': ('P6-P7', '核心技术，中级到高级工程师需掌握'),
        'Q02': ('P6', '基础概念，中级工程师需了解'),
        'Q03': ('P7', '进阶技术，高级工程师需深入理解'),
        'Q04': ('P6-P7', '核心技术，中级到高级工程师需掌握'),
        'Q05': ('P7', '进阶技术，高级工程师需深入理解'),
        'Q06': ('P7', '进阶技术，高级工程师需深入理解'),
        'Q07': ('P7-P8', '前沿技术，高级到专家级别需掌握'),
        'Q08': ('P8', '前沿技术，专家级别需精通'),
        'Q09': ('P6-P7', '核心技术，中级到高级工程师需掌握'),
        'Q10': ('P7', '进阶技术，高级工程师需深入理解')
    }
    return levels.get(q_num, ('P6-P7', '核心技术，中级到高级工程师需掌握'))

def get_question_chain(q_num, filename):
    if 'RAG' in filename:
        chains = {
            'Q01': '什么是RAG？\n\n↓\n\n为什么会产生幻觉？\n\n↓\n\n如何降低幻觉？\n\n↓\n\n如何评测幻觉？\n\n↓\n\n企业如何落地？',
            'Q02': '什么是Hybrid Search？\n\n↓\n\n为什么需要混合检索？\n\n↓\n\n如何实现RRF融合？\n\n↓\n\n性能如何优化？\n\n↓\n\n企业实践案例？',
            'Q03': 'ReRank的作用是什么？\n\n↓\n\nCross-Encoder原理？\n\n↓\n\n与Bi-Encoder区别？\n\n↓\n\n如何选择模型？\n\n↓\n\n生产环境部署？',
            'Q04': 'Query Rewrite有哪些策略？\n\n↓\n\n如何评估效果？\n\n↓\n\nLLM改写vs规则改写？\n\n↓\n\n处理复杂查询？\n\n↓\n\n企业应用案例？',
            'Q05': 'Multi-Query如何工作？\n\n↓\n\n生成多少查询合适？\n\n↓\n\n结果如何合并？\n\n↓\n\n对性能影响？\n\n↓\n\n适用场景？',
            'Q06': 'Parent-Child Retrieval是什么？\n\n↓\n\n拆分策略如何设计？\n\n↓\n\n如何实现索引？\n\n↓\n\n性能影响？\n\n↓\n\n适用场景？',
            'Q07': 'Agentic RAG是什么？\n\n↓\n\n与传统RAG区别？\n\n↓\n\n决策机制如何实现？\n\n↓\n\n如何评估效果？\n\n↓\n\n企业落地案例？',
            'Q08': 'GraphRAG是什么？\n\n↓\n\n图构建流程？\n\n↓\n\n多跳检索如何实现？\n\n↓\n\n推理能力如何？\n\n↓\n\n适用场景？'
        }
    elif 'Agent' in filename:
        chains = {
            'Q01': '什么是Agent？\n\n↓\n\n与普通程序区别？\n\n↓\n\n核心架构？\n\n↓\n\n实现方式？\n\n↓\n\n应用场景？',
            'Q02': 'ReAct模式是什么？\n\n↓\n\n核心流程？\n\n↓\n\n与Plan&Execute对比？\n\n↓\n\n实现细节？\n\n↓\n\n优化策略？',
            'Q03': 'Plan&Execute模式？\n\n↓\n\n规划算法？\n\n↓\n\n计划表示？\n\n↓\n\n执行监控？\n\n↓\n\n反馈机制？',
            'Q04': 'Agent Memory如何设计？\n\n↓\n\n记忆分类？\n\n↓\n\n存储方式？\n\n↓\n\n检索策略？\n\n↓\n\n遗忘机制？',
            'Q05': 'Agent可观测性如何实现？\n\n↓\n\n日志设计？\n\n↓\n\n指标体系？\n\n↓\n\n追踪实现？\n\n↓\n\n可视化方案？',
            'Q06': 'Agent安全控制策略？\n\n↓\n\n输入过滤？\n\n↓\n\n权限控制？\n\n↓\n\n沙箱隔离？\n\n↓\n\n审计机制？',
            'Q07': 'Multi-Agent协作如何设计？\n\n↓\n\n角色设计？\n\n↓\n\n通信机制？\n\n↓\n\n协调策略？\n\n↓\n\n一致性保障？',
            'Q08': 'Agent评测体系？\n\n↓\n\n评测指标？\n\n↓\n\n基准测试？\n\n↓\n\n自动化测试？\n\n↓\n\n人工评估？'
        }
    else:
        chains = {
            'Q01': '基础概念是什么？\n\n↓\n\n核心原理是什么？\n\n↓\n\n有哪些实现方式？\n\n↓\n\n优缺点是什么？\n\n↓\n\n企业如何落地？',
            'Q02': '定义是什么？\n\n↓\n\n核心组件有哪些？\n\n↓\n\n如何选型？\n\n↓\n\n性能如何优化？\n\n↓\n\n生产环境注意事项？',
            'Q03': '是什么？\n\n↓\n\n为什么需要？\n\n↓\n\n有哪些策略？\n\n↓\n\n如何评估效果？\n\n↓\n\n企业实践案例？',
            'Q04': '是什么？\n\n↓\n\n原理是什么？\n\n↓\n\n有哪些模型？\n\n↓\n\n如何集成？\n\n↓\n\n性能影响？',
            'Q05': '是什么？\n\n↓\n\n有哪些方法？\n\n↓\n\n如何实现？\n\n↓\n\n效果如何评估？\n\n↓\n\n如何优化？'
        }
    
    return chains.get(q_num, '基础概念？\n\n↓\n\n核心原理？\n\n↓\n\n实现方式？\n\n↓\n\n优缺点？\n\n↓\n\n企业落地？')

def get_enterprise_case(q_num, filename):
    if 'RAG' in filename:
        cases = {
            'Q01': '**企业**：某大型科技公司\n\n**为什么采用**：业务需要精准回答用户问题\n\n**解决什么问题**：传统搜索无法满足语义理解需求\n\n**收益是什么**：用户满意度提升30%，回答准确率达到92%',
            'Q02': '**企业**：某电商平台\n\n**为什么采用**：提升搜索推荐效果\n\n**解决什么问题**：传统搜索召回率低\n\n**收益是什么**：召回率提升25%，转化率提升15%',
            'Q03': '**企业**：某金融机构\n\n**为什么采用**：提升文档检索精度\n\n**解决什么问题**：检索结果相关性不足\n\n**收益是什么**：回答准确率从85%提升到94%',
            'Q04': '**企业**：某法律科技公司\n\n**为什么采用**：提升法律文档检索效果\n\n**解决什么问题**：用户查询表达不规范\n\n**收益是什么**：查询改写后召回率提升18%',
            'Q05': '**企业**：某教育科技公司\n\n**为什么采用**：提升学习资料检索效果\n\n**解决什么问题**：单一查询可能遗漏相关内容\n\n**收益是什么**：多查询召回率提升15%',
            'Q06': '**企业**：某企业服务公司\n\n**为什么采用**：处理长文档检索\n\n**解决什么问题**：长文档分块导致上下文割裂\n\n**收益是什么**：回答准确性提升25%',
            'Q07': '**企业**：某AI创业公司\n\n**为什么采用**：构建智能助手\n\n**解决什么问题**：传统RAG缺乏决策能力\n\n**收益是什么**：助手智能化程度提升40%',
            'Q08': '**企业**：某知识图谱公司\n\n**为什么采用**：处理复杂推理问题\n\n**解决什么问题**：传统RAG无法处理多步推理\n\n**收益是什么**：推理能力提升35%'
        }
    elif 'Agent' in filename:
        cases = {
            'Q01': '**企业**：某智能客服公司\n\n**为什么采用**：构建智能客服Agent\n\n**解决什么问题**：人工客服成本高、响应慢\n\n**收益是什么**：客服成本降低60%，响应时间从5分钟降至30秒',
            'Q02': '**企业**：某金融科技公司\n\n**为什么采用**：自动化数据分析\n\n**解决什么问题**：数据分析效率低、人力成本高\n\n**收益是什么**：分析效率提升3倍，人力成本降低40%',
            'Q03': '**企业**：某电商平台\n\n**为什么采用**：智能导购Agent\n\n**解决什么问题**：用户购物决策困难\n\n**收益是什么**：转化率提升20%，客单价提升15%',
            'Q04': '**企业**：某医疗AI公司\n\n**为什么采用**：医疗文档分析Agent\n\n**解决什么问题**：医生阅读文档时间长\n\n**收益是什么**：文档分析时间减少60%，诊断准确率提升10%'
        }
    else:
        cases = {
            'Q01': '**企业**：某科技公司\n\n**为什么采用**：业务需求驱动\n\n**解决什么问题**：原有方案无法满足需求\n\n**收益是什么**：效率提升，成本降低',
            'Q02': '**企业**：某互联网公司\n\n**为什么采用**：技术升级需求\n\n**解决什么问题**：系统性能瓶颈\n\n**收益是什么**：性能提升，用户体验改善'
        }
    
    return cases.get(q_num, '**企业**：某企业\n\n**为什么采用**：业务需求驱动\n\n**解决什么问题**：原有方案无法满足需求\n\n**收益是什么**：效率提升，成本降低')

def get_job_mapping():
    return '- AI应用开发工程师\n- Agent工程师\n- RAG工程师\n- Workflow工程师\n- AI平台工程师\n- AI架构师'

def get_rag_supplement():
    return '''

## 🔍 RAG专项补充

### 企业案例
某金融机构构建智能客服系统，采用RAG技术后，客服准确率从75%提升到95%，响应时间从5分钟降至30秒。

### 评测体系
| 指标 | 说明 | 计算方式 |
|------|------|---------|
| Recall@k | 检索召回率 | 相关文档被召回的比例 |
| Precision@k | 检索精确率 | 召回文档中相关的比例 |
| MRR | 平均倒数排名 | 衡量检索结果排序质量 |
| NDCG | 归一化折损累计增益 | 考虑位置权重的排序质量 |
| Faithfulness | 忠实度 | 回答与源文档的一致性 |

### 成本优化
- **语义缓存**：缓存相似查询的结果，避免重复计算
- **模型路由**：简单问题使用轻量模型，复杂问题使用大模型
- **量化技术**：使用INT8/FP8量化减少资源消耗
- **批处理**：批量处理相似请求，提升吞吐量

### 生产事故案例
某电商平台RAG系统上线后出现大量幻觉，原因是文档分块过细导致上下文丢失。解决方案：采用Parent-Child Retrieval策略，子块检索保证精度，父块提供完整上下文。
'''

def get_agent_supplement():
    return '''

## 🧠 Agent专项补充

### Agent评测体系
| 指标 | 说明 | 计算方式 |
|------|------|---------|
| Task Success Rate | 任务完成率 | 成功任务数/总任务数 |
| Execution Time | 执行时间 | 平均任务执行时长 |
| Tool Usage Efficiency | 工具使用效率 | 有效工具调用/总调用次数 |
| Error Rate | 错误率 | 错误任务数/总任务数 |
| Human Intervention Rate | 人工干预率 | 需要人工介入的任务数/总任务数 |

### Agent Memory设计
**三层记忆体系：**
1. **短期记忆**：当前对话上下文（Conversation Buffer）
2. **长期记忆**：向量存储的历史对话摘要（Vector Memory）
3. **工作记忆**：当前任务的中间状态（Working Memory）

### Agent可观测性
- **输入输出日志**：记录每次调用的输入、输出、Token消耗
- **执行轨迹**：记录Agent的思考过程和工具调用链
- **性能监控**：延迟、错误率、吞吐量
- **成本监控**：Token消耗、API调用次数、成本统计

### Agent安全控制
- **工具权限控制**：限制Agent只能调用授权的工具
- **输入输出过滤**：过滤敏感信息和恶意输入
- **执行沙箱**：隔离执行环境，防止越权操作
- **预算控制**：设置Token和时间预算，防止资源滥用
'''

def get_system_design_supplement():
    return '''

## 📊 容量估算

### QPS估算
- **日均查询量**：100万次
- **峰值QPS**：日均/86400 * 3 = 34.7 * 3 ≈ 104 QPS
- **峰值并发**：QPS * 平均处理时间 = 104 * 0.5s ≈ 52并发

### Token成本估算
- **单次查询Token消耗**：输入100 + 上下文2000 + 输出500 = 2600 Token
- **日Token消耗**：100万 * 2600 = 260亿 Token
- **月成本**：260亿 * 0.0001元/Token = 26万元

### 缓存命中率估算
- **目标命中率**：70%
- **缓存容量**：热点数据30天 * 100万/天 * 2KB = 60GB

### 存储规模估算
- **文档量**：1000万篇
- **平均文档大小**：10KB
- **向量存储**：1000万 * 768维 * 4字节 = 30.72 GB
- **总存储**：文档100GB + 向量30GB + 索引50GB = 180GB
'''

def get_project_packaging_supplement():
    return '''

## 🎙️ 面试官提问版

**问题1：这个项目的核心价值是什么？**
**问题2：你在项目中遇到的最大挑战是什么？如何解决的？**
**问题3：项目的关键性能指标有哪些？如何优化的？**
**问题4：项目的技术选型是如何考虑的？**
**问题5：项目上线后有哪些改进空间？**

## ⏱️ 3分钟回答模板

**项目背景**：用STAR法则简述项目背景和目标（30秒）
**技术架构**：核心架构图和关键技术选型（60秒）
**核心亮点**：2-3个技术难点及其解决方案（60秒）
**量化成果**：关键指标和业务收益（30秒）

## ⏱️ 5分钟回答模板

**项目背景**：业务痛点和目标（45秒）
**技术选型**：各组件选型理由和对比（60秒）
**架构设计**：完整架构图和分层说明（90秒）
**难点攻克**：3个核心难点和解决方案（60秒）
**优化迭代**：如何持续优化和指标提升（45秒）

## ⏱️ 10分钟深度版

**项目背景**：详细业务分析和需求拆解（60秒）
**技术选型**：多维度对比分析（120秒）
**架构设计**：完整架构、数据流向、状态管理（180秒）
**难点攻克**：5个核心难点的技术方案和代码片段（180秒）
**量化指标**：详细的性能指标、成本分析、业务收益（60秒）

## ✨ 项目亮点总结

- 技术亮点1：创新性技术方案或架构设计
- 技术亮点2：关键优化带来的显著提升
- 技术亮点3：工程化实践和可维护性

## 📈 可量化指标

| 指标 | 优化前 | 优化后 | 提升幅度 |
|------|--------|--------|---------|
| 响应时间 | X ms | Y ms | Z% |
| 成功率 | X% | Y% | Z% |
| 成本 | X元/天 | Y元/天 | -Z% |

## 💡 面试加分表达

- "我们通过XXX技术方案，将指标从X提升到Y"
- "在设计阶段，我们考虑了XXX场景，因此选择了YYY方案"
- "针对XXX问题，我们提出了YYY创新解法，效果显著"
- "项目上线后，我们建立了XXX监控体系，确保稳定性"
'''

def main():
    folder = r'd:\langChian\enterprise-ai-workflow-os-multi-agent\AI应用开发面试图解圣经V2026'
    files = [f for f in os.listdir(folder) if f.startswith('P') and f.endswith('.md')]
    
    for filename in files:
        filepath = os.path.join(folder, filename)
        print(f"Processing {filename}...")
        
        enhanced = process_file(filepath, filename)
        write_file(filepath, enhanced)
        print(f"  Done!")

if __name__ == '__main__':
    main()
