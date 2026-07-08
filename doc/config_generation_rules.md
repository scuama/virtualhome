# VirtualHome 场景配置生成与最佳实践规范

本文档旨在为 AI Agent（或开发者）基于初步设想（如 `doc/config.md`）生成完整的 `.json` 配置文件提供核心规则和最佳实践。请在编写配置时**严格遵守**以下约束，以确保配置能成功被 Unity 引擎加载并执行。
## 0. 语言与指令 (Language & Instructions)
- **强制英文**：配置中的 `goal_instruction` 必须全部使用英文（例如：`If there is an apple in the fridge, take two and put them on the table.`），因为大模型对于英文指令的语义理解和指代消解更加精准。

## 1. 场景与物品一致性 (Scene & Objects Consistency)
- **环境优先**：每个配置必须首先选定 `environment_id` (0-6) 以及具体房间。
- **目录为准**：在配置任何物品之前，**必须**查阅 `doc/scene_room_objects_catalog.md`。
- **禁止捏造**：**绝不允许**生成或使用场景目录中不存在的物品名称。严格使用目录中列出的英文名称（且推荐全小写），例如 `coffeetable`, `remotecontrol`，不要使用 `coffee_table` 或 `Remote`。

## 2. 初始物理关系约束 (Physical Initialization Rules)
- **禁止直接放入房间**：在编写 `initial_relations_override` 时，**严禁**将物品直接设置为属于某个房间（例如 `{"subject": "apple", "relation": "INSIDE", "object": "livingroom"}` 是非法的，会导致引擎死锁崩溃）。
- **依托具体支撑物**：物品必须被精确地放置在房间内的具体家具表面或容器内部。例如：放置于 `ON tvstand` 或 `INSIDE kitchencabinet`。

## 3. 成功条件配置 (Success Conditions)
- **极简画像漏斗模式 (Unified Funnel Schema)**：在配置 `success_condition` 时，引擎完全基于“节点特征与关联边”进行全盘扫描。
- **支持的约束维度**：
  - `target_class` / `destination_class`: 可以指定具体物品名称，或使用 `"ANY"` 代表匹配任何物品（泛型匹配）。
  - `states` / `destination_states`: 用于约束主语/宾语的动态状态（如 `["HOT"]`, `["DIRTY"]`, `["FILLED_JUICE"]`）。
  - `properties` / `destination_properties`: 用于约束主语/宾语的静态固有属性（如 `["POURABLE"]`）。
  - `relation`: 约束主语到宾语的有向动作边（支持正则 `|`，例如 `"HOLDS_RH|HOLDS_LH"` 代表左手或右手均可）。
  - `require_ask_to_pass`: (布尔值) 如果任务规定必须先通过 `[ask]` 澄清需求才能成功，需要设置为 `true`。

## 3.5 最佳实践范例 (Best Practice Example)
为了展示泛化匹配能力，假设我们需要配置一个任务：“给用户倒一杯装满果汁的饮料（且不在乎是用什么容器装的）”。
最优的配置写法如下：

```json
    "success_condition": {
        "target_class": "character",
        "relation": "HOLDS_RH|HOLDS_LH",
        "destination_class": "ANY",
        "destination_properties": ["POURABLE"],
        "destination_states": ["FILLED_JUICE"],
        "min_count": 1
    }
```
**解析**：引擎会首先找出名为 `character` 的主体，查验它是否有伸向其它物体的 `HOLDS_RH` 或 `HOLDS_LH` 的边。接着顺着这条边去检查那个被拿在手里的物体（`ANY` 代表忽略其具体的 class 名字），只要该物体具备 `POURABLE` 属性（证明它是个容器）且其内部状态为 `FILLED_JUICE`，即刻判定任务成功。

## 4. 动态事件的高级使用 (Dynamic Events)
- 当需要测试大模型的感知和适应能力时，可以合理使用 `dynamic_events`。
- 支持的 `trigger` 包括 `"step"` 和 `"distance"`。
- 支持的 `action` 包括 `"hide"`（隐藏物体）、`"teleport"`（瞬移物体）和 `"add_rule"`（运行时增加指令约束）。

## 5. 务实验证原则 (Pragmatic Validation)
- `doc/config.md` 往往只是设计层面的初步草案。
- **一切以实际为准**：在生成最终 JSON 并在 `test_runner.py` 中测试时，允许对初步计划进行大修。如果发现草案中的物品在所选环境中不存在，请直接更换为类似物品或更换场景，不要硬行强求。
