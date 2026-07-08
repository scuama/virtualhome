# VirtualHome 测试框架快速入门指南

欢迎使用经过全面优化的 VirtualHome 测试框架。本指南旨在为您提供一个清晰的端到端使用流程，带您快速了解如何编写测试、运行测试以及分析结果。

为了避免赘述，本指南将会按需索引 `doc/` 目录下更详尽的专项文档。

---

## 1. 如何编写配置与测试用例

在我们的框架中，所有的测试配置均通过 JSON 格式定义，放置于 `agent/configs/` 的各个系列目录（如 `g_class`, `m_class`, `p_class`）下。

### 1.1 测试配置文件的结构
一个典型的 JSON 配置文件包含以下关键信息：
- **目标指令 (`instruction`)**: 大语言模型需要去理解并完成的任务。
- **环境要求 (`environment_id`)**: 指定要加载的 Unity 地图（场景）。
- **初始化状态覆盖 (`initial_relations_override`)**: 强制设定某些物品的初始位置（非常关键，比如让盘子出现在桌子上）。
- **成功判定条件 (`success_condition`)**: 验证任务是否成功的依据。

### 1.2 编写与生成规则（必读索引）
在动手写配置之前，您必须了解场景的客观物理限制，并且熟悉撰写规范，**请务必参阅以下文档**：
- 📖 [物品摆放规则与配置生成规范](file:///mnt/disk1/decom/virtualhome/doc/config_generation_rules.md)：学习如何编写符合物理引擎限制的配置（例如物品必须放置在正确的支撑物上，不可悬空）。
- 📖 [场景与房间内可用物品清单](file:///mnt/disk1/decom/virtualhome/doc/scene_room_objects_catalog.md)：在编写测试之前，查询对应 `environment_id` 的场景里到底有哪些真实的物品供您使用。
- 📖 [全局配置说明](file:///mnt/disk1/decom/virtualhome/doc/config.md)：查看更详细的系统配置字段含义。

---

## 2. 如何运行测试

测试框架采用 Client-Server 分离架构运行：

### 2.1 启动 Unity 服务端 (Server)
物理引擎**必须作为常驻进程提前在后台拉起**。
- 📖 [Unity 引擎连接与通讯最佳实践](file:///mnt/disk1/decom/virtualhome/doc/unity_connection_guide.md)：这篇文档包含了启动引擎的 Bash 命令（使用 `xvfb-run`）以及排障方法。请在运行任何 Python 测试前，确保 8080 端口存活。

### 2.2 启动自动化测试 (Client)
引擎就绪后，您可以调用测试运行器。主入口脚本为 `agent/test_runner.py`。

- **运行指定的单个用例**：
  ```bash
  # 指定前缀或具体的 ID
  python3 agent/test_runner.py M1_01
  python3 agent/test_runner.py P3_12
  ```

- **批量运行**：
  ```bash
  # 运行所有 G 系列
  python3 agent/test_runner.py G
  # 运行所有配置
  python3 agent/test_runner.py
  ```

**运行状态监控**：测试命令执行后会进入后台并提示您查看日志文件。使用以下命令可以实时查看 Agent 执行进度：
```bash
tail -f agent/logs/test_runner.log
```

---

## 3. 如何查看测试结果

当一个用例（例如 `M1_01`）运行结束后，框架会自动进行以下归档操作：

### 3.1 成功记录归档
所有跑通的测试记录会被写入到 `agent/results/success/<Test_ID>/` 目录中：
- **`run_<Test_ID>.md`**: 这是一份详尽的 Markdown 格式日志！里面记录了整个思考链（Chain of Thought）、感知到的场景图压缩结果，以及每一步执行的具体物理动作序列。这是进行复盘和调试的最佳产物。
- **`config.json`**: 被锁定的当时的配置快照。

### 3.2 动作词典参考
如果您在看结果报告时，对 Agent 吐出的动作格式（如 `[grab] <apple> (id)` 或 `[putback] <apple> (id) <table> (id)`）感到疑惑，可以参考：
- 📖 [可用物理动作与手册](file:///mnt/disk1/decom/virtualhome/doc/action_manual.md)

---

## 4. 常见问题排障

1. **ConnectionRefusedError: [Errno 111] Connection refused**：
   - 物理引擎挂了或未启动。参见 [unity_connection_guide.md](file:///mnt/disk1/decom/virtualhome/doc/unity_connection_guide.md) 重启服务端。
2. **底层环境死锁 / NavMesh 瘫痪**：
   - 这是由于调用了非法的 `expand_scene` 导致，请牢记永远不要使用代码创建物品，所有状态应该在初始化 JSON 中解决。
3. **Agent 跑了几步之后不停地输出无意义指令或死循环**：
   - 请查看 Agent 的提示词逻辑或打开 `run_<Test_ID>.md` 检查它的规划（SDG）是否脱离了物理实际，尝试通过调整提示词让它进行更严格的自反思（Self-verification）。
