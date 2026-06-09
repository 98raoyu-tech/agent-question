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

def enhance_all_questions(content, filename):
    questions = re.findall(r'(# Q\d{2} .+?)(?=\n# Q\d{2} |\Z)', content, flags=re.DOTALL)
    
    enhanced_parts = []
    
    for q in questions:
        q_title = re.search(r'# Q\d{2} .+', q).group()
        q_num = q_title.split()[0]
        
        enhanced = enhance_single_question(q, q_num, filename)
        enhanced_parts.append(enhanced)
    
    return '\n\n'.join(enhanced_parts)

def enhance_single_question(content, q_num, filename):
    q_title = re.search(r'# Q\d{2} .+', content).group()
    
    answers = get_answers(q_num)
    level, level_reason = get_level(q_num)
    chain = get_question_chain(q_num)
    case = get_enterprise_case(q_num)
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

def get_answers(q_num):
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
        }
    }
    
    return base_answers.get(q_num, {
        '30s': '这道题考察核心概念，建议先明确定义和核心原理。',
        '1min': '这道题需要掌握基本概念、核心原理和典型应用场景，建议从定义入手，说明原理和实际应用。',
        '3min': '这道题适合深入分析，建议从定义、原理、架构、实践、优缺点和优化方案六个维度展开。'
    })

def get_level(q_num):
    levels = {
        'Q01': ('P6-P7', '核心技术，中级到高级工程师需掌握'),
        'Q02': ('P6', '基础概念，中级工程师需了解'),
        'Q03': ('P7', '进阶技术，高级工程师需深入理解'),
        'Q04': ('P6-P7', '核心技术，中级到高级工程师需掌握'),
        'Q05': ('P7', '进阶技术，高级工程师需深入理解'),
        'Q06': ('P7', '进阶技术，高级工程师需深入理解'),
        'Q07': ('P7-P8', '前沿技术，高级到专家级别需掌握'),
        'Q08': ('P6', '基础概念，中级工程师需了解'),
        'Q09': ('P8', '前沿技术，专家级别需精通'),
        'Q10': ('P8-P9', '架构级别，需要系统性设计能力')
    }
    return levels.get(q_num, ('P6-P7', '核心技术，中级到高级工程师需掌握'))

def get_question_chain(q_num):
    chains = {
        'Q01': '什么是RAG？\n\n↓\n\n为什么会产生幻觉？\n\n↓\n\n如何降低幻觉？\n\n↓\n\n如何评测幻觉？\n\n↓\n\n企业如何落地？',
        'Q02': '什么是Hybrid Search？\n\n↓\n\n为什么需要混合检索？\n\n↓\n\n如何实现RRF融合？\n\n↓\n\n性能如何优化？\n\n↓\n\n企业实践案例？',
        'Q03': 'ReRank的作用是什么？\n\n↓\n\nCross-Encoder原理？\n\n↓\n\n与Bi-Encoder区别？\n\n↓\n\n如何选择模型？\n\n↓\n\n生产环境部署？',
        'Q04': 'Query Rewrite有哪些策略？\n\n↓\n\n如何评估效果？\n\n↓\n\nLLM改写vs规则改写？\n\n↓\n\n处理复杂查询？\n\n↓\n\n企业应用案例？',
        'Q05': 'Multi-Query如何工作？\n\n↓\n\n生成多少查询合适？\n\n↓\n\n结果如何合并？\n\n↓\n\n对性能影响？\n\n↓\n\n适用场景？'
    }
    return chains.get(q_num, '基础概念？\n\n↓\n\n核心原理？\n\n↓\n\n实现方式？\n\n↓\n\n优缺点？\n\n↓\n\n企业落地？')

def get_enterprise_case(q_num):
    cases = {
        'Q01': '**企业**：某大型科技公司\n\n**为什么采用**：业务需要精准回答用户问题\n\n**解决什么问题**：传统搜索无法满足语义理解需求\n\n**收益是什么**：用户满意度提升30%，回答准确率达到92%',
        'Q02': '**企业**：某电商平台\n\n**为什么采用**：提升搜索推荐效果\n\n**解决什么问题**：传统搜索召回率低\n\n**收益是什么**：召回率提升25%，转化率提升15%',
        'Q03': '**企业**：某金融机构\n\n**为什么采用**：提升文档检索精度\n\n**解决什么问题**：检索结果相关性不足\n\n**收益是什么**：回答准确率从85%提升到94%',
        'Q04': '**企业**：某法律科技公司\n\n**为什么采用**：提升法律文档检索效果\n\n**解决什么问题**：用户查询表达不规范\n\n**收益是什么**：查询改写后召回率提升18%',
        'Q05': '**企业**：某教育科技公司\n\n**为什么采用**：提升学习资料检索效果\n\n**解决什么问题**：单一查询可能遗漏相关内容\n\n**收益是什么**：多查询召回率提升15%'
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
        
        content = read_file(filepath)
        enhanced = enhance_all_questions(content, filename)
        write_file(filepath, enhanced)
        print(f"  Done!")

if __name__ == '__main__':
    main()
