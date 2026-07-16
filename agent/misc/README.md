# IntentAgent for VirtualHome

针对 [VirtualHome](https://github.com/xavierpuigf/virtualhome) 仿真的**意图推理智能体 (Intent Reasoning Agent)**。
本模块从原 EmbodiedBench 架构平移而来，通过「五层 Why」挖掘深层意图，在目标缺失或物理引擎报错（动作执行失败）时主动挂起并与用户对话，并结合 **EmbodiedLTM**（GraphRAG 长期记忆服务）跨任务积累场景知识与探索状态（如防止死循环探索）。

## 核心特性

1. **环境适配引擎** (`vh_runner.py`)：直接驱动 VirtualHome Unity 物理引擎，实时获取 `partial_graph` 节点及 `available_rooms` 全局房间数据。
2. **五层 “Why” 意图解析** (`goal_reasoner.py`)：对指令进行反思，提取深层意图与可接受的物理替代物。
3. **解空间严格过滤** (`solution_space.py`)：结合环境节点和 LTM `explored_locs` 记忆，利用 LLM 对 VirtualHome `[Action] <Target> (ID)` 语法格式的技能树进行语义与防死循环过滤。
4. **方案排序与决策** (`solution_ranker.py` + `task_validator.py`)：多方案打分排序，选取 Top-1 动作；支持 Action 9999 触发用户对话。
5. **长期记忆** (`memory_manager.py` + `ltm_client.py`)：写入情景记忆、状态更新与 checkpoint。
6. **运行日志** (`logger_utils.py`)：动态创建带时间戳的 `logs/run_YYYYMMDD_HHMMSS/` 目录，每步生成环境截图与决策全量日志。

## 架构与模块依赖

```text
vh_runner.py                 # 入口：连接 VirtualHome Unity，驱动主循环
        │
        ▼
core_agent.py                # 调度：错误恢复 → 意图 → 解空间 → 排序决策
   ├── goal_reasoner.py      # 意图提取（LLM + prompt_templates）
   ├── solution_space.py     # 动作过滤与解析（适配 [Walk] <kitchen> (1) 语法）
   ├── task_validator.py     # 调用 SolutionRanker 选动作
   │     └── solution_ranker.py
   ├── memory_manager.py     # LTM checkpoint
   ├── llm_client.py         # OpenAI 兼容接口
   └── logger_utils.py       # 日志、截图与输出统一落盘
```

## 快速上手

### 步骤 0：启动 VirtualHome Unity 仿真器
由于需要在后台渲染物理环境，首先需要启动 Unity 可执行文件（需配置显卡与显示环境变量）：
```bash
export DISPLAY=:0
export XAUTHORITY=/run/user/1002/gdm/Xauthority
cd /mnt/disk1/decom/virtualhome/virtualhome/simulation/unity_simulator
killall -9 linux_exec.v2.3.0.x86_64 || true
./linux_exec.v2.3.0.x86_64 -screen-fullscreen 0 -screen-quality 4 &
```

### 步骤 1：启动 / 重置 EmbodiedLTM（长期记忆服务）
```bash
cd /mnt/disk1/decom/virtualhome/agent/EmbodiedLTM
source /home/decom/anaconda3/etc/profile.d/conda.sh
conda activate embodiedltm
uvicorn app:app --host 0.0.0.0 --port 8000
```
*(如需清空跨任务污染的记忆图谱，执行 `bash reset_ltm.sh`)*

### 步骤 2：启动 Agent 任务测试
使用 `embench` 环境来运行 Agent 主循环（支持加载 json 任务配置）：
```bash
cd /mnt/disk1/decom/virtualhome/agent
source /home/decom/anaconda3/etc/profile.d/conda.sh
conda activate embench
export DISPLAY=:0
export XAUTHORITY=/run/user/1002/gdm/Xauthority
python vh_runner.py --config configs/task_impossible.json
```

运行产生的日志与交互图像截图会实时写入每次动态创建的 `agent/logs/run_<timestamp>/` 目录中。

## 环境变量配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `EMBODIED_LTM_URL` | `http://127.0.0.1:8000` | EmbodiedLTM 知识图谱服务地址 |
| `OPENAI_API_KEY` | — | LLM 调用的核心鉴权密钥（由 `llm_client.py` 内部使用） |
