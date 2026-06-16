# 模块说明

本文档按目录说明大脑模块中每个主要文件的作用，方便后续同学定位代码。

## 1. 根目录文件

### `big_brain.py`

系统主入口，核心类是 `BigBrain`。

主要职责：

- 读取历史任务。
- 初始化 RAG 检索器。
- 初始化任务规划 LLM。
- 拼接最终 Prompt。
- 调用 LLM 生成动作代码。
- 读取 L2 语义对象。
- 使用 `exec()` 执行动作计划。
- 整理新任务历史记录。

注意点：

- 执行环境会注入 `objects`、`instruction` 和对象字典。

### `config.py`

集中管理配置：

- 大模型和视觉模型 API。
- 当前启用的目标模型。
- RAG 模型和相似度阈值。
- 判断误差阈值。
- 默认物体尺寸。
- YOLO 目标检测类别。

重要配置：

```python
RAG_MODEL = "sentence-transformers/all-mpnet-base-v2"
RAG_SIMILARITY_THRESHOLD = 0.5
HISTORY_PATH = "memory/rag_history.json"

MOVE_ERROR_THRESHOLD = 5.0
PLACE_ERROR_THRESHOLD = 5.0
CATCH_ERROR_THRESHOLD = 20.0
```

后续小脑返回单位时，要和这里的阈值单位统一。

### `test_api.py`

用于测试大模型接口是否可用。支持：

- SiliconFlow
- OpenAI 兼容接口
- Ollama

示例：

```bash
python test_api.py --only siliconflow
```

### `runtime_context.py`

保存运行期上下文：

```python
CTX = {
    "instruction": None,
    "task_id": None,
    "step_idx": 0,
}
```

`JudgeLLM` 会从这里读取当前全局任务，供 VLM 判断当前动作是否满足整体指令。

## 2. `model/`

### `model/llm.py`

包含两个核心类：

#### `PlannerLLM`

负责根据 Prompt 生成动作计划代码。

调用链：

```text
BigBrain.run()
  -> PlannerLLM.generate_code()
  -> utils.call_LLM()
  -> utils.extract_code()
```

输出是一段 Python 代码，会被主流程执行。

#### `JudgeLLM`

负责动作后判断和失败恢复。

核心方法：

- `judge()`：动作原语调用的总入口。
- `_parse_atomic_task()`：解析结构化动作。
- `_collect_observation()`：收集机器人状态。
- `_rule_judge()`：基于阈值做规则判断。
- `judge_VLM()`：调用视觉模型判断。
- `extract_VLM_answer()`：解析 VLM JSON 输出。
- `replan()`：根据失败原因生成恢复代码。

动作编号：

| action_id | 动作                     |
| --------- | ------------------------ |
| 1         | `move_to_xy`             |
| 2         | `move_to_obj_by_offset`  |
| 3         | `pick_up_xy`             |
| 4         | `pick_up_obj`            |
| 5         | `put_down_xy`            |
| 6         | `put_down_obj_by_offset` |

当前需要注意：

- `replan()` 中实际执行恢复代码的 `exec(adjust_code, exec_globals)` 被注释。

### `model/rag.py`

负责历史任务检索。

流程：

1. 读取历史任务中的 `command`。
2. 使用 `SentenceTransformer` 编码。
3. 对当前任务编码。
4. 计算余弦相似度。
5. 若最高相似度超过阈值，返回历史任务代码片段。

历史文件：

```text
memory/rag_history.json
```

## 3. `prompt/`

### `prompt/task_prompt.py`

定义 `BASE_PROMPT`，告诉 LLM 可用动作函数和示例任务。

这里是规划能力的核心。如果新增动作原语，要同步更新此 Prompt。

### `prompt/object_prompt.py`

定义对象解析示例，用于 `parse_obj_name()`。

模型需要生成 Python 筛选代码，并设置：

```python
ret_val = ...
```

### `prompt/vlm_prompt.py`

定义视觉裁判 Prompt。要求 VLM 输出严格 JSON：

```json
{
  "pass": true,
  "error_type": "none",
  "reason": "explanation",
  "suggested_correction": ""
}
```

### `prompt/adjust_prompt.py`

定义失败恢复 Prompt。输入失败动作和 VLM 建议，输出局部恢复动作代码。

### `prompt/position_prompt.py`

位置解析 Prompt 预留，目前主要保存 CAP 原始示例，项目主链路暂未重点使用。

## 4. `utils/`

### `utils/utils.py`

辅助函数集合，也是小脑对接重点文件。

主要函数：

- `get_obj_xy()`
- `get_obj_z()`
- `get_obj_size()`
- `get_obj_rgb()`
- `get_robot_pos()`
- `get_robot_orientation()`
- `get_robot_arm()`
- `parse_obj_name()`
- `call_LLM()`
- `extract_code()`
- `load_L2_memory()`
- `encode_image()`

## 5. `action/`

### `action/robot_api.py`

大脑暴露给 LLM 的动作原语层，也是小脑 API 的主要占位层。

当前动作：

- `move_to_xy(x, y)`
- `move_to_obj_by_offset(Object, dx, dy)`
- `pick_up_xy(x, y)`
- `pick_up_xy_arm(x, y)`
- `pick_up_obj(item)`
- `put_down_xy(x, y)`
- `put_down_obj_by_offset(target, dx, dy)`

这些函数目前大多只打印动作并调用 `JudgeLLM.judge()`。后续需要在这里接入小脑底盘和机械臂 API。

### `action/arm.py`

RoArm-M3 机械臂简单控制示例，展示如何通过 `roarm-sdk` 初始化机械臂并调用 `pose_ctrl()`。

### `action/RoArm-M3_Python/`

RoArm-M3 相关示例或辅助文件。

## 6. `memory/`

### `memory/rag_history.json`

历史任务样本，用于 RAG。

格式：

```json
{
  "id": 1,
  "command": "pick up the apple",
  "task_queue": [
    "apple_obj = parse_obj_name('apple', objects)",
    "move_to_obj_by_offset(apple_obj, 0, 0)",
    "pick_up_obj(apple_obj)"
  ]
}
```

### `memory/l2.json`

L2 语义地图预留文件。当前主流程里 `load_L2_memory()` 仍然硬编码，后续需接入小脑API

## 7. `image/`

### `image/image.png`

当前 VLM 判断读取的动作后图片路径。接入真实小脑后，可以让小脑每次动作后覆盖这张图片，或修改 `JudgeLLM.judge_VLM()` 直接获取最新图像。
