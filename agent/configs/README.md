# Agent 测试场景配置说明

当前目录下存放了一系列场景配置文件，用于测试 Agent 在 Embodied AI 环境下的决策与反应能力。
我们重点支持并测试了以下三种具有代表性的场景：

## 1. 持续指令跟随 (Continuous Instruction Following)
**示例配置**：`scenario1_maintenance.json` 以及所有的 `maintenance_xxx.json`
**场景说明**：
Agent 接受一个长期的后台维护类指令（例如：“如果有人看书没收，就把它放好”）。在场景中，会有动态的 NPC 执行动作（例如走过去看书并乱丢在沙发上），或者通过环境注入制造混乱现场。Agent 必须在多步交互中持续观察环境，识别出违反维护规则的现场并去修复它。

## 2. 场景中不可完成的任务，需要寻找替代方案 (Unachievable Task & Alternative Finding)
**示例配置**：`scenario2_missing_item.json`
**场景说明**：
指令要求 Agent 去执行一项在当前物理空间下根本不可能的任务，例如“去卧室拿一个钻石戒指（diamond ring）”。在这个场景中，目标物品在全图都不存在。这主要测试 Agent 的探索容错机制、视觉感知模块的防幻觉能力。Agent 需要在遍历相关区域无果后，通过 `Action 9999` (Proactive Communication) 主动向用户汇报异常，或寻找相近的替代品。

## 3. 人类（NPC）活动导致的意外阻断 (NPC Disruption)
**示例配置**：`scenario3_npc_disruption.json`
**场景说明**：
原本是可以正常完成的任务，但因为环境中其他实体的动态行为导致了意外失败。在 `scenario3` 中，用户的指令是“把馅饼（pie）放进微波炉加热”。原本馅饼在桌子上，大模型规划了一条正常的路径去拿馅饼；但在并发执行时，环境中的 NPC 会抢在大模型之前，跑过去把馅饼拿走并且扔进垃圾桶（trashcan）。这测试了 Agent 能够基于动作失败反馈或视野重判，重新定位被人类转移走的目标，展现出极强的动态环境适应性和重新规划能力。

## 4. 环境运行最佳实践与踩坑记录 (Best Practices & Troubleshooting)

由于 VirtualHome 底层依赖于吃资源的 3D 物理引擎（Unity `linux_exec`），我们在引入多 Agent (NPC) 时遇到了诸多环境卡死与越界报错，总结出以下工业界标准实践与填坑记录：

### 最佳实践：Client-Server 分离模式
**绝对不要**在 Python 测试脚本中通过指定 `file_name` 让代码去后台反复拉起新的 Unity 进程。在无外设（headless）的云服务器中反复拉起引擎极易导致僵尸进程堆积并耗尽 8080 端口，甚至报出 `Desktop is 0 x 0 @ 0 Hz` 永久卡死。
*   **Server 端（引擎守护进程）**：在本地图形界面终端（或搭配 XServer 的 tmux）中，**预先手动运行一次**引擎作为常驻守护进程：
    ```bash
    /mnt/disk1/decom/virtualhome/virtualhome/simulation/unity_simulator/linux_exec.v2.3.0.x86_64 -batchmode -http-port=8080
    ```
*   **Client 端（Python Agent）**：在跑测试代码（如 `vh_runner.py`）时，永远将传入 `UnityEnvironment` 的 `executable_args={'file_name': None}`。这样 Python 会像调用 API 一样直接轻量化连接到 8080 端口，再也不会引发卡死或资源冲突。

### 核心踩坑记录 (Troubleshooting)
1.  **多智能体初始化崩溃 (`IndexError: list index out of range`)**：
    *   **现象**：最初接入 `num_agents=2` 跑 NPC 时，一初始化就崩溃，误以为是引擎不支持两小人。
    *   **真凶**：`vh_runner.py` 初始化时硬编码传了单元素的观测列表 `observation_types=['partial']`。导致在取 NPC（agent 1）的观测类型时触发列表越界。
    *   **修复**：直接移除了 `observation_types` 参数，让源码根据智能体数量自动生成对应长度的列表即可。
2.  **NPC 并发动作报错**：
    *   **现象**：底层的 `utils.py` 解析器如果拿到不带括号的动词会崩溃。
    *   **修复**：对于空闲占位符 `[WAIT]`，在送入 `env.step()` 前已统一过滤并映射为 `None`，完美支持双边智能体的空闲状态。
