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

## 4. 与 Unity 图形化交互 (Graph API) 的致命暗坑 ⚠️

在调用 `env.comm.expand_scene(graph)` 动态修改环境时，Unity 底层的 JSON 反序列化器极其严苛，稍有不慎就会发生**静默丢弃（不报错但修改无效）**的现象。请务必遵守以下铁律：

1. **`bounding_box` 毒药陷阱**：
   从 `env.comm.environment_graph()` 获取到的节点字典中天然带有 `bounding_box` 字段。**但如果你把带有 `bounding_box` 的图原封不动地发回给 `expand_scene`，Unity 会直接解析崩溃并静默忽略该节点！** 在下发修改图之前，必须写一个 `clean_graph` 函数遍历剔除所有节点的 `bounding_box` 键。
2. **人物 IK 死锁 (IK Deadlock)**：
   在下发修改过的 Graph 之前，**必须确保剔除了所有的 `character` 节点**。如果在带有角色状态的图上强行 `expand_scene`，Unity 底层的逆向运动学 (Inverse Kinematics) 骨骼结算会彻底崩溃，导致角色四肢扭曲或者环境直接卡死。
3. **`category` 属性不可缺失**：
   如果你试图在 Graph 中无中生有（手动 append 节点），**千万不能漏掉 `category` 字段，且必须绝对正确**（例如 `beer` 必须对应 `'Food'`）。传错或漏传，节点将被静默丢弃。
4. **引擎会没收自定义状态 (需 Monkey Patch 补救)**：
   Unity 引擎只认它内置的几种原生状态（如 `OPEN`, `ON`）。如果在下发的图里加上了自定义逻辑状态（比如 `BROKEN`）或我们自己扩展的动作属性（比如拔插头的机制），Unity 在重新渲染后会强行将其清洗为空。**正因为我们在 Graph 逻辑层扩展（Mock）了许多底层不支持的物理逻辑，这就要求我们在 Python 端必须写一个 Monkey Patch（猴子补丁）**。在每次环境获取观测图后，将这些自定义状态强行缝合回字典里。
5. **小心预制体缺失 (Missing Prefabs)**：
   并不是所有在 `.json` 目录里的物品都能被动态生成（例如 `juice`, `apple` 被官方漏打包了）。如果要求 Unity 生成黑名单物品，节点也会神秘消失。

---

## 5. 调试与排障
- **辟谣 `env.close()` 的危害**：有传言说不要调用 `env.close()` 否则会杀死 Server。实际上源码中 `env.close()` 只是关闭了 Python 端的 local launcher 句柄，只要 `file_name=None`，它什么都不会做，是绝对安全的。
- **防止僵尸态（Zombie State）**：不要写出在短时间（如 1 分钟内）进行几百次深度 `env.reset(0)` 的死循环遍历代码。过高频率的资源重载会导致 Unity 服务器的内存分配器锁死，引发 `Connection Refused`，此时只能去 Server 端杀掉重启。
- **测试端口连通性**：如果 Agent 一直报连接被拒绝，可以在服务器终端直接运行 `curl http://127.0.0.1:8080/`。如果很快退出且没有任何输出，说明 8080 端口的 Unity 存活。如果卡死或报错，说明 Server 挂了，需回到第一步重启。
