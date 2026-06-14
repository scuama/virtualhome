# VirtualHome Unity 引擎连接最佳实践指南

为了在无外设（headless）的服务器环境中稳定运行 VirtualHome 物理引擎，并避免因频繁拉起导致僵尸进程堆积、8080 端口被占满以及 `Desktop is 0 x 0 @ 0 Hz` 等致命卡死错误，我们**必须严格采用 Client-Server 分离架构**。

## 架构原则
- **Server 端**：作为常驻守护进程运行在后台，负责真正的物理模拟与 3D 渲染，监听本地 8080 端口。
- **Client 端**：也就是我们的 Python Agent 算法端。Agent 代码不应该负责启动或杀死 Unity 引擎，而应该只负责通过 HTTP 请求去连接和通讯。

---

## 具体操作步骤

### 第一步：在后台（或 Tmux）启动 Unity Server
由于服务器没有物理显示器，我们必须使用 `Xvfb` (X virtual framebuffer) 提供虚拟显示服务。请在 tmux session 中或使用 `nohup`/`&` 启动：

```bash
# 杀掉以前残留的僵尸进程（如果有的话）
killall -9 linux_exec.v2.3.0.x86_64
killall -9 Xvfb

# 使用 xvfb-run 拉起引擎，并暴露 8080 端口
xvfb-run -a /mnt/disk1/decom/virtualhome/virtualhome/simulation/unity_simulator/linux_exec.v2.3.0.x86_64 -batchmode -http-port=8080 > unity.log 2>&1 &
```
启动后，Unity Server 就会作为一个常驻进程一直跑在后台。

### 第二步：Client 端 (Python Agent) 的正确连接姿势
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

## 避坑提示
1. **不要在代码中 `env.close()` 随意结束进程**：如果 Client 和 Server 分离，`env.close()` 可能向 8080 端口发送关闭指令，导致你必须重新去控制台手动拉起 Server。调试时应尽量复用环境。
2. **测试端口连通性**：如果 Agent 一直报连接被拒绝，可以在服务器终端直接运行 `curl http://127.0.0.1:8080/`。如果很快退出且没有任何输出，说明 8080 端口的 Unity 存活。如果卡死或报 `Connection refused`，说明 Server 挂了，需回到第一步重启。
