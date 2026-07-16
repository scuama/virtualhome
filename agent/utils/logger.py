import json
import os

class AgentLogger:
    def __init__(self, log_mode="text", scenario_id="", log_dir=None):
        self.log_mode = log_mode
        if not log_dir:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            log_dir = os.path.join(base_dir, "..", "..", "evaluation", "logs")
        
        os.makedirs(log_dir, exist_ok=True)
        prefix = f"run_{scenario_id}" if scenario_id else "run_log"
        self.log_file = os.path.join(log_dir, f"{prefix}.md")
        
        # Initialize markdown file
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write("# 🚀 VirtualHome Agent Episode Log\n\n")
            
    def info(self, msg):
        print(f"INFO: {msg}")
        
    def log_info(self, msg):
        self.info(msg)
        
    def error(self, msg):
        print(f"ERROR: {msg}")
        
    def log_error(self, msg):
        self.error(msg)
        
    def log_module_output(self, module_name, step, output_data):
        with open(self.log_file, "a", encoding="utf-8") as f:
            if isinstance(output_data, str):
                formatted_data = output_data
            else:
                formatted_data = json.dumps(output_data, ensure_ascii=False, indent=2)
            f.write(f"\n### [{module_name}] Output\n```json\n{formatted_data}\n```\n")
        
    def write_step(self, step, action, sdg, observed_items, current_node_focus=None, satisfied_nodes=None):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"## Step {step}\n")
            f.write(f"- **Action**: `{action}`\n")
            
            # Always output the Mermaid graph for SDG
            f.write(f"- **SDG Status**:\n")
            if sdg:
                f.write(f"```mermaid\n{self._generate_mermaid(sdg, current_node_focus, satisfied_nodes)}\n```\n")
            else:
                f.write("No SDG active.\n")
                
            f.write(f"- **Observed Items ({len(observed_items)})**: {', '.join(observed_items[:15])}{'...' if len(observed_items) > 15 else ''}\n")
            f.write("\n")

    def _generate_mermaid(self, sdg, current_node_focus=None, satisfied_nodes=None):
        if satisfied_nodes is None:
            satisfied_nodes = []
            
        lines = ["graph TD"]
        nodes = sdg.get("nodes", [])
        edges = sdg.get("edges", [])

        for node in nodes:
            nid = node["id"]
            if node["type"] == "State":
                label = f"{node['object']}<br>({node['value']})"
            elif node["type"] == "Relation":
                label = f"{node.get('object', '')}<br>{node.get('relation', node.get('state', node.get('value', '')))}<br>{node.get('target', '')}"
            else:
                label = f"{node['object']}"
            
            # Escape quotes in label to avoid syntax errors
            label = label.replace('"', '\\"')
            
            style_str = ""
            if current_node_focus and nid == current_node_focus:
                style_str = f"\n    style {nid} fill:#ff9,stroke:#333,stroke-width:4px"
            elif nid in satisfied_nodes:
                style_str = f"\n    style {nid} fill:#9f9,stroke:#333,stroke-width:2px"
                
            lines.append(f'    {nid}["{label}"]{style_str}')

        for edge in edges:
            reason = edge.get('reason', '')
            reason = reason.replace('"', '\\"')
            lines.append(f'    {edge["from"]} -->|"{reason}"| {edge["to"]}')
        return "\n".join(lines)
