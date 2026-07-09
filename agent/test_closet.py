import sys
sys.path.insert(0, '/mnt/disk1/decom/virtualhome')

from virtualhome.simulation.environment.unity_environment import UnityEnvironment

# 启动环境（确保 Unity Server 已运行）
env = UnityEnvironment()
env.reset(environment_id=0)  # 可改为 1 或你想测试的场景

# 获取完整的场景图
graph = env.get_graph()

# 遍历所有节点，找出所有 closet 和 microwave
for node in graph['nodes']:
    class_name = node['class_name']
    if class_name in ['closet', 'microwave']:
        print(f"=== {class_name} ID: {node['id']} ===")
        print(f"States: {node.get('states', [])}")
        print(f"Properties: {node.get('properties', [])}")
        print(f"CAN_OPEN in Properties? {'CAN_OPEN' in node.get('properties', [])}")
        print("---")

env.close()