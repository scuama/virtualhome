# VirtualHome 项目 AI 协作规则 (Project Rules)

在处理此 VirtualHome 具身智能项目时，请严格遵守以下规则和约束：

## 1. 核心架构与引擎连接
- **Client-Server 分离**：**严禁**在 Python 脚本的 `UnityEnvironment` 中传入引擎的物理执行路径（`exec_path`）。必须始终使用 `executable_args={'file_name': None}` 来连接 8080 端口服务端，否则会导致引擎内部自带线程管理引发的严重端口占用和死锁。但**允许**测试框架 (`test_runner.py`) 在外部通过干净的 `subprocess` 主动管理（启动/杀死）Unity 独立进程，以保证测试的自动恢复能力。
- 📖 **相关文档索引**：[doc/unity_connection_guide.md](file:///Users/rushy/program/virtualhome/doc/unity_connection_guide.md)

## 2. 场景与物品初始化配置
- **禁止直接放置于房间**：在编写测试用例配置（如 `G2_06.json` 的 `initial_relations_override`）时，**绝不允许**将物品直接设置为 `INSIDE <room_name>`（例如 `INSIDE livingroom`）。
- **具体到支撑物**：必须将物品放置于房间内的具体支撑物或容器上/中（例如 `ON coffeetable` 或 `INSIDE kitchencabinet`）。
- 📖 **相关文档索引**：
  - [doc/scene_room_objects_catalog.md](file:///Users/rushy/program/virtualhome/doc/scene_room_objects_catalog.md) (查阅每个场景和房间中真实可用的物品)
  - [doc/config_generation_rules.md](file:///Users/rushy/program/virtualhome/doc/config_generation_rules.md) (从草案生成正式配置的全面规则与最佳实践)

## 3. 物理动作与宏约束
- **严禁代码作弊 (No Magic Macros)**：不要试图在 Python 代码（如 `LLMExecutor`）中强行硬编码追加 `[walk]` 或 `[grab]` 等前置动作。
- **依赖 Prompt 教学**：必须通过修改 `agent/prompt_templates.py` 中的提示词，严格要求大模型遵守物理约束。例如：要求大模型在输出 `[putin]`、`[putback]`、`[pour]` 之前，必须自行检查其状态是否持有该物品（`HOLDS_RH`/`LH`），若没有则必须在前一步输出 `[walk]` 和 `[grab]`。

## 4. 测试与运行环境
- 运行 `test_runner.py` 需要 `OPENAI_API_KEY` 环境变量。如果终端报错找不到 Key，请确保在执行前先 `source ~/.zshrc` 或正确配置环境变量。

## 5. 测试结果管理
- **禁止清理成功记录**：绝不允许手动或通过命令清理 `evaluation/results/*/success` 目录下的内容。如果需要强制重跑已经成功的用例，请使用 `test_runner.py` 脚本的 `--force` 参数，而不要删除成功记录文件夹。

---
*注：本文件定义了针对本工作区的 AI 行为准则，系统将在后续任务中自动加载并遵循。*
