import json
from llm_client import LLMClient
from logger_utils import AgentLogger
from goal_reasoner import GoalReasoner
from solution_space import SolutionSpaceAnalyzer
from task_validator import TaskValidator
from memory_manager import MemoryManager

class IntentReasoningAgent:
    def __init__(self, episode_id=None, model_name="gpt-4o-mini", scene_id=None, inject_priors=False, log_dir=None):
        self.logger = AgentLogger(episode_id, log_dir=log_dir)
        self.llm = LLMClient(model_name=model_name)

        self.goal_reasoner = GoalReasoner(self.llm, self.logger)
        self.solution_space = SolutionSpaceAnalyzer(self.llm, self.logger)
        self.task_validator = TaskValidator(self.llm, self.logger)
        self.memory_manager = MemoryManager(self.llm, self.logger)

        self.global_intent = {}
        self.action_history = []
        self.current_location = "unknown starting location"
        self.held_object = None
        self.inject_priors = inject_priors
        self.failed_actions = {}
        self.visited_locations = []

        self.scene_id = scene_id if scene_id else (episode_id if episode_id else "unknown_scene")

    @staticmethod
    def _fallback_action_id(legal_combinations: dict, prefer_place: bool = False) -> int:
        if not legal_combinations:
            return 0
        if prefer_place:
            for aid, desc in legal_combinations.items():
                dl = (desc or "").lower()
                if dl.startswith("place ") or dl.startswith("put ") or dl.startswith("drop "):
                    return aid
        for aid in sorted(k for k in legal_combinations.keys() if k != 9999):
            return aid
        return next(iter(legal_combinations.keys()))

    def step(self, instruction: str, observation_text: str, skill_set: list, step_idx: int, img_path: str = None, dual_img_path: str = None, action_success: bool = True, available_rooms: list = None) -> dict:
        """
        核心调度循环
        :param instruction: 当前关卡的文本指令
        :param observation_text: 当前视角的文字描述/日志
        :param skill_set: 当前允许的 Action_IDs 列表 (元组或字符串形式)
        :param step_idx: 当前环境的步数
        :param img_path: (新增) 第一人称视觉截图路径，供多模态解析
        :param dual_img_path: (新增) 双视角截图路径，供日志记录
        :return: 决定执行的动作详情字典 (dict)
        """
        self.logger.info(f"\n========== STARTING STEP {step_idx} ==========")
        
        # 0. 错误恢复与容错机制 (Error Recovery Mechanism)
        action_failed = not action_success
        
        if action_failed:
            if len(self.action_history) > 0:
                failed_action = self.action_history.pop()
                self.logger.info(f"[Error Recovery] Last action '{failed_action}' failed. Removed from history.")
                
                # 记录失败次数
                self.failed_actions[failed_action] = self.failed_actions.get(failed_action, 0) + 1
                
                # 如果是拾取失败，且连续失败达 2 次以上，判定为视觉误判/物理死锁，从记忆和 LTM 中抹除该物品
                if failed_action.lower().startswith("pick ") and self.failed_actions[failed_action] >= 2:
                    obj = failed_action.lower().replace("pick up the ", "").replace("pick up ", "").replace("pick the ", "").replace("pick ", "").strip()
                    if obj in self.solution_space.memory_objects:
                        del self.solution_space.memory_objects[obj]
                    self.memory_manager.ltm.update_state(f"Object('{obj}') DOES NOT EXIST at Location('{self.current_location}').")
                    self.logger.info(f"[Error Recovery] Sent STATE UPDATE to delete hallucinated object '{obj}'.")
        else:
            # 动作成功执行，重置所有失败计数器（因为环境/物理状态已发生改变）
            self.failed_actions.clear()
            
            # 仅向 LTM 写入跨越长期记忆所需的客观事实（如放置物品导致的位置变更）
            if step_idx > 0 and len(self.action_history) > 0:
                last_act = self.action_history[-1].lower()
                state_msg = ""
                
                if "[putback]" in last_act or "[putin]" in last_act or last_act.startswith("place ") or last_act.startswith("put ") or last_act.startswith("drop "):
                    obj = self.held_object if self.held_object else "object"
                    state_msg = f"Object('{obj}') is located at Location('{self.current_location}')."
                    
                if state_msg:
                    self.memory_manager.ltm.update_state(state_msg)
                    self.logger.info(f"[CoreAgent] Sent EPISODIC UPDATE to LTM: {state_msg}")
        
        # 提取目标名称的辅助函数
        def extract_target(act_str):
            import re
            act_str = act_str.lower()
            match = re.search(r'\[.*?\]\s*<(.*?)>', act_str)
            if match:
                return match.group(1).strip()
            return act_str.replace("navigate to the ", "").replace("navigate to ", "").replace("nav_", "").replace("pick up the ", "").replace("pick up ", "").replace("pick the ", "").replace("pick ", "").replace("open the ", "").replace("open ", "").replace("close the ", "").replace("close ", "").strip()
            
        def extract_instance(act_str):
            import re
            act_str = act_str.lower()
            match = re.search(r'\[.*?\]\s*<(.*?)>\s*\((.*?)\)', act_str)
            if match:
                return f"{match.group(1).strip()}_{match.group(2).strip()}"
            return extract_target(act_str)

        # 1. 目标提取 (仅在第一步执行)
        if step_idx == 0 and not self.global_intent:
            import os
            clarification_path = os.path.join(self.logger.run_dir, "clarification_context.json")
            combined_instruction = instruction
            
            if os.path.exists(clarification_path):
                try:
                    with open(clarification_path, 'r', encoding='utf-8') as f:
                        context = json.load(f)
                    combined_instruction = f"Original Instruction: {context.get('original_instruction')}\nUser Clarification: {instruction}"
                except Exception as e:
                    self.logger.error(f"Failed to load clarification context: {e}")

            intent_dict = self.goal_reasoner.extract_intent(combined_instruction)
            
            if intent_dict.get("is_instruction_obviously_vague", False):
                msg = intent_dict.get("clarification_question", "Could you please clarify your request? I need more specific details.")
                self.logger.info(f"[Clarification Needed] {msg}")
                
                # 保存原始指令上下文
                with open(clarification_path, 'w', encoding='utf-8') as f:
                    json.dump({"original_instruction": combined_instruction}, f, ensure_ascii=False)
                    
                # 保存断点状态
                self.memory_manager.save_session_state(
                    scene_id=self.scene_id,
                    global_intent={}, 
                    visited_locations=self.visited_locations if isinstance(self.visited_locations, dict) else {},
                    known_objects=self.solution_space.memory_objects,
                    action_history=self.action_history,
                    last_agent_message=msg,
                    log_dir=self.logger.run_dir
                )
                return {"stop_and_save": True, "communication_to_user": msg}
                
            self.global_intent = intent_dict
            
        # 因为 LTM (GraphRAG) 的全局索引更新有异步延迟，
        # 我们在本地通过 action_history 精准维护一套已探索地点作为 Short-Term Memory 补充。
        # 规则：
        # - 如果执行过 nav_X 或 navigate to X：
        #   - 如果该地点无需开门（如 counter, table, sofa, sink），直接视为 visited_closed
        #   - 如果该地点是个容器，必须在 action_history 中同时包含 open X，才视为 visited_open (即完全探索完)
        visited_locations_state = {}
        
        # 1. 找出所有去过的地点
        navigated_locs = []
        for action in self.action_history:
            action_lower = action.lower()
            if "[walk]" in action_lower or action_lower.startswith("nav_") or "navigate to" in action_lower:
                loc = extract_target(action_lower)
                if loc not in navigated_locs:
                    navigated_locs.append(loc)

        # 2. 判定每个去过的地点是否已经探索完
        openable_locs = set()
        for cap in skill_set:
            if "[open]" in cap.lower() or cap.lower().startswith("open "):
                openable_locs.add(extract_target(cap))

        # 3. 实时判断状态
        for loc in navigated_locs:
            if loc in openable_locs:
                has_opened = False
                for action in self.action_history:
                    if ("[open]" in action.lower() or action.lower().startswith("open ")) and (loc in action.lower() or extract_target(action) in loc):
                        has_opened = True
                        break
                if has_opened:
                    visited_locations_state[loc] = "visited_open"
            else:
                visited_locations_state[loc] = "visited_open"

        # 解析 held_object 并推断容器开关状态
        self.held_object = None
        receptacle_states = {}
        for action in self.action_history:
            action_lower = action.lower()
            if "[grab]" in action_lower or action_lower.startswith("pick "):
                self.held_object = extract_target(action_lower)
            elif "[putback]" in action_lower or "[putin]" in action_lower or "place " in action_lower or "put " in action_lower or "drop " in action_lower:
                self.held_object = None
            elif "[open]" in action_lower or action_lower.startswith("open "):
                receptacle_states[extract_instance(action_lower)] = "open"
            elif "[close]" in action_lower or action_lower.startswith("close "):
                receptacle_states[extract_instance(action_lower)] = "closed"
                
        # 在 self.visited_locations 被单步临时字典覆盖之前，先创建一个真正的历史已探索地点快照，
        # 以便在 Step 结尾施加【记忆单调递增约束】合并时使用，防止记忆随着 LTM 注意力稀释而减少！
        historical_explored_snapshot = list(self.visited_locations) if hasattr(self, "visited_locations") and self.visited_locations else []
        
        self.visited_locations = visited_locations_state
        self.logger.info(f"[Visited Locations State] {visited_locations_state}")
        self.logger.info(f"[Inventory] held_object: {self.held_object}")
        self.logger.info(f"[Receptacle States] {receptacle_states}")

        # 2. 解空间更新
        self.solution_space.update_capabilities(skill_set, available_rooms=available_rooms, inject_priors=self.inject_priors)
        # 生成当前黑名单（连续失败 >= 2 次的动作直接被屏蔽）
        blacklisted = [act for act, count in self.failed_actions.items() if count >= 2]
        
        self.solution_space.update_observation(
            observation_text=observation_text, 
            current_location=self.current_location,
            visited_locations_state=visited_locations_state,
            step=step_idx, 
            global_intent=self.global_intent,
            img_path=img_path, 
            dual_img_path=dual_img_path,
            held_object=self.held_object,
            receptacle_states=receptacle_states,
            blacklisted_actions=blacklisted
        )
        # 从 LTM 同步获取最新已探索地点列表，并与本地通过 action_history 推断的已探索地点取并集，
        # 从而完美抵消 GraphRAG 的异步索引延迟。
        # 此外，为了防止大模型在 LTM 长期记忆中对旧节点产生注意力稀释（遗忘），
        # 我们强行引入【记忆单调递增约束】：与上一轮保存的历史已探索列表取并集，确保记忆绝对只增不减！
        ltm_explored = self.solution_space.world_model.get("explored_locations", [])
        local_explored = list(visited_locations_state.keys())
        current_step_explored = list(set(ltm_explored) | set(local_explored))
        
        # 融入历史记忆快照
        historical_explored = historical_explored_snapshot if isinstance(historical_explored_snapshot, list) else list(historical_explored_snapshot)
        merged_explored = list(set(current_step_explored) | set(historical_explored))
        
        self.visited_locations = merged_explored
        self.logger.info(f"[Visited Locations State Updated] {merged_explored} (LTM: {ltm_explored}, Local: {local_explored}, History Snapshot: {historical_explored})")
        
        # 将合并后的已探索地点同步回 solution_space 的 world_model，以确保内部约束（如 _apply_combination_constraints）过滤准确
        self.solution_space.world_model["explored_locations"] = merged_explored

        current_solution_space = self.solution_space.get_solution_space_dict()
        
        # 3. 验证与决策 (Merged C & D)
        validation_result = self.task_validator.validate_action_feasibility(
            global_intent=self.global_intent,
            solution_space=current_solution_space,
            action_history=self.action_history,
            visited_locations=visited_locations_state,
            current_location=self.current_location,
            step=step_idx,
            max_steps=50,
            persistent_memory_text=self.memory_manager.get_full_memory_context(),
            held_object=self.held_object,
        )
        
        # 4. 提取动作并更新状态
        action_id = validation_result.get("action_id", 0)
        
        if action_id == 9999:
            # 允许 9999：手持物在 LLM relevant_objects 中，或已探索全部地点且双手为空
            all_locs = list(self.solution_space.composition_elements.get("locations", []))
            all_explored = len(self.visited_locations) >= len(all_locs) if all_locs else False
            relevant_lower = [o.lower() for o in self.solution_space.relevant_objects]
            held_ok = bool(self.held_object and self.held_object.lower() in relevant_lower)
            legal = current_solution_space.get("legal_combinations", {})

            if self.held_object and not held_ok:
                self.logger.info(
                    f"[CoreAgent] Intercepted Action 9999: holding irrelevant '{self.held_object}'"
                )
                action_id = self._fallback_action_id(legal, prefer_place=True)
                validation_result["action_id"] = action_id
            elif not self.held_object and not all_explored:
                self.logger.info(
                    "[CoreAgent] Intercepted Action 9999: not holding a valid alternative "
                    "and exploration is incomplete."
                )
                action_id = self._fallback_action_id(legal)
                validation_result["action_id"] = action_id
            else:
                msg = validation_result.get("communication_to_user", "I need your assistance.")
                self.logger.info(f"[Communication to User] {msg}")
                
                # 当决定跟用户对话时，保存断点上下文
                self.memory_manager.save_session_state(
                    scene_id=self.scene_id,
                    global_intent=self.global_intent,
                    visited_locations=visited_locations_state,
                    known_objects=self.solution_space.memory_objects,
                    action_history=self.action_history,
                    last_agent_message=msg,
                    log_dir=self.logger.run_dir
                )
                validation_result["stop_and_save"] = True
                return validation_result

        if action_id is None:
            self.logger.log_module_output(
                module_name="CoreAgent",
                step=step_idx,
                output_data="Agent decided to stop. No action selected (action_id is None)."
            )
            # Default to 0 or some valid format to avoid crashing, or return a special termination signal.
            # Usually we return a stop action. If no stop action is known, return 0 as dummy.
            validation_result["action_id"] = 0
            action_id = validation_result.get("action_id", 0)
            return validation_result
        
        # 从 SolutionSpace 的合法动作中提取
        current_solution_space = self.solution_space.get_solution_space_dict()
        legal = current_solution_space.get("legal_combinations", {})
        action_str = legal.get(action_id, "UNKNOWN")
        
        self.action_history.append(action_str)
        
        self.logger.info(f"[Step {step_idx}] CoreAgent Final Decision: Action_ID {action_id} -> {action_str}")
        
        # 写入简版 Markdown 战报
        self.logger.log_step_markdown(
            step=step_idx,
            img_path=dual_img_path if dual_img_path else img_path,
            held_object=self.held_object,
            legal_combos_count=len(current_solution_space.get("legal_combinations", {})),
            visited_locations=self.solution_space.world_model.get("explored_locations", []),
            memory_objects=self.solution_space.memory_objects,
            ranked_plans=validation_result.get("ranked_plans", []),
            selected_action=f"Action {action_id} -> {action_str}"
        )
        
        # Check if navigate action to update current_location
        if "[walk]" in action_str.lower() or "navigate to" in action_str.lower() or action_str.lower().startswith("nav_"):
            self.current_location = extract_target(action_str)
            
        return validation_result
