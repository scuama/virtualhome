import json
import os
import re
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import numpy as np

from .base_agent import BaseAgent
from .utils.llm_client import LLMClient
from .utils.logger import AgentLogger

# 尝试导入 sentence_transformers，如果没有则使用文本预处理但不做检索
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


FLARE_AGENT_VERSION = "FLARE-VH-v1.0-2026-07-20"


@dataclass
class FlareExample:
    instruction: str
    high_level_plan: str          # 例如 "PickupObject, apple; PutObject, apple, fridge"
    scene_description: str = ""   # 用于相似度匹配的场景描述


class FlareRetriever:
    """简单的句子嵌入检索器，从示例库中选择最相似的 k 个示例。"""
    def __init__(self, examples: List[FlareExample]):
        self.examples = examples
        if SENTENCE_TRANSFORMERS_AVAILABLE and examples:
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            self.example_embeddings = self.encoder.encode(
                [ex.instruction + " " + ex.scene_description for ex in examples]
            )
        else:
            self.encoder = None
            self.example_embeddings = None

    def retrieve(self, query: str, k: int = 5) -> List[FlareExample]:
        if not self.examples:
            return []
        if self.encoder is not None and self.example_embeddings is not None:
            query_emb = self.encoder.encode([query])
            similarities = np.dot(query_emb, self.example_embeddings.T)[0]
            top_indices = np.argsort(similarities)[-k:][::-1]
            return [self.examples[i] for i in top_indices]
        else:
            # Fallback: 随机返回 k 个示例（或不返回）
            return random.sample(self.examples, min(k, len(self.examples)))


class FlareHighLevelExecutor:
    """将 FLARE 的高层动作展开为 VirtualHome 基元动作序列。
    
    支持的动作：ToggleObject, PickupObject, PutObject, HeatObject, CoolObject, CleanObject, SliceObject。
    对象名使用小写，与 VirtualHome 图节点匹配。
    """
    OPENABLE_CLASSES = {'fridge', 'cabinet', 'microwave', 'drawer', 'safe'}
    
    def execute_high_level(self, action: str, obj: str, target: Optional[str] = None) -> List[str]:
        """
        :param action: 高层动作名（如 'ToggleObject'）
        :param obj: 对象类名（小写）
        :param target: 可选的目标容器或接收器（小写）
        :return: VirtualHome 基元动作字符串列表，如 ['[walk] <obj> (id)', '[grab] <obj> (id)']
                  注意：这里只生成动作模板（带类名），具体对象 ID 需要在执行时由观察确定。
                  因此返回的是带占位符的字符串，例如 '[walk] <apple> (?)', 实际 ID 由 Agent 后续动态替换。
                  为简化，我们要求 Agent 在生成基元动作时已经能通过观察找到具体物体 ID。
                  但在此处我们只返回动作模板，由 Agent 在队列管理时根据当前 graph 替换 ID。
        """
        # 暂时返回带有对象类名的抽象动作，实际执行时由 FLAREAgent 解析并替换为具体 ID。
        # 为了便于队列处理，我们返回类似 '[walk] <apple>' 这样的字符串，不含 ID。
        # 最终动作生成会在 FLAREAgent 中完成。
        pass


class FLAREAgent(BaseAgent):
    VERSION = FLARE_AGENT_VERSION
    REQUIRED_OBSERVATION = ['partial']

    def __init__(self, model_name: str = "gpt-5.4-mini", scenario_id: str = ""):
        super().__init__(model_name=model_name, scenario_id=scenario_id)
        self.llm = LLMClient(model_name=model_name)
        self.project_root = Path(__file__).resolve().parents[1]

        # 内部规划状态（非环境上下文）
        self.current_high_plan: List[Tuple[str, str, Optional[str]]] = []  # (action, obj, target)
        self.completed_high_steps: List[str] = []
        self.primitive_queue: List[str] = []
        self.replan_count = 0
        self.max_replans = 5

        # 示例库
        self.examples = self._load_examples()

    def _load_examples(self, path: str = None) -> List[FlareExample]:
        """加载示例库，默认从 agent/flare_examples.json 读取，否则使用内置默认值。"""
        if path is None:
            path = os.path.join(os.path.dirname(__file__), 'flare_examples.json')
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
            return [FlareExample(**item) for item in data]
        else:
            return self._get_default_examples()

    @staticmethod
    def _get_default_examples() -> List[FlareExample]:
        """内置的几个简单示例，确保在没有外部库时也能运行。"""
        return [
            FlareExample(
                instruction="Put the apple in the fridge.",
                high_level_plan="PickupObject, apple; PutObject, apple, fridge",
                scene_description="kitchen with an apple on the counter and a fridge"
            ),
            FlareExample(
                instruction="Heat a potato in the microwave.",
                high_level_plan="PickupObject, potato; HeatObject, potato, microwave",
                scene_description="kitchen with a potato on the table and a microwave"
            ),
            FlareExample(
                instruction="Turn on the tv.",
                high_level_plan="ToggleObject, tv",
                scene_description="living room with a tv and a sofa"
            ),
            FlareExample(
                instruction="Slice the bread and put it on the counter.",
                high_level_plan="PickupObject, bread; SliceObject, bread; PutObject, bread, countertop",
                scene_description="kitchen with a bread loaf and a countertop"
            )
        ]

    def _generate_high_plan(self, goal: str, visible_objects: List[str], action_history: List[dict]) -> List[Tuple[str, str, Optional[str]]]:
        """调用 LLM 生成高层计划，使用 FLARE 风格的 prompt 和检索增强。"""
        # 1. 检索相关示例
        retriever = FlareRetriever(self.examples)
        scene_desc = self._describe_scene(visible_objects)
        query = goal + " " + scene_desc
        few_examples = retriever.retrieve(query, k=3)

        # 2. 构造 prompt
        prompt = self._build_prompt(goal, visible_objects, action_history, few_examples)

        # 3. 调用 LLM
        system = (
            "You are a household robot planner. Given the task instruction, the visible objects, "
            "and the action history, generate a high-level plan using the allowed actions and objects. "
            "Allowed actions: ToggleObject, PickupObject, PutObject, HeatObject, CoolObject, CleanObject, SliceObject.\n"
            "Output each step as 'Action, Object, Target' separated by semicolons. Target is only needed for "
            "PutObject, HeatObject, CoolObject, CleanObject. If no target, leave it empty. "
            "Example: 'PickupObject, apple; PutObject, apple, fridge'. Do not include any explanation."
        )
        raw_output = self.llm.generate_response(system, prompt)

        # 4. 解析计划
        return self._parse_plan(raw_output)

    def _describe_scene(self, visible_objects: List[str]) -> str:
        """用可见物体列表构造简单的场景描述文本。"""
        return "visible objects: " + ", ".join(visible_objects) if visible_objects else "unknown room"

    def _build_prompt(self, goal: str, visible_objects: List[str], action_history: List[dict], few_examples: List[FlareExample]) -> str:
        """构建 FLARE 风格的 prompt，包含 few-shot 示例和当前任务信息。"""
        prompt_parts = []
        # Few-shot 示例
        for i, ex in enumerate(few_examples):
            prompt_parts.append(f"Example {i+1}:\nTask: {ex.instruction}\nScene: {ex.scene_description}\nPlan: {ex.high_level_plan}\n")
        
        # 当前任务
        history_str = self._format_history(action_history)
        prompt_parts.append(
            f"Current Task: {goal}\n"
            f"Scene: {self._describe_scene(visible_objects)}\n"
            f"Action History (last few steps):\n{history_str}\n"
            "Now generate the high-level plan (one line, no extra text):"
        )
        return "\n".join(prompt_parts)

    def _format_history(self, action_history: List[dict]) -> str:
        if not action_history:
            return "No actions yet."
        recent = action_history[-5:]
        lines = []
        for entry in recent:
            lines.append(f"- {entry.get('action', '?')} (success={entry.get('success', '?')})")
        return "\n".join(lines)

    def _parse_plan(self, text: str) -> List[Tuple[str, str, Optional[str]]]:
        """解析高层计划字符串为结构化列表。
        例如: "PickupObject, apple; PutObject, apple, fridge"
        """
        plan = []
        steps = text.split(';')
        for step in steps:
            step = step.strip()
            if not step:
                continue
            parts = [p.strip() for p in step.split(',')]
            if len(parts) == 0:
                continue
            action = parts[0]
            obj = parts[1] if len(parts) > 1 else ""
            target = parts[2] if len(parts) > 2 else None
            # 规范动作名
            action = action.strip().lower()
            if action == 'pickupobject':
                action = 'PickupObject'
            elif action == 'putobject':
                action = 'PutObject'
            elif action == 'toggleobject':
                action = 'ToggleObject'
            elif action == 'heatobject':
                action = 'HeatObject'
            elif action == 'coolobject':
                action = 'CoolObject'
            elif action == 'cleanobject':
                action = 'CleanObject'
            elif action == 'sliceobject':
                action = 'SliceObject'
            # 其他动作忽略
            if action not in {'PickupObject', 'PutObject', 'ToggleObject', 'HeatObject', 'CoolObject', 'CleanObject', 'SliceObject'}:
                continue
            plan.append((action, obj, target))
        return plan

    def _expand_high_action_to_primitives(self, action: str, obj: str, target: Optional[str], graph: dict) -> List[str]:
        """将单个 FLARE 高层动作展开为 VirtualHome 基元动作序列，并解析具体物体 ID。
        
        参数 graph 用于通过类名查找物体节点 ID。返回的动作字符串包含具体的 ID。
        例如 'walk', 'grab', 'open', 'close', 'switchon', 'switchoff', 'putin', 'putback', 'cut' 等。
        """
        # 查找物体节点
        obj_node = self._find_node_by_class(graph, obj)
        target_node = self._find_node_by_class(graph, target) if target else None

        primitives = []
        action_lower = action.lower()

        if action_lower == 'pickupobject':
            if obj_node:
                obj_id = obj_node['id']
                primitives.append(f"[walk] <{obj}> ({obj_id})")
                primitives.append(f"[grab] <{obj}> ({obj_id})")
            else:
                primitives.append(f"[walk] <{obj}> (?)")  # 无法找到物体时的占位，实际应重规划

        elif action_lower == 'putobject':
            if obj_node and target_node:
                obj_id = obj_node['id']
                target_id = target_node['id']
                # 需要判断 target 是否为容器等
                primitives.append(f"[walk] <{target}> ({target_id})")
                # 如果是可开关的容器，需要先打开
                if target.lower() in self._OPENABLE_CLASSES:
                    primitives.append(f"[open] <{target}> ({target_id})")
                primitives.append(f"[putin] <{obj}> ({obj_id}) <{target}> ({target_id})")
                # 关闭
                if target.lower() in self._OPENABLE_CLASSES:
                    primitives.append(f"[close] <{target}> ({target_id})")
            else:
                primitives.append(f"[walk] <{obj}> (?)")

        elif action_lower == 'toggleobject':
            if obj_node:
                obj_id = obj_node['id']
                primitives.append(f"[walk] <{obj}> ({obj_id})")
                primitives.append(f"[switchon] <{obj}> ({obj_id})")
            else:
                primitives.append(f"[walk] <{obj}> (?)")

        elif action_lower == 'heatobject':
            # HeatObject 通常放入微波炉/炉子并开启
            if obj_node and target_node:
                obj_id = obj_node['id']
                target_id = target_node['id']
                # 打开 target
                primitives.append(f"[walk] <{target}> ({target_id})")
                if target.lower() in self._OPENABLE_CLASSES:
                    primitives.append(f"[open] <{target}> ({target_id})")
                # 放入
                primitives.append(f"[putin] <{obj}> ({obj_id}) <{target}> ({target_id})")
                # 关闭
                if target.lower() in self._OPENABLE_CLASSES:
                    primitives.append(f"[close] <{target}> ({target_id})")
                # 开启设备
                primitives.append(f"[switchon] <{target}> ({target_id})")
            else:
                primitives.append(f"[walk] <{obj}> (?)")

        elif action_lower == 'coolobject':
            # 类似 HeatObject
            if obj_node and target_node:
                obj_id = obj_node['id']
                target_id = target_node['id']
                primitives.append(f"[walk] <{target}> ({target_id})")
                if target.lower() in self._OPENABLE_CLASSES:
                    primitives.append(f"[open] <{target}> ({target_id})")
                primitives.append(f"[putin] <{obj}> ({obj_id}) <{target}> ({target_id})")
                if target.lower() in self._OPENABLE_CLASSES:
                    primitives.append(f"[close] <{target}> ({target_id})")
            else:
                primitives.append(f"[walk] <{obj}> (?)")

        elif action_lower == 'cleanobject':
            # CleanObject 假设在水槽中清洗
            sink_node = self._find_node_by_class(graph, 'sink')
            if obj_node and sink_node:
                obj_id = obj_node['id']
                sink_id = sink_node['id']
                primitives.append(f"[walk] <sink> ({sink_id})")
                primitives.append(f"[wash] <{obj}> ({obj_id})")
            else:
                primitives.append(f"[walk] <{obj}> (?)")

        elif action_lower == 'sliceobject':
            if obj_node:
                obj_id = obj_node['id']
                primitives.append(f"[walk] <{obj}> ({obj_id})")
                primitives.append(f"[cut] <{obj}> ({obj_id})")
            else:
                primitives.append(f"[walk] <{obj}> (?)")

        return primitives

    @staticmethod
    def _find_node_by_class(graph: dict, class_name: str) -> Optional[dict]:
        """在 graph 中通过 class_name 查找一个可交互物体节点，排除 character 和 Rooms。"""
        target_name = class_name.lower().replace(' ', '')
        nodes = graph.get('nodes', [])
        candidates = []
        for node in nodes:
            cat = str(node.get('category', '')).lower()
            if cat == 'rooms':
                continue
            cn = str(node.get('class_name', '')).lower().replace(' ', '')
            # 精确匹配或包含
            if cn == target_name or target_name in cn or cn in target_name:
                if cn != 'character':
                    candidates.append(node)
        # 优先选择离角色近的？暂时返回第一个
        return candidates[0] if candidates else None

    # ------------------------------------------------------------------
    # Agent 主接口
    # ------------------------------------------------------------------
    def get_action(self, obs: dict, config: dict, env_info: dict = None) -> str:
        env_info = env_info or {}
        step = int(env_info.get("step", 0))
        action_history = env_info.get("action_history", [])
        logger = env_info.get("logger")

        goal = str(config.get("goal_instruction", "")).strip()
        if not goal:
            return "[wait]"

        # 从当前观察中提取可见物体类名
        visible_objects = self._get_current_visible_objects(obs)
        full_graph = self._deduplicate_graph(obs)

        # Step 0 重置
        if step == 0:
            self.current_high_plan = []
            self.completed_high_steps = []
            self.primitive_queue = []
            self.replan_count = 0

        # 如果有基元动作队列，直接返回下一个
        if self.primitive_queue:
            return self.primitive_queue.pop(0)

        # 如果高层计划为空或已执行完毕，则触发重规划
        if not self.current_high_plan:
            if self.replan_count >= self.max_replans:
                self._safe_error(logger, "FLARE: max replanning reached.")
                return "[wait]"

            # 检查上一步是否失败，若失败则清空已完成步骤（简单策略：清空全部已完成的）
            if step > 0 and action_history and not action_history[-1].get("success", True):
                self.completed_high_steps = []

            try:
                plan = self._generate_high_plan(goal, visible_objects, action_history)
                self.replan_count += 1
                self.current_high_plan = plan
                self._safe_info(logger, f"FLARE HLP: {plan}")
            except Exception as e:
                self._safe_error(logger, f"FLARE plan generation failed: {e}")
                return "[wait]"

        # 展开第一个高层动作为基元动作序列
        if self.current_high_plan:
            action, obj, target = self.current_high_plan.pop(0)
            primitives = self._expand_high_action_to_primitives(action, obj, target, full_graph)
            if primitives:
                # 将剩余基元动作放入队列，返回第一个
                self.primitive_queue = list(primitives)
                self.completed_high_steps.append(f"{action}:{obj}:{target}")
                return self.primitive_queue.pop(0)
            else:
                # 无法展开（例如物体找不到），跳过并继续下一个高层步骤
                self._safe_info(logger, f"FLARE: cannot expand {action} {obj}, skipping.")
                # 递归调用自己来处理下一个步骤（注意不要无限递归，最多计划长度次）
                return self.get_action(obs, config, env_info)

        # 如果没有任何可执行的，返回 wait
        return "[wait]"

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------
    @staticmethod
    def _get_current_visible_objects(obs: dict) -> List[str]:
        """从 obs 中提取当前可见物体的类名列表。"""
        nodes = obs.get('nodes', [])
        objects = set()
        for node in nodes:
            cat = str(node.get('category', '')).lower()
            if cat == 'rooms':
                continue
            cn = str(node.get('class_name', '')).strip().lower()
            if cn and cn != 'character':
                objects.add(cn)
        return sorted(list(objects))

    @staticmethod
    def _deduplicate_graph(graph: dict) -> dict:
        # 简单去重，可复用之前 LLM-Planner 的 deduplicate_graph 逻辑
        # 这里直接返回 graph，假设传入的 obs 已经是去重后的
        return graph

    @staticmethod
    def _safe_info(logger, msg: str):
        if logger and hasattr(logger, 'info'):
            logger.info(msg)

    @staticmethod
    def _safe_error(logger, msg: str):
        if logger and hasattr(logger, 'error'):
            logger.error(msg)

    # 可以在必要时包含 OPENABLE_CLASSES
    _OPENABLE_CLASSES = {'fridge', 'cabinet', 'microwave', 'drawer', 'safe'}


# 如果需要在 __init__.py 中注册