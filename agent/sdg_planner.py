import json
import networkx as nx
import matplotlib.pyplot as plt
import os
from .llm_client import LLMClient

SDG_SYSTEM_PROMPT = """你是一个具身智能体的 SDG (State Dependency Graph) 规划器。
环境在一个离散的 3D 物理图中。你的任务是将用户的最终意图转化为“状态依赖图”。

### 动作与状态能力限制：
1. 只能使用基础动作带来的状态改变，如走动、拿取、开关门、放入取出、插电、开关电器。
2. 热力学法则（加热）：必须通过将物品放入/放在热源（microwave/oven/toaster/stove）内部/表面，并开启热源（switchon）来实现。且热源必须先有电（plugin）。
3. 容器法则：放入东西前必须先打开（open）。

### 输出格式 (严格 JSON)：
你需要输出一个有向无环图的 JSON 表达。
"nodes": [
    { "id": "N1", "type": "State" | "Relation", "object": "...", "target": "...", "value": "..." }
]
"edges": [
    { "from": "N2", "to": "N1", "reason": "..." } // N2是N1的前置条件
]

节点示例：
- 状态节点：{"id": "N1", "type": "State", "object": "microwave", "value": "ON"}
- 拓扑关系节点：{"id": "N2", "type": "Relation", "object": "milk", "relation": "INSIDE", "target": "microwave"}

你的目标是为用户指令规划完整的倒推依赖链。严格输出规范的 JSON。
"""

class SDGPlanner:
    def __init__(self, llm_client: LLMClient, logger):
        self.llm = llm_client
        self.logger = logger
        self.current_sdg = None

    def generate_sdg(self, goal_description: str) -> dict:
        user_prompt = f"请为以下用户任务生成完整的状态依赖图（SDG）：\n任务：{goal_description}"
        response = self.llm.generate_response(
            system_prompt=SDG_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_format="json_object"
        )
        
        # 处理可能被 markdown 包裹的 JSON
        if response.startswith("```json"):
            response = response[7:-3]
        elif response.startswith("```"):
            response = response[3:-3]
            
        try:
            sdg_data = json.loads(response)
            self.current_sdg = sdg_data
            if self.logger:
                self.logger.log_info(f"Generated SDG with {len(sdg_data.get('nodes', []))} nodes.")
            return sdg_data
        except json.JSONDecodeError as e:
            if self.logger:
                self.logger.log_error(f"SDG JSON 解析失败: {e}\nRaw Response:\n{response}")
            return None

    def generate_mermaid_graph(self) -> str:
        if not self.current_sdg:
            return "No SDG generated yet."

        lines = ["graph TD"]
        nodes = self.current_sdg.get("nodes", [])
        edges = self.current_sdg.get("edges", [])

        for node in nodes:
            nid = node["id"]
            if node["type"] == "State":
                label = f"{node['object']}\\n({node['value']})"
            elif node["type"] == "Relation":
                label = f"{node['object']}\\n{node['relation']}\\n{node.get('target', '')}"
            else:
                label = f"{node['object']}"
            lines.append(f'    {nid}["{label}"]')

        for edge in edges:
            reason = edge.get('reason', '')
            # from -> to means prerequisite -> goal
            lines.append(f'    {edge["from"]} -->|"{reason}"| {edge["to"]}')

        return "\n".join(lines)
