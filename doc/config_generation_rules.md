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

## 3. 成功与失败条件 (Conditions Setup)
- **规范字段**：在配置 `success_condition` 时，目前主要支持的 `check_type` 为 `"relation"` 或 `"agent_action"`。
- **关系校验**：对于 `"relation"`，通常必须明确提供 `target_class`（或 `subject`）、`relation`（如 `ON` / `INSIDE`）以及 `destination_class`（或 `object`）。
- **状态要求**：可以通过 `require_target_state` 要求目标物体的特定状态（如电视必须处于 `ON` 状态）。

## 4. 动态事件的高级使用 (Dynamic Events)
- 当需要测试大模型的感知和适应能力时，可以合理使用 `dynamic_events`。
- 支持的 `trigger` 包括 `"step"` 和 `"distance"`。
- 支持的 `action` 包括 `"hide"`（隐藏物体）、`"teleport"`（瞬移物体）和 `"add_rule"`（运行时增加指令约束）。

## 5. 务实验证原则 (Pragmatic Validation)
- `doc/config.md` 往往只是设计层面的初步草案。
- **一切以实际为准**：在生成最终 JSON 并在 `test_runner.py` 中测试时，允许对初步计划进行大修。如果发现草案中的物品在所选环境中不存在，请直接更换为类似物品或更换场景，不要硬行强求。
