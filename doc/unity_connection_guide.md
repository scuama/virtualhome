# VirtualHome Unity 引擎连接与通讯最佳实践指南

为了在无外设（headless）的服务器环境中稳定运行 VirtualHome 物理引擎，并避免因频繁拉起导致僵尸进程堆积、8080 端口被占满以及 `Desktop is 0 x 0 @ 0 Hz` 等致命卡死错误，我们**必须严格采用 Client-Server 分离架构**。

## 1. 架构原则
- **Server 端**：作为常驻守护进程运行在后台，负责真正的物理模拟与 3D 渲染，监听本地 8080 端口。
- **Client 端**：也就是我们的 Python Agent 算法端。Agent 代码不应该负责启动或杀死 Unity 引擎，而应该只负责通过 HTTP 请求去连接和通讯。

---

## 2. Server 端的启动步骤

由于服务器没有物理显示器，我们必须使用 `Xvfb` (X virtual framebuffer) 提供虚拟显示服务。请在 tmux session 中或使用 `nohup`/`&` 启动：

```bash
# 杀掉以前残留的僵尸进程（如果有的话）
killall -9 linux_exec.v2.3.0.x86_64
killall -9 Xvfb

# 使用 xvfb-run 拉起引擎，并暴露 8080 端口
xvfb-run -a /mnt/disk1/decom/virtualhome/virtualhome/simulation/unity_simulator/linux_exec.v2.3.0.x86_64 -batchmode -http-port=8080 > unity.log 2>&1 &
```
启动后，Unity Server 就会作为一个常驻进程一直跑在后台。

---

## 3. Client 端 (Python Agent) 的连接姿势

在编写测试脚本或修改 `core_agent.py` 时，**必须显式传入 `executable_args={'file_name': None}`**。
如果不传或传了文件路径，`UnityCommunication` 库的底层机制（`comm_unity.py`）会默认尝试重新拉起一个新的可执行文件实例，这会瞬间导致资源冲突和卡死。

**正确的代码样例：**
```python
from virtualhome.simulation.environment.unity_environment import UnityEnvironment

def init_env():
    # 关键：file_name 必须是 None，这告诉 API 直接去连 localhost:8080
    exec_args = {'file_name': None}
    
    env = UnityEnvironment(
        num_agents=1, 
        observation_types=['partial'], # 或 'graph'
        executable_args=exec_args
    )
    
    # 连接成功后即可正常复位环境
    env.reset(environment_id=1)
    return env
```

---

## 4. 与 Unity 物理环境交互的致命暗坑 ⚠️

**核心铁律：绝对不要使用 `expand_scene` 和 `add_character` 接口！**

在尝试动态修改环境（例如无中生有地添加缺失物品或强行指定坐标）时，请务必遵守以下最佳实践与禁忌：

1. **NavMesh (导航网格) 瘫痪陷阱**：
   **一定不要做**：使用 `env.comm.expand_scene(graph)` 去刷新场景。
   **原因**：VirtualHome 引擎底层在销毁和重建环境时，存在严重的 C# Bug，**它会丢失人物的 NavMesh 寻路网格绑定**。只要调用过一次 `expand_scene`，场景里的角色就会彻底变成无法寻路的“植物人”。此后的任何物理 `[walk]` 操作都会抛出底层空指针异常，导致 8080 端口服务端彻底死锁。
2. **正确的物品摆放姿势**：
   **最佳实践**：如果需要在测试前把某物品放到指定位置，**必须老老实实地通过物理引擎搬运**。例如，编写初始化脚本让角色走过去（`[walk]`）、抓起来（`[grab]`）、再走过去放下来（`[putback]` / `[putin]`）。
3. **应对物品先天缺失**：
   **一定不要做**：试图用 Graph API 强行生成当前场景里根本没有的预制体（Prefab）。
   **最佳实践**：如果你需要的物品在当前场景里找不到（即缺失该预制体），**直接抛出异常并换一个地图（Environment ID）**。强行生成无效物品只会让节点神秘消失或崩溃。
4. **引擎会没收自定义状态 (需 Monkey Patch 补救)**：
   **最佳实践**：Unity 引擎只认它内置的原生状态（如 `OPEN`, `ON`）。如果在 Python 端扩展了自定义逻辑状态（比如 `BROKEN`）或我们自己扩展的动作属性，引擎是不认的。如果需要这些状态，必须在 Python 端写一个 Monkey Patch（猴子补丁），每次从环境获取状态图（`get_graph`）后，在代码层面将这些自定义状态强行缝合进去。

---

## 5. 调试与排障
- **辟谣 `env.close()` 的危害**：有传言说不要调用 `env.close()` 否则会杀死 Server。实际上源码中 `env.close()` 只是关闭了 Python 端的 local launcher 句柄，只要 `file_name=None`，它什么都不会做，是绝对安全的。
- **防止僵尸态（Zombie State）**：不要写出在短时间（如 1 分钟内）进行几百次深度 `env.reset(0)` 的死循环遍历代码。过高频率的资源重载会导致 Unity 服务器的内存分配器锁死，引发 `Connection Refused`，此时只能去 Server 端杀掉重启。
- **测试端口连通性**：如果 Agent 一直报连接被拒绝，可以在服务器终端直接运行 `curl http://127.0.0.1:8080/`。如果很快退出且没有任何输出，说明 8080 端口的 Unity 存活。如果卡死或报错，说明 Server 挂了，需回到第一步重启。
