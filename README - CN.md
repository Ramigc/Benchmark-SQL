

---

# LLM SQL Agent Benchmark（SQL 智能体评测框架）

一个用于评估 **基于大语言模型（LLM）的 SQL Agent** 的轻量级 Benchmark 框架。

本项目构建了一个 SQL Agent，通过 **OpenAI 兼容 API（如 DeepSeek 或 Qwen）调用 LLM**，并评估其将自然语言问题转换为 SQL 查询的能力。

Benchmark 会从多个维度评估 Agent 的表现，包括：

* **准确率（Accuracy）**
* **结果完整性（Completeness）**
* **效率（Efficiency）**
* **鲁棒性（Robustness）**
* **响应延迟（Latency）**

---

# 项目结构

```
.
├── llm_sql_agent.py          # SQL Agent实现
├── benchmark_sql_agent.py    # Benchmark评测脚本
├── test_cases_sql.py         # Benchmark测试任务
├── employee_dataset.py       # SQLite示例数据集
├── config_local.py           # LLM API配置
├── visualize_radar.py        # 雷达图可视化
├── requirements.txt
└── README.md
```

---

# 项目功能

本项目包含以下功能：

* 基于 **LangChain + LLM** 的 SQL Agent
* SQLite 员工数据库示例
* 自动化 Benchmark 评测
* 多维度评估指标
* 噪声输入鲁棒性测试
* 雷达图结果可视化

---

# 数据集

Benchmark 使用一个简单的员工数据库。

数据库结构如下：

| 列名     | 含义   |
| ------ | ---- |
| name   | 员工姓名 |
| dept   | 部门   |
| title  | 职位   |
| salary | 工资   |

示例数据：

```
("John Smith", "Engineering", "ML Engineer", 32000)
("Sophia Martinez", "Finance", "Accountant", 20000)
("Alexander Lewis", "Engineering", "Software Architect", 40000)
```

数据集定义在：

```
employee_dataset.py
```

数据库 `company.db` 会在程序初始化时自动创建并写入数据。 

---

# SQL Agent

SQL Agent 的实现文件：

```
llm_sql_agent.py
```

该 Agent 的工作流程：

1. 连接 SQLite 数据库
2. 使用 LangChain SQL Toolkit
3. 调用 LLM 生成 SQL 查询

LLM 的配置在：

```
config_local.py
```

示例配置如下： 

```python
LLM_MODEL = "deepseek-chat"
LLM_API_KEY = "your_api_key"
LLM_BASE_URL = "https://api.deepseek.com/v1"
```

---

# Benchmark 测试任务

Benchmark 查询定义在：

```
test_cases_sql.py
```

每个测试任务包含：

```
Case(
    id="avg_salary_engineering",
    question="What is the average salary in Engineering?",
    gold_sql="SELECT AVG(salary) FROM employees WHERE dept='Engineering';"
)
```

Benchmark 包含多种 SQL 推理任务：

### 基础 SQL 查询

* 条件过滤
* 排序
* 聚合计算
* 分组查询

### 中等复杂度查询

* 嵌套查询
* 逻辑条件
* 部门统计

### 边界情况

* 空结果查询

示例任务：

* 查询最高工资员工
* 查询工资大于 X 的员工
* 每个部门的平均工资
* 平均工资高于公司平均值的部门
* 每个部门工资最高的员工

---

# Benchmark 评测流程

该 Benchmark 用于评估 Agent **将自然语言问题转换为 SQL 查询的能力**。

评测流程如下：
 
1. 向 SQL 代理提供自然语言问题。
2. LLM 生成 SQL 查询。
3. 在 SQLite 数据库上执行查询。
4. 将结果与真实 SQL 结果进行比较。
5. 计算评估指标。

流程示意：

```
自然语言问题
      │
      ▼
  LLM SQL Agent
      │
      ▼
  生成 SQL
      │
      ▼
SQLite数据库执行
      │
      ▼
Agent结果
      │
      ▼
与Ground Truth比较
      │
      ▼
评估指标
```

---

# 评估指标

Benchmark 从多个维度评估 SQL Agent。

---

## 1 Accuracy（准确率）

判断 Agent 返回结果是否与 Ground Truth SQL 的结果一致。

---

## 2 Result Completeness（结果完整性）

衡量返回结果是否完整：

```
matched_rows / total_gold_rows
```

---

## 3 Query Efficiency（查询效率）

统计 Agent 在回答一个问题时执行了多少次 SQL。

执行次数越少，说明推理效率越高。

---

## 4 Latency Efficiency（延迟效率）

测量 Agent 回答问题所需时间。

响应时间越短越好。

---

## 5 Token Efficiency（Token效率）

统计 LLM 调用过程中使用的 Token 数量。

Token 越少说明 Prompt 和推理更加高效。

---

## 6 Robustness（鲁棒性）

评估在 **输入存在噪声时** Agent 的表现。

噪声包括：

* 删除字符
* 字符交换
* 键盘输入错误
* 单词顺序扰动

模拟真实用户输入错误。

---

# 安装

### 推荐 Python 版本

```
Python 3.10 – 3.11
```

---

### 安装依赖

```
pip install -r requirements.txt
```

主要依赖包括： 

```
langchain
langchain-community
langchain-openai
sqlalchemy
```

---

# 配置

运行 Benchmark 之前，需要配置 LLM API：

编辑文件：

```
config_local.py
```

示例：

```python
LLM_MODEL = "deepseek-chat"
LLM_API_KEY = "your_api_key"
LLM_BASE_URL = "https://api.deepseek.com/v1"
```

该文件包含 API Key，**不建议提交到 GitHub**。

---

# 运行 Benchmark

运行：

```
python benchmark_sql_agent.py
```

该脚本会：

1. 初始化 SQLite 数据库
2. 构建 SQL 代理
3. 运行所有基准测试用例
4. 计算评估指标
5. 将结果保存到：

```
benchmark_results.json
```

---

# 结果可视化

运行：

```
python visualize_radar.py
```

脚本会读取：

```
benchmark_results.json
```

并绘制 **雷达图（Radar Chart）**。

展示指标包括：

* Accuracy
* Completeness
* Query Efficiency
* Latency Efficiency
* Token Efficiency
* Robustness

---

# 示例 Benchmark 输出

示例结果：

```
{
  "total": 15,
  "passed": 13,
  "accuracy": 0.867,
  "result_completeness": 0.91,
  "query_efficiency": 0.83,
  "latency_efficiency": 0.79,
  "token_efficiency": 0.81,
  "robust_accuracy": 0.72
}
```

雷达图可以直观展示 Agent 在各个维度的表现。

---

# 可扩展方向

该 Benchmark 框架可以扩展到：

* 更大的 SQL 数据集
* 多表数据库结构
* Schema Linking 评估
* 对抗性自然语言查询
* 多模型对比（GPT / Gemini / DeepSeek / Qwen）

---

# License

本项目仅用于 **研究与教学目的**。

---
