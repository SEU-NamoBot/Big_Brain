# 快速上手

本文档说明如何安装依赖、配置大模型接口、测试 API 连通性，并运行大脑主流程。

## 1. 环境准备

建议在项目根目录创建 Python 虚拟环境：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

当前 `requirements.txt` 包含：

```text
numpy
sentence-transformers
openai
roarm-sdk
```

依赖用途：

- `numpy`：坐标、路径、距离等数值计算。
- `sentence-transformers`：RAG 历史任务相似度检索。
- `openai`：调用 OpenAI 兼容的大模型和视觉模型接口。
- `roarm-sdk`：RoArm-M3 机械臂控制。

第一次运行 `sentence-transformers` 时可能会下载模型，初始化会比较慢。

## 2. 配置大模型

大模型相关配置集中在 `config.py`。

当前代码预留了多类 OpenAI 兼容接口：

- 智谱：`ZHIPU_*`
- 硅基流动：`SILICONFLOW_*`
- GPT 兼容接口：`GPT_*`
- Ollama 本地接口：`OLLAMA_*`
- DeepSeek 预留：`DEEPSEEK_*`

如果要换模型，通常只需要改 `TARGET_*` 指向。例如使用本地 Ollama+硅基流动VLM：

```python
TARGET_API_KEY = OLLAMA_API_KEY
TARGET_BASE_URL = OLLAMA_BASE_URL
TARGET_LLM_MODEL = OLLAMA_LLM_MODEL
TARGET_VLM_MODEL = SILICONFLOW_VLM_MODEL
```

注意：当前代码还没有自动读取 `.env`。交接给别人时，不要把真实 API Key 写入仓库；建议后续改成环境变量或 `.env` 读取。

## 3. 测试 API 连通性

运行：

```bash
python test_api.py --only siliconflow
python test_api.py --only openai
python test_api.py --only ollama
```

可选参数：

```bash
python test_api.py --only siliconflow --timeout 30
```

如果失败，优先检查：

- `API_KEY` 是否为空。
- `BASE_URL` 是否是 OpenAI 兼容 `/v1` 地址。
- 模型名是否被供应商支持。
- 本地 Ollama 是否已经启动。

## 4. 运行大脑主流程

在项目根目录运行：

```bash
python big_brain.py
```

主流程会：

1. 读取 `memory/rag_history.json`。
2. 初始化 RAG。
3. 拼接规划 Prompt。
4. 调用 LLM 生成 Python 动作代码。
5. 执行生成代码。
6. 调用 `action/robot_api.py` 中的动作原语。

## 5. 当前运行状态提醒

当前项目是“高层规划原型 + 小脑 API 占位”。也就是说：
具体使用的时候需要接入小脑的具体接口实现
