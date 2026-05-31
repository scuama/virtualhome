# VirtualHome 任务配置指南 (Task Configuration Guide)

为了让其他研究人员或开发者能够快速上手构造 Agent 的评测任务，我们将所有的任务环境初始化、动态干扰规则以及目标判定都抽象为了 JSON 配置文件。

本指南将教你如何编写一个规范的 `task_*.json`，并深入解析我们的配置体系所支持的三大核心任务类型。

---

## 一、 配置文件基本结构

每个 JSON 配置文件都必须包含以下基础结构：

```json
{
  "task_name": "HeatMilk_BrokenMicrowave",  // 任务的唯一名称
  "task_type": "impossible",                // 任务类型（决定了评测的侧重点）
  "scene_id": 1,                            // VirtualHome 初始场景编号 (1~7)
  "instruction": "I want to drink hot milk.",// 给 Agent 接收的自然语言指令
  "max_steps": 50,                          // 允许的最大步数（防死循环）
  
  // (可选) 初始环境修饰器：在第 0 步强行修改物理引擎的物体属性
  "init_graph_modifiers": [
    {
      "target": "microwave",
      "action": "remove_property",          // 支持 add_property 或 remove_property
      "property": "CAN_OPEN"
    }
  ],
  
  // (可选) 动态触发器：在特定条件满足时触发环境或 NPC 干扰
  "triggers": [
    {
      "condition": "lambda time_step: time_step == 15",
      "event_type": "graph_injection",
      "target_node": "tv",
      "action": "inject_property('ON')"
    }
  ],
  
  // 目标判定条件
  "goal": {
    "target_node_contains": "milk",
    "required_state": "hot"
  }
}
```

---

## 二、 推荐支持的三种核心类型 (`task_type`)

为了全面评测 Agent 的**意图理解**、**常识推理**和**临场应变**能力，我们的配置文件在设计上支持且仅划分为以下三种核心类型：

### 1. 静态基础任务 (`static`)
这是最传统的具身智能评测任务类型。
* **特点**：环境是友好的、静态的，所需物品全部都在预期的位置。物理引擎不会有任何阻碍。
* **侧重点**：测试 Agent 基础的“指令拆解”和“寻路抓取”能力。
* **配置写法**：`init_graph_modifiers` 和 `triggers` 必须为空。
* **示例**：“去厨房拿个苹果”。（苹果就乖乖放在桌上）

### 2. 先天不可能 / 平替推理任务 (`impossible`)
这是为了测试大模型常识与容错能力的高级任务。
* **特点**：在 Agent 出生前（第 0 步），上帝（测试者）就已经把必需的物品拿走、或者把核心工具弄坏了。
* **侧重点**：测试 Agent 遇到物理死胡同（如 `[Open] <microwave>` 失败）时，能否不崩溃，而是主动触发 Fallback 机制去寻找**平替方案**（例如用平底锅和炉灶加热）。
* **配置写法**：严重依赖 `init_graph_modifiers`。在初始化时对关键物体执行 `remove_property` 或直接删除节点。
* **示例**：“热一杯牛奶”，但微波炉一开始就被设定为门坏了（被移除了 `CAN_OPEN` 属性）。

### 3. 动态干扰 / 重新规划任务 (`dynamic`)
这是最贴近真实物理世界、最难的任务类型。
* **特点**：任务刚开始时一切正常（环境可行），但随着时间推移或 Agent 的移动，突发事件会破坏原定计划。
* **侧重点**：测试 Agent 在执行计划一半时，面对突发状况的**动态重规划（Dynamic Replanning）**能力。
* **配置写法**：严重依赖 `triggers`。使用 `lambda` 表达式绑定时间步或空间距离触发条件，触发时强制修改 Graph（比如 NPC 截胡）。
* **示例**：“去厨房拿桌上的苹果”。当 Agent 走到厨房门口时（触发空间 `distance` 阈值），NPC 突然出现把桌上的苹果吃掉了（节点消失）。Agent 必须立刻重新扫描环境，去打开冰箱找其他的苹果。

---

## 三、 编写新任务的避坑指南

1. **环境探针（Target 名称核对）**
   VirtualHome 对物体名称是严格的。在写 `target: "microwave"` 之前，最好先确认对应 `scene_id` 的场景里到底有没有微波炉，以及它的确切 `class_name` 是什么（有可能是 `microwaveoven`）。

2. **动作连贯性设定**
   当使用 `init_graph_modifiers` 时，剥夺一个物体的 `CAN_OPEN` 会导致引擎不再生成 `[Open]` 技能。您需要在验证脚本（如 `vh_runner.py`）中确保这种底层改动能真实地反馈给 Agent，而不是被外壳代码强行标记为 `action_success = True`。

3. **目标函数不要写死位置**
   `goal` 的设定最好是基于**最终状态**（如 `required_state: "hot"`），而不是基于固定路径（比如要求 Agent 必须走特定路线），因为高智商 Agent 可能会利用常识找到你意想不到的捷径（例如用咖啡机加热水来隔水温牛奶），只要最终状态符合，任务就算成功。
