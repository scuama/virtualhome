# VirtualHome Agent 接入最佳实践指南

本指南介绍了如何将一个新的 Agent 接入到重构后的 VirtualHome 测试框架中，并确保其符合“纯粹决策者”的架构规范。

## 1. 核心架构原则

为了保持客户端（Agent）与服务端（UnityEnvironment）的严格解耦，新接入的 Agent 必须遵守以下原则：
- **纯粹的“感知-决策-行动”边界**：Agent **绝对不能**在代码内部修改环境状态（如调用 `expand_scene`，篡改 Node 的 `states` 或 `properties`，或自行处理 `sabotage` 逻辑）。所有的环境规则拦截和超时判定均由 `test_runner.py` 负责。
- **无状态/弱状态依赖**：Agent 内部不要自行维护 `self.step` 或是私有 `action_history`，而应始终从外层框架传入的 `env_info` 字典中读取当前的真实上下文。

## 2. 编写 Agent 类

1. 在 `agent/` 目录下创建一个新的 Python 文件（例如 `my_custom_agent.py`）。
2. 创建一个继承自 `BaseAgent` 的类，并实现 `get_action` 方法：

```python
from .base_agent import BaseAgent

class MyCustomAgent(BaseAgent):
    def __init__(self, model_name: str = "gpt-4o-mini", scenario_id: str = ""):
        # 初始化大模型客户端、自定义配置等
        pass

    def get_action(self, obs: dict, config: dict, env_info: dict = None) -> str:
        """
        核心决策逻辑
        :param obs: 环境观察，包含当前可见的 graph (nodes, edges)
        :param config: 任务配置，包含 goal_instruction 等
        :param env_info: 运行时上下文，包含 step, action_history, active_hidden_nodes 等
        :return: 返回决策动作字符串，例如 "[walk] <character> (1)"
        """
        env_info = env_info or {}
        
        # 1. 遵守规范：从 env_info 读取框架维护的上下文
        current_step = env_info.get("step", 0)
        action_history = env_info.get("action_history", [])
        
        goal = config.get("goal_instruction", "")

        # 2. 你的核心决策逻辑（如通过大模型推理）
        # action = self.llm_infer(...)
        action = "[walk] <character> (1)"  # 示例
        
        return action
```

## 3. 注册 Agent

在 `agent/__init__.py` 中导入你的 Agent，并将其注册到 `AGENT_REGISTRY` 字典中：

```python
# agent/__init__.py
from .my_custom_agent import MyCustomAgent

AGENT_REGISTRY = {
    'robostate': RoboStateAgent,
    'saycan': SayCanAgent,
    'llm_planner': LLMPlannerAgent,
    'my_custom': MyCustomAgent  # <--- 注册你的新 Agent
}
```

## 4. 运行简单测试

接入并注册完毕后，你可以通过 `test_runner.py` 运行最简单的测试场景（例如 ExRAP 测试集中的 `E1_01`）来验证你的 Agent。

在终端中执行：
```bash
python evaluation/test_runner.py \
  evaluation/configs/source_tasks/exrap/E1_01.json \
  --method my_custom --force
```

- `E1_01`: 测试场景的 ID（也可以传入配置文件的完整路径）。
- `--method my_custom`: 指定使用你刚才注册的 Agent。
- `--force`: （可选）忽略并覆盖已有的成功日志记录，强制重新运行该场景，方便反复调试。

## 5. 交互与提问机制 (QA)

如果你的 Agent 支持提问求助（输出 `[ask]` 动作），请注意新架构的处理规范：
- **禁止私自修改环境与配置**：Agent 内部不要拦截 `[ask]` 来修改 `config['goal_instruction']` 或返回假动作，应直接原样返回 `[ask] ...` 动作字符串。
- **由框架自动反馈**：框架拦截到 `[ask]` 后，若 `config` 存在 `user_clarification_reply`，会自动将其作为成功动作的 `message` 记入 `action_history` 并传给下一步。Agent 在下一回合的 `env_info` 中读取回复即可；若不存在预设回复，则按 `on_ask_policy` (SUCCESS/FAIL) 立即结束测试。

## 6. 调试建议

- 测试框架 `test_runner.py` 会自动检测并管理 Unity 后台进程。如果未启动或在运行中发生崩溃，框架会自动通过 `--unity-path` 参数（或默认路径）重新拉起 8080 端口服务端，无需手动干预。
