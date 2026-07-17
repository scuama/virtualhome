# RoboState 多任务扩展测试复盘与优化计划

> 日期：2026-07-17
> 范围：`agent/robostate`、`evaluation/test_runner.py`、9 个 E 类扩展配置，以及已落盘的 RoboState 多任务运行记录。
> 目标：明确 Agent、测试框架和配置文件各自的问题，并给出后续可直接执行的修改顺序。

## 结论摘要

当前 RoboState **没有针对多任务做显式适配**。它把编号后的多条指令当成一条普通自然语言指令，经过一次 GoalReasoner 和一次 SDGPlanner 生成一个全局意图与一个全局 SDG；之后每一步仍只让 LLM 从这个全局 SDG 中选择动作。虽然 `RoboStateAgent` 内存在 `_check_success()`，但该方法没有被调用，Agent 也没有读取配置中的 `tasks`，更没有接收到测试框架计算出的逐任务完成状态。

这导致多任务运行出现三个主要症状：

1. 已完成任务被反复操作，未完成任务没有稳定调度。
2. 目标对象不在当前 partial observation 时，Agent 大量输出 `[wait]`，而不是系统探索未访问房间。
3. LLM 同时承担任务拆分、完成判断、目标选择、探索和动作落地，输出会漂移，并产生 `unknown` ID、错误对象类型和重复动作。

测试框架已经具备多任务配置选择、AND 成功判断和动态事件运行时，但仍缺少适合论文实验的任务进度接口、原始记录、初始化后角色位置恢复、动作校验和中断运行生命周期管理。

9 个配置在结构上正确，可作为首批管线验证配置；但目前仅覆盖一个 Scene、少量源任务，且多任务规模与任务身份、顺序和语义难度存在混杂，暂时不足以单独支撑论文中的统计结论。

## 已有测试结果与证据范围

### 有效的最终结果

以下结果来自 ask 策略和初始化放置修复后的完整运行。这里仅使用原始量：任务总数、完成任务数和总决策步数；不采用当前 `metrics.json` 中已经确认需要重命名的 SR/PS 字段。

| 场景 | 任务总数 | 完成任务数 | 总步数 | 已完成任务 | 未完成任务 | 终止原因 |
|---|---:|---:|---:|---|---|---|
| E_MULTI_S3 | 3 | 1 | 45 | E1_03 book→sofa，step 18 | E1_07 mug→coffeetable；E1_15 folder→closet | 达到最大步数 |
| E_MULTI_S5 | 5 | 3 | 75 | E1_18 plate→dishwasher，step 2；E1_03，step 21；E1_07，step 27 | E1_15；E1_11 computer ON | 达到最大步数 |

证据：

- [S3 metrics](../evaluation/results/robostate/fail/E_MULTI_S3/metrics.json)
- [S3 完整 Markdown](../evaluation/results/robostate/fail/E_MULTI_S3/run_E_MULTI_S3.md)
- [S5 metrics](../evaluation/results/robostate/fail/E_MULTI_S5/metrics.json)
- [S5 完整 Markdown](../evaluation/results/robostate/fail/E_MULTI_S5/run_E_MULTI_S5.md)

两次运行的行为分布：

| 场景 | `[wait]` | wait 占比 | `[ask]` | 典型无效/重复行为 |
|---|---:|---:|---:|---|
| S3 | 25/45 | 55.6% | 1 | 多次 `[open] <folder>`；`[walk] <closet> (??/unknown)`；完成 book 后再次 grab/putback book |
| S5 | 43/75 | 57.3% | 1 | 多次重新处理已完成的 plate、mug；从 step 56 起基本持续 wait |

### 未形成最终结果的运行

S7 在用户要求暂停测试时被中断。`evaluation/test_runner.log` 记录了：

- E1_03 在 step 6 首次完成。
- E1_07 在 step 8 首次完成。
- E1_18 在 step 13 首次完成。
- E1_14 在 step 17 首次完成。

[S7 raw Markdown](../evaluation/results/robostate/raw/run_E_MULTI_S7.md) 中已有 57 个动作，但没有 episode 结束记录，因此不能作为最终任务完成数量。`fail/E_MULTI_S7/metrics.json` 是更早的“ask 直接失败”旧结果，时间早于本次 raw log，属于陈旧产物，不能用于当前版本汇报。

Semantic 三个配置和 Dynamic 三个配置尚未产生当前版本下的完整端到端结果。

---

## 1. Agent 缺陷

### 1.1 没有多任务数据模型

`RoboStateAgent.get_action()` 只读取顶层 `goal_instruction`，没有读取 `config["tasks"]`。step 0 只创建：

- 一个 `GoalReasoner`；
- 一个 `SDGPlanner`；
- 一个 `goal_intent`；
- 一个 `current_sdg`。

代码位置：[agent/robostate_agent.py](../agent/robostate_agent.py#L122)。

因此多条互相独立的 E 任务没有被表示成 `pending / active / satisfied / blocked` 的任务集合，也不存在任务切换策略。

### 1.2 单个全局 SDG 不适合并列任务

`SDGPlanner.generate_sdg()` 接收整个复合字符串，并要求 LLM 生成一个 DAG：[agent/robostate/sdg_planner.py](../agent/robostate/sdg_planner.py#L11)。

单任务 SDG 的“根目标—前置条件”结构适合一个目标，但并列任务应是多个互相独立的 SDG 或一个包含明确多根节点的任务图。当前实现没有多根任务语义，LLM 会自行选择所谓“primary goal”或“next node”，不同调用之间焦点容易漂移。

S5 日志中 book、mug、plate 已满足后，Executor 仍反复把这些节点当作当前焦点，而 folder 和 computer 长期没有得到稳定调度。

### 1.3 Agent 的成功检查是未使用代码

`RoboStateAgent._check_success()` 能解析部分 AND 条件，但整个 Agent 内没有调用点：[agent/robostate_agent.py](../agent/robostate_agent.py#L40)。

实际的 `satisfied_nodes` 完全来自 LLMExecutor 的 JSON 自报，不是由统一 condition checker 验证。Agent 因而不知道：

- 哪些顶层任务已经完成；
- 哪些完成状态后来被破坏；
- 应该切换到哪一个未完成任务。

直接后果：

- S3 在 book 已于 step 18 完成后，又于 step 28、41 重新 grab book，并再次 putback。
- S5 在 plate 已于 step 2 完成后，又多次 grab/putin plate；mug 完成后也被反复操作。

### 1.4 没有明确的探索状态机

RoboState 使用 partial observation，并通过 `memory_nodes` / `memory_edges` 合并历史观察，但没有维护：

- 已访问房间；
- 未访问房间 frontier；
- 某个目标类别最后出现的位置；
- 当前缺失目标应触发的搜索计划；
- 搜索失败后的房间切换。

代码位置：[agent/robostate_agent.py](../agent/robostate_agent.py#L169)。

当 closet、computer 等目标没有出现在当前图中时，Executor 通常解释为“等待图刷新”，而不是走向尚未搜索的 bedroom/livingroom。S3 和 S5 超过一半的步数被 `[wait]` 消耗。

这与 Executor prompt 本身的约束冲突：prompt 规定 `[wait]` 只应用于动态事件、临时规则或移动物体，但运行 reasoning 多次明确承认“没有动态事件”，仍然选择 wait。

### 1.5 PerceptionFilter 只能筛选已见对象，不能解决未见目标

PerceptionFilter 的输入只包含 memory graph 中已经观察到的类别。它让 LLM 从这些类别中选择相关类，然后强制保留在 SDG/intent 字符串中出现且**已经存在于 unique_classes** 的类别：[agent/robostate/perception_filter.py](../agent/robostate/perception_filter.py#L13)。

如果 closet 或 computer 从未被观察到：

- Prompt 再强调“必须保留 closet”也无法产生 closet 的 ID；
- Executor 只能看到房间和少量局部物体；
- 当前 Agent 又没有探索策略，最终进入 wait 循环。

### 1.6 动作 grounding 缺少硬校验

LLM 直接输出最终 Unity action。格式化层只为带数字 ID 的对象补尖括号，没有验证：

- ID 是否为整数；
- ID 是否存在于当前/记忆图；
- class 与 ID 是否匹配；
- 动作目标是否具有所需 property；
- 当前是否满足距离、持有、容器状态等前置条件。

因此 S3 出现：

- `[walk] <closet> (??)`；
- `[walk] <closet> (unknown)`；
- 把 folder 当作需要 open 的目标。

这些动作本应在进入 Unity 前被确定性拒绝和重新规划。

### 1.7 ask 后的策略只有“禁止再问”，没有“自主恢复”

当前首次 ask 会收到配置澄清或 `nothing to claim`，之后通过 prompt 和硬拦截禁止再次 ask。这个约束本身已生效，但默认回复不提供新位置或对象信息。

Agent 收到 `nothing to claim` 后，没有把它解释为“用户没有额外信息，应自主探索”，而是因为不能再次 ask，频繁退化为 `[wait]`。因此 ask 修复消除了早停，却没有解决缺失目标时的恢复策略。

### 1.8 记忆缺少时效性和一致性

当前 memory 对可见节点覆盖状态和 outgoing edges，对不可见节点保留旧关系，没有 `last_seen_step`、置信度或失效规则。物体被移动、动态隐藏或关系改变后，旧空间关系可能继续参与 LLM 推理。

对于多任务长 episode，这种陈旧关系比单任务更容易累积，可能造成“认为物体已在某处”或重复处理已完成对象。

### 1.9 每步 LLM 调用过多且无缓存

当前每个决策步至少调用：

1. PerceptionFilter LLM；
2. LLMExecutor LLM。

step 0 还会调用 GoalReasoner 和 SDGPlanner；ask 后又重新调用 GoalReasoner 和 SDGPlanner。S3 用时 220.30 秒，S5 用时 360.44 秒。运行中还观察到请求超时、连接错误和一次 invalid prompt，失败回退统一变成 `[wait]`，进一步放大 wait 循环。

### Agent 缺陷结论

当前 RoboState 的核心问题不是 prompt 少写了一条规则，而是缺少多任务控制层。继续只修改 Executor prompt，无法稳定解决任务切换、完成反馈、探索、循环和 grounding 问题。

---

## 2. 测试框架缺陷

### 2.1 Runner 没有向 Agent 提供任务进度

Runner 已经用 `TaskProgressTracker` 检查逐任务条件，但传入 Agent 的 `env_info` 只有：

- step；
- logger；
- action_history；
- hidden_nodes。

代码位置：[evaluation/test_runner.py](../evaluation/test_runner.py#L856)。

`task_id`、任务指令、当前是否满足、完成任务列表都没有进入标准 Agent 接口。Runner 掌握真实进度，Agent 却只能让 LLM从局部图重复推测。

### 2.2 TaskProgressTracker 只增不减

`TaskProgressTracker.update()` 一旦把任务设为 completed，后续不再检查该条件：[evaluation/test_runner.py](../evaluation/test_runner.py#L57)。

对于可逆状态，例如 book 已在 sofa 后又被 grab，`task_completed` 仍保持 true。当前顶层 AND 会检查实时图，所以整个 episode 不会被错误判为全部成功；但部分任务计数可能高估最终状态。

后续应区分：

- `currently_satisfied`：当前图是否满足，用于最终完成数量；
- `first_satisfied_step`：首次满足时间，仅作为原始调试记录；
- `ever_satisfied`：可选诊断字段，不能代替最终完成数量。

### 2.3 初始化过程会改变最终角色出生位置

配置把 character→kitchen 放在第一条 relation override，但 runner 随后使用角色真实执行 walk/grab/putback，把 book、mug、folder、plate 放到指定位置：[evaluation/test_runner.py](../evaluation/test_runner.py#L373)。

因此角色最终停在**最后一个初始化物品的目的地**，而不一定是配置声明的 kitchen：

- S3 最后一项是 folder→desk，episode 很可能从 desk/bedroom 附近开始；运行也确实首先处理 folder。
- S5/S7 最后一项是 plate→kitchencounter，最终回到 kitchen 只是任务顺序造成的巧合。

正确做法是先初始化所有物品，最后再执行 character spawn override，并验证角色 room relation。

### 2.4 Markdown 没有记录真实动作结果

Runner 调用：

```python
logger.write_step(step_count, action_str, None, [])
```

代码位置：[evaluation/test_runner.py](../evaluation/test_runner.py#L923)。

因此 Markdown 中：

- `SDG Status` 永远显示 `No SDG active`；
- `Observed Items` 永远是 0；
- 没有 action_success；
- 没有 Unity error/message；
- 没有当前任务进度。

虽然 Markdown 保存了各模块 reasoning，但不能单独还原动作是否成功，只能结合控制台输出和后续图状态推断。这直接降低失败分析和论文审计能力。

### 2.5 中断运行会留下陈旧最终结果

S7 新运行被中断后，raw Markdown 比 `fail/E_MULTI_S7/metrics.json` 更新，但旧 metrics 仍在 fail 目录中。读取结果目录的人容易把旧版本结果当作当前结果。

Runner 需要：

- 每次运行生成 `run_id`；
- 先写 `status=running`；
- 正常结束后原子更新为 success/fail；
- SIGINT、SIGTERM、timeout 时写 `status=aborted`；
- 结果读取脚本只接受相同 run_id 的完整文件。

### 2.6 运行时会修改原始配置对象

RoboState 在收到澄清后会修改 `config['goal_instruction']`；runner 最后把这个已经修改的 config 保存到结果目录。结果文件因而不一定等于真正启动时的冻结配置，影响复现和 provenance。

应保存：

- `source_config.json`：输入配置的不可变副本和 hash；
- `runtime_state.json`：澄清后的指令等运行态数据；
- `metrics.json`：原始结果。

### 2.7 缺少 Unity 前动作验证层

Runner 会把 `[walk] <closet> (unknown)` 等动作直接交给 Unity。框架需要统一 parser/validator，给所有 Agent 相同的确定性约束和结构化错误，而不是依赖每个 Agent 自己拼字符串。

### 2.8 初始化失败没有统一结果记录

reset 或 apply_overrides 失败时，当前代码会直接 `continue`。这些场景会进入 summary 的 fail 数，但未必生成与普通 episode 一致的 config、原始计数、失败阶段和日志文件，后续统计容易漏项。

### 2.9 success/fail 目录和统计职责混杂

当前 runner 同时：

- 执行场景；
- 计算当前定义不正确的 SR/PS；
- 汇总 aggregate；
- 维护 success/fail 目录。

用户已经明确：runner 只需记录每个场景的任务总数、最终完成任务数、总步数和必要运行状态；SR/PS 之后由独立统计脚本计算。当前 runner 中的 `sr`、`ps`、`aggregate_sr`、`aggregate_ps` 应移除或停止作为权威输出。

### 2.10 Runner 单文件职责过重

`evaluation/test_runner.py` 当前约 1087 行，同时处理 CLI、Unity 生命周期、初始化、动态事件、ask、任务跟踪、日志、归档和统计。继续扩展会增加回归风险，应按模块拆分。

---

## 3. 配置文件缺陷

### 3.1 已确认正确的部分

当前 9 个配置已经满足首批管线验证要求：

- JSON 可解析且自包含；
- 三类 `extension_type` 互斥；
- multi 的顶层 AND 与 `tasks` 一一对应；
- semantic 三份除文本和 instruction type 外保持一致；
- dynamic 三份除难度、触发次数和 max_steps 外保持一致；
- 初始成功条件在修复后的 Unity 预检中为 false；
- dynamic 使用 1/2/3 次重复隐藏，不包含瞬移。

以下问题主要属于论文实验设计与可复现性风险，不表示这 9 个 JSON 当前不可运行。

### 3.2 样本覆盖不足

Semantic 和 Dynamic 都只使用 E1_03、Scene 2、book→sofa。三种难度各只有一个场景，当前只能验证机制，不能区分：

- 指令变异本身的影响；
- 特定 book/sofa 任务的偶然难度；
- Scene 2 布局和实例 ID 的影响。

论文实验阶段至少需要多个源任务、不同动作类型和多个可用场景的平衡样本。

### 3.3 Multi 的规模与任务身份、顺序混杂

S3/S5/S7 使用嵌套集合有利于比较，但同时存在：

- 前三个任务永远出现在指令开头；
- 新增任务只在更大 scale 出现；
- E1_18 本身语义较含糊；
- switchon 类任务与跨房间搬运任务难度不同。

因此结果差异不能完全归因于“指令数量”。需要增加任务顺序轮换和多个等规模组合，或者在论文中明确这是 nested workload，而不是纯 instruction-count 因果实验。

### 3.4 仅按 class 绑定实例，运行间可能选择不同对象

初始化和成功条件主要使用 class + `min_count=1`。Scene 中存在多个同类实例时：

- 初始化可能选择第一个可用实例；
- 某些表面不接受特定物品，runner 会尝试下一个实例；
- 状态 override 可能作用到同类的多个实例；
- 成功条件允许完成任意一个实例。

这对功能测试足够，但论文复现需要把运行时解析出的 subject ID、destination ID 和选择理由写入 manifest。无需把易漂移的 Unity ID硬编码进源 JSON，但必须归档解析结果。

### 3.5 配置没有正式 schema/version

当前缺少：

- `schema_version`；
- 必填字段与互斥字段机器可读约束；
- max_steps 预算策略版本；
- 动态事件语义版本；
- 指令变异生成方法和 provenance。

框架演进后，旧结果难以确认对应哪一版语义。

### 3.6 ask/default clarification 语义未在配置层统一

Multi 配置没有 `user_clarification_reply`，因此使用全局 `nothing to claim`。这不会提供新的任务信息，并且 E1_18 等含糊任务只在 S5/S7 出现，会把“是否触发无信息澄清”混入 scale 对比。

建议配置明确声明：

- `clarification_policy: configured_or_default`；
- 可选的 per-task clarification；
- 默认回复文本版本。

### 3.7 max_steps 策略尚未形成实验协议

Multi 当前使用 `15 × task_count`，Dynamic 使用 `15 + 3 × max_triggers`。这些数值逻辑合理，但需要在 schema/doc 中明确，并验证不同任务的真实最短路径是否相近。否则某些跨房间任务会因为天然路径更长而被 scale budget 不公平截断。

### 3.8 语义变异缺少生成元数据

Semantic 配置记录了 original instruction 和 instruction type，但没有记录：

- 变异方法版本；
- 人工还是模型生成；
- 生成模型/提示词；
- 变异强度；
- 校验者或 source hash。

首批手工配置可以继续使用，但论文复现实验应补充这些 provenance 字段。

---

## 4. 总体下一步修改计划

### 修改原则

1. **Evaluator 是成功条件的唯一真源。** Agent 不复制 condition checker。
2. **多任务拆分为多个任务状态，不再强行生成一个全局 SDG。**
3. **探索和动作校验尽量确定性实现，LLM 只负责高层判断和局部动作选择。**
4. **Runner 只记录原始数据，不计算论文统计指标。**
5. **不向语义变异 Agent 泄露 success condition 的 target/destination。** Runner 可以提供 task ID、原始指令和当前 satisfied 状态，但不把评价条件文本直接放进 prompt。

### Phase 1：先修测试框架契约（P0）

#### 1.1 任务进度接口

Runner 每一步重新检查全部任务，并向所有 Agent 提供标准字段：

```python
env_info["task_progress"] = [
    {
        "task_id": "E1_03",
        "instruction": "...",
        "currently_satisfied": True
    }
]
```

注意：不传 `success_condition`，避免 semantic 模式泄露精确目标。

最终原始结果只保留：

```json
{
  "scenario_id": "E_MULTI_S5",
  "task_total": 5,
  "task_completed": 3,
  "steps_executed": 75,
  "all_success": false,
  "status": "completed",
  "reason": "max_steps"
}
```

#### 1.2 修复初始化顺序

1. 先完成所有非 character 的状态和关系覆盖。
2. 再把 character 移动到配置声明房间。
3. 验证无 HOLDS 残留、所有任务初始为 false、角色 room 正确。
4. 将解析后的实例 ID 写入 `initialization_manifest.json`。

#### 1.3 动作 parser/validator

在 Unity 前增加统一验证：

- 严格 action grammar；
- numeric ID；
- class/ID 一致；
- ID 可见或允许使用已知 memory ID；
- 动作基本 property/precondition；
- 失败返回结构化 `invalid_action`，不让 Unity 接收 `unknown`。

#### 1.4 完整运行日志

每步同时写 Markdown 和 JSONL：

- action；
- action_success / action_message；
- 当前 active task；
- 所有 task 的 currently_satisfied；
- observed/filtered object 摘要；
- SDG focus；
- LLM 延迟和错误；
- dynamic event 状态。

#### 1.5 原子结果生命周期

加入 `run_id`、`status=running/completed/aborted`、配置 hash 和原子写入，消除 S7 这种 raw log 已更新而 metrics 仍是旧版本的问题。

#### 1.6 拆分 runner

建议拆为：

- `evaluation/config_selector.py`
- `evaluation/initialization.py`
- `evaluation/task_progress.py`
- `evaluation/dynamic_runtime.py`
- `evaluation/action_validator.py`
- `evaluation/result_recorder.py`
- `evaluation/test_runner.py`（只负责编排）

### Phase 2：增加 RoboState 多任务控制层（P0）

#### 2.1 新增 MultiTaskManager

建议新增 `agent/robostate/task_manager.py`，内部状态：

```text
TaskState
├── task_id
├── instruction
├── status: pending | active | satisfied | blocked
├── intent
├── sdg
└── retry/loop counters
```

初始化规则：

- multi：从 `config.tasks` 创建多个 TaskState；
- semantic/dynamic/legacy：从顶层 goal 创建一个 synthetic task；
- 每个任务独立生成 intent 和 SDG，可按需 lazy generate；
- 不再把全部编号指令生成一个全局 SDG。

#### 2.2 确定性任务调度

调度优先级：

1. 如果 active task 已由 runner 标记 satisfied，立即冻结并切换。
2. 优先选择目标和 destination 已在 memory 中的未完成任务。
3. 其次选择预计位于当前房间的任务。
4. 都不可见时进入探索状态，而不是 wait。
5. 如果某任务连续失败，暂时切换其他任务，避免阻塞全部任务。

Executor prompt 每次只接收当前 active task 的 intent/SDG，同时接收简短的 pending/satisfied task ID 列表。

#### 2.3 完成任务保护

当任务 currently_satisfied 时：

- 默认禁止对该任务的 target object 执行 grab/switchoff 等可能破坏状态的动作；
- 如果 evaluator 发现状态回退，再将任务重新置为 pending；
- 不再依赖 LLM 自报 `satisfied_nodes` 决定任务是否完成。

### Phase 3：补齐探索、循环恢复和 grounding（P0/P1）

#### 3.1 Room Frontier Explorer

新增确定性探索策略：

- 维护 visited rooms 和 last_seen(class→room/id)；
- active task 所需类不可见时，依次搜索未访问房间；
- 所有房间访问后再使用替代对象或一次 ask；
- `nothing to claim` 表示“无额外信息，继续自主搜索”。

#### 3.2 严格限制 wait

只有以下情况允许 wait：

- `hidden_nodes` 中存在 active task 目标；
- active global rule 明确要求等待；
- 已知动态事件尚未到重现 step。

普通“对象未见”“不知道位置”“没有可执行动作”必须转为 explore/task switch，不允许 wait。

#### 3.3 Loop Detector

检测：

- 连续 wait；
- 相同动作/对象重复；
- 已完成任务被重新操作；
- 相同 Unity error 重复。

触发后依次执行：重新 grounding → 切换任务 → 探索新房间；不直接 ask 或无限 wait。

#### 3.4 降低 LLM 调用

- 从 task instruction/SDG 确定性提取 required classes，并缓存；
- 只有图中类别集合发生变化时才重新运行 PerceptionFilter；
- GoalReasoner/SDG 每个任务只生成一次，除非收到有效澄清；
- API 错误不直接消费成普通 wait，应记录为 infrastructure retry。

### Phase 4：配置协议与实验设计（P1）

1. 增加 JSON Schema 和 `schema_version`。
2. 增加 runtime binding manifest，不在源配置硬编码不稳定 ID。
3. Multi 增加任务顺序轮换和同 scale 的多个平衡组合。
4. Semantic/Dynamic 扩展到多个源任务和动作类型。
5. 增加 mutation provenance、clarification policy、budget policy。

### Phase 5：分阶段恢复测试

#### 5.1 无 Unity 单元测试

- task 状态重新计算与状态回退；
- scheduler 切换；
- wait gating；
- loop detector；
- action parser/validator；
- dynamic hide 1/2/3 次时序；
- 中断结果生命周期。

#### 5.2 Unity 初始化 smoke test

- Scene 2 对象绑定正确；
- 所有初始成功条件为 false；
- 角色最终在配置房间；
- 无手持残留；
- 不调用 `expand_scene` 或手工 `add_character`。

#### 5.3 先只跑 S3

验收条件：

- 不出现 unknown/?? ID；
- 非动态条件下不连续 wait；
- 完成任务不被重复破坏；
- Agent 能从缺失目标转为房间探索；
- Markdown/JSONL 能完整还原每一步；
- 原始结果正确记录 task_total、task_completed、steps_executed。

#### 5.4 再扩展 S5/S7

验证任务调度随规模增长仍稳定，重点观察：

- 各任务是否都获得执行机会；
- 任务完成后是否正确切换；
- wait 和重复动作比例是否显著下降；
- 中断和超时是否产生一致结果。

#### 5.5 最后运行 Semantic/Dynamic

- Semantic：确保 Agent 没有从 evaluator 条件获得精确 book/sofa 泄露。
- Dynamic：验证每次 grab 当步失败、隐藏两个完整决策步、第三步前重现并重新武装。

## 推荐实施顺序

按照依赖关系，建议下一轮按以下顺序修改：

1. 修复初始化后 character 位置、TaskProgressTracker 实时状态和原始结果格式。
2. 把 task_progress 接入标准 Agent `env_info`。
3. 实现 `MultiTaskManager`，按任务独立生成 SDG。
4. 实现 Room Frontier Explorer、wait gating 和 Loop Detector。
5. 增加动作 validator、完整 JSONL/Markdown 和 run lifecycle。
6. 用 S3 做小步回归，稳定后再跑 S5/S7。
7. 扩展配置样本，最后进行 Semantic/Dynamic 全量实验。

最重要的第一步不是继续强化 prompt，而是建立“Evaluator 任务状态 → MultiTaskManager → 单任务 SDG → 探索/执行 → Evaluator 重新验证”的闭环。
