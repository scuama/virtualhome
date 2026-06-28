# VirtualHome 具身智能动作指令集手册

本文档汇总了当前系统中 Agent 可以执行的所有动作指令。根据系统底层的支持情况与我们的代码重构，动作库现已划分为三大类别：**纯原生动作**、**半原生补丁动作**，以及**纯补充高级动作**。

---

## 1. 纯原生环境动作 (Pure Native Actions)
这些动作由 VirtualHome 引擎原生提供，物理交互、动画渲染和内部图数据 (Graph) 更新完全由 Unity 底层独立处理，不存在任何 Python 层的干预。

### 移动与抓取
*   **[walk]**
    *   **语法**: `[walk] <object_class> (<object_id>)`
    *   **作用**: 移动到指定物体旁边，使其处于 `CLOSE`（靠近）状态。
    *   **注意**: 这是绝大多数交互的**刚性前置条件**。
*   **[grab]**
    *   **语法**: `[grab] <object_class> (<object_id>)`
    *   **作用**: 捡起/抓取物品，建立 `HOLDS` 关系。
    *   **前置**: 必须先 `[walk]` 靠近目标。

### 放置与收纳
*   **[putin]**
    *   **语法**: `[putin] <object_class> (<object_id>) <container_class> (<container_id>)`
    *   **作用**: 将手中物品放入容器内。
    *   **前置**: 必须正手持被放物品；容器必须处于 `OPEN`（打开）状态。
*   **[putback]**
    *   **语法**: `[putback] <object_class> (<object_id>) <surface_class> (<surface_id>)`
    *   **作用**: 将手中物品放置在平面（如桌子、床）上。
    *   **前置**: 必须正手持被放物品。

### 容器开合
*   **[open] / [close]**
    *   **语法**: `[open] <object_class> (<id>)` / `[close] <object_class> (<id>)`
    *   **作用**: 打开/关闭容器（如冰箱、抽屉）或门。
    *   **前置**: 必须 `[walk]` 靠近。

---

## 2. 半原生补丁动作 (Semi-Native Patched Actions)
这类动作的指令在原生引擎中是存在的，但由于底层 Unity 引擎在处理特定电气设备的交互时存在恶性 Bug（常出现 "Requested value was not found" 等导致报错或失效的问题），我们**使用 Python 在接口层接管了它们的状态转移**，模拟其执行成功以填补引擎漏洞。

### 开关与插拔
*   **[switchon] / [switchoff]**
    *   **语法**: `[switchon] <object_class> (<id>)` / `[switchoff] <object_class> (<id>)`
    *   **作用**: 开启或关闭电器（在图节点中赋予 `ON`/`OFF` 状态）。
    *   **前置**: 物品必须具有 `HAS_SWITCH` 属性；如果是需要插电的电器，必须已处于 `PLUGGED_IN` 状态。
*   **[plugin] / [plugout]**
    *   **语法**: `[plugin] <object_class> (<id>)` / `[plugout] <object_class> (<id>)`
    *   **作用**: 插上或拔下电器插头（赋予 `PLUGGED_IN`/`PLUGGED_OUT` 状态）。
    *   **前置**: 物品必须具有 `HAS_PLUG` 属性。

---

## 3. 纯补充高级动作 (Mocked Extension Actions)
由于原生引擎缺乏复杂的物质转移与精细状态追踪机制（没有 SLICED、FILLED、DIRTY转移），我们从零开始，通过 Python 拦截层独创了以下高级动作。这些动作具备极高的推理深度，包含了**严格的物理前提检查和脏污闭环逻辑**。

### 液体转移与清空
*   **[pour]**
    *   **语法**: `[pour] <source_class> (<source_id>) <target_class> (<target_id>)`
    *   **模式 A：转移液体**
        *   **用法**: 将源容器（如牛奶）里的液体倒入目标容器（如马克杯）。
        *   **前置**: 源和目标**都必须**具有 `POURABLE` 属性（如两栖类杯子）；Agent 必须手持源容器并靠近目标容器。
        *   **结果**: 目标容器获得内容物状态（如 `"FILLED_MILK"`），失去 `"EMPTY"` 状态。
    *   **模式 B：清空与抛弃**
        *   **用法**: 将容器里的液体倒进下水道清空。
        *   **前置**: 目标物体的类名必须是 `sink`。Agent 必须手持带有液体状态的源容器。
        *   **结果**: 容器被清空（获得 `"EMPTY"`）。**【脏污连动】**：如果倒掉的不是纯水（`"FILLED_WATER"`），容器将自动获得 `"DIRTY"` 状态！

### 清洗脏物
*   **[wash]**
    *   **语法**: `[wash] <object_class> (<object_id>)`
    *   **作用**: 洗净带有 `"DIRTY"` 状态的物品（包括吃完东西的盘子，或者刚刚倒掉牛奶的脏杯子）。
    *   **前置**:
        1. 物品必须是 `GRABBABLE`。
        2. **必须手持**被洗物品。
        3. **必须靠近**水槽 (`sink`) 或洗碗机 (`dishwasher`)。
    *   **结果**: 移除 `"DIRTY"`，添加 `"CLEAN"` 状态。

### 切片加工
*   **[cut]**
    *   **语法**: `[cut] <object_class> (<object_id>)`
    *   *(注：已删除冗余的 `[slice]` 别名，统一使用 `[cut]`)*
    *   **作用**: 将完整的食材（如苹果、面包）切片。
    *   **前置**:
        1. 目标必须具有 `CUTTABLE` 属性。
        2. **必须手持**一把刀 (`knife`)。
        3. **必须靠近**被切的食物（或者直接手持食物）。
    *   **结果**: 目标食物追加获得 `"SLICED"` 状态。
