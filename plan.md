**TODO List**。

---

# 1. 每次实验要收集的数据

每次实验记录一行，字段如下：

| English Field            | 中文含义                                          |
| ------------------------ | ------------------------------------------------- |
| `run_id`                 | 实验编号                                          |
| `task_id`                | 任务编号（N1~N4, G1~G4, C1~C4）                   |
| `task_type`              | 任务类型（Navigation / Manipulation / Composite） |
| `instruction`            | 自然语言指令                                      |
| `model_name`             | 使用的大模型名称                                  |
| `temperature`            | 温度参数                                          |
| `adjust_policy`          | adjust策略（0 / 1 / 2）                           |
| `repeat_id`              | 第几次重复实验                                    |
| `generated_code`         | 生成的代码/API序列                                |
| `semantic_parse_correct` | 语义解析是否正确（是/否）                         |
| `decomposition_correct`  | 子任务分解是否正确（是/否）                       |
| `code_executable`        | 生成代码是否可执行（是/否）                       |
| `api_call_count`         | 本次任务总API调用次数                             |
| `adjust_count`           | 实际触发的adjust次数                              |
| `success_at_1`           | 首次执行是否成功（是/否）                         |
| `success_at_2`           | 最多1次adjust后是否成功（是/否/—）                |
| `success_at_3`           | 最多2次adjust后是否成功（是/否/—）                |
| `final_result`           | 最终结果（Success / Fail）                        |
| `total_time_s`           | 总耗时（秒）                                      |
| `nav_call_count`         | navigateto调用次数                                |
| `pickup_call_count`      | pickup调用次数                                    |
| `putdown_call_count`     | putdown调用次数                                   |
| `nav_success_count`      | navigateto成功次数                                |
| `pickup_success_count`   | pickup成功次数                                    |
| `putdown_success_count`  | putdown成功次数                                   |
| `final_position_error`   | 最终位置误差（导航/放置类可填）                   |
| `failure_reason`         | 失败原因                                          |
| `vlm_summary`            | VLM判断摘要                                       |
| `human_note`             | 人工备注                                          |

---

# 2. 固定任务列表

## Navigation

- `N1` 导航到(100,200)
- `N2` 导航到垃圾桶旁边
- `N3` 绕垃圾桶做长50，宽50的方形运动
- `N4` 前往坐标绝对值之和最小的垃圾桶旁边，以50为半径绕行一圈，随后返回出发位置

## Manipulation

- `G1` 夹起红色方块
- `G2` 夹起位于地面的红色方块
- `G3` 把物体放到桌子上
- `G4` 把物体放到蓝色方块和黄色方块中间

## Composite

- `C1` 把沙发上的水杯放到椅子上
- `C2` 把红色方块从桌子上拿起，放到蓝色方块和黄色方块中间
- `C3` 把地上所有的非家具丢到垃圾桶中
- `C4` 以长度为100的方形方式绕着桌子运动，当有红色方块出现时，夹起他，放到垃圾桶中

---

# 3. 要做哪些实验

---

## ✅ E1 主实验

> 或许不需要5次。这个是必做的大小脑协同，包含全量能力，是必须做出来的。

**目的**：主结果、任务类型分析、原语统计、失败分析

- 模型：`GPT-4o`
- temperature：`0.0`
- adjust_policy：`2`
- 任务：`N1~N4, G1~G4, C1~C4`
- 每个任务重复：`5次`

### 数量

- 12 个任务 × 5 次 = **60 次**

### TODO

- 跑 N1 共5次
- 跑 N2 共5次
- 跑 N3 共5次
- 跑 N4 共5次
- 跑 G1 共5次
- 跑 G2 共5次
- 跑 G3 共5次
- 跑 G4 共5次
- 跑 C1 共5次
- 跑 C2 共5次
- 跑 C3 共5次
- 跑 C4 共5次

---

## ✅ E2 adjust消融实验

> 鉴于是代码吸附式抓取，所以只能测试手动扰动导致的失误，验证其纠偏能力？
> adjust主要是起修正原语的作用，如果大脑本身就是错的，那么怎么纠偏也就纠正不回来。
> 或许不需要那么多次实验，或者单纯验证adjust的有效性？
> 紧密跟随的还有VLM视觉裁判，裁判的判断准确度是否也需要测量？毕竟他提供一手信息给adjust

**目的**：比较 0次 / 1次 / 2次 adjust 的效果

注意：`2次adjust` 数据直接用 E1，不用重跑。
这里只补做 `0次` 和 `1次`。

- 模型：`GPT-4o`
- temperature：`0.0`
- adjust_policy：`0` 和 `1`
- 任务：`N1~N4, G1~G4, C1~C4`
- 每个任务重复：`3次`

### 数量

- 12 个任务 × 2 种adjust策略 × 3 次 = **72 次**

### TODO

#### adjust = 0

- 跑 N1 共3次
- 跑 N2 共3次
- 跑 N3 共3次
- 跑 N4 共3次
- 跑 G1 共3次
- 跑 G2 共3次
- 跑 G3 共3次
- 跑 G4 共3次
- 跑 C1 共3次
- 跑 C2 共3次
- 跑 C3 共3次
- 跑 C4 共3次

#### adjust = 1

- 跑 N1 共3次
- 跑 N2 共3次
- 跑 N3 共3次
- 跑 N4 共3次
- 跑 G1 共3次
- 跑 G2 共3次
- 跑 G3 共3次
- 跑 G4 共3次
- 跑 C1 共3次
- 跑 C2 共3次
- 跑 C3 共3次
- 跑 C4 共3次

---

## ✅ E3 高层规划静态评估实验

> 额外添加parse_object_name的静态测试，测试使用的是human_object中涉及的parse，从而方便比较
> 依旧是2个模型，3个温度，3次重复

- **目的**：比较不同模型、不同 temperature 下，高层任务规划是否正确
  **特点**：只看大脑输出，不进仿真执行

  ***

  ### 配置

  ### 模型
  - `GPT-4o`
  - `Qwen2.5 7B`

  ### temperature
  - `0.0`
  - `0.4`
  - `0.8`

  ### 任务

  建议仍然使用全部 12 个任务：
  - `N1~N4`
  - `G1~G4`
  - `C1~C4`

  ### 每个任务重复
  - `3次`

  ***

  ### 数量

  2 个模型 × 3 个温度 × 12 个任务 × 3 次
  = **216 次静态生成**

  这个不需要执行机器人，所以很快。

  ***

  ### 每次静态实验要收集的数据

  | English Field            | 中文含义           |
  | ------------------------ | ------------------ |
  | `run_id`                 | 实验编号           |
  | `task_id`                | 任务编号           |
  | `task_type`              | 任务类型           |
  | `instruction`            | 自然语言指令       |
  | `model_name`             | 模型名称           |
  | `temperature`            | 温度参数           |
  | `repeat_id`              | 第几次重复         |
  | `generated_code`         | 生成的代码/API序列 |
  | `semantic_parse_correct` | 语义解析是否正确   |
  | `decomposition_correct`  | 子任务分解是否正确 |
  | `code_executable`        | 代码是否可执行     |
  | `human_note`             | 人工备注           |

  ***

  ### 你要判断的三个结果

  每次只判断这三件事：
  - `semantic_parse_correct`
  - `decomposition_correct`
  - `code_executable`

  ***

  ### TODO

  #### GPT-4o, temp=0.0
  - N1~N4 各3次
  - G1~G4 各3次
  - C1~C4 各3次

  #### GPT-4o, temp=0.4
  - N1~N4 各3次
  - G1~G4 各3次
  - C1~C4 各3次

  #### GPT-4o, temp=0.8
  - N1~N4 各3次
  - G1~G4 各3次
  - C1~C4 各3次

  #### Qwen2.5 7B, temp=0.0
  - N1~N4 各3次
  - G1~G4 各3次
  - C1~C4 各3次

  #### Qwen2.5 7B, temp=0.4
  - N1~N4 各3次
  - G1~G4 各3次
  - C1~C4 各3次

  #### Qwen2.5 7B, temp=0.8
  - N1~N4 各3次
  - G1~G4 各3次
  - C1~C4 各3次

216 次

---

## ✅ E4 人工API序列对照实验

**目的**：人工编写API序列 vs LLM自动生成

- 方法：`人工编写正确API序列`
- 模型：`None`
- temperature：`None`
- adjust_policy：`0`
- 任务：`C1~C4`
- 每个任务重复：`3次`

### 数量

- 4 个任务 × 3 次 = **12 次**

### TODO

- 跑 C1 共3次（人工API）
- 跑 C2 共3次（人工API）
- 跑 C3 共3次（人工API）
- 跑 C4 共3次（人工API）

---

## ✅ E5 RAG能力测试

- 第一次跑，三遍的效果
- 有了第一次跑的结果后，重跑的准确率
- 不同类型+复杂度测试提升幅度
- 人工作为RAG，微调任务作为测试案例，测试其逻辑是否正确。

# 4. 总实验次数

- E1：60 次
- E2：72 次
- E3：216 次 静态
- E4：12 次
- E5: 36 静态

---

# 5. 每次实验怎么做

每次实验统一流程：

- 选择任务 `task_id`
- 设置模型 `model_name`
- 设置 `temperature`
- 设置 `adjust_policy`
- 运行任务
- 保存生成的 `generated_code`
- 记录是否语义解析正确
- 记录是否分解正确
- 记录 API 调用次数
- 记录 adjust 次数
- 记录 `success_at_1 / success_at_2 / success_at_3`
- 记录最终成功或失败
- 记录总耗时
- 若失败，填写失败原因
- 补充 VLM 摘要和人工备注

---

# 6. 最后汇总时要算的东西

- Success@1
- Success@2
- Success@3
- 平均任务时间
- 平均adjust次数
- 平均API调用次数
- 语义解析正确率
- 子任务分解正确率
- navigateto成功率
- pickup成功率
- putdown成功率
- 失败原因分布
