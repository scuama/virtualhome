"""Evaluator-owned per-task progress used only for metrics and logs."""

import copy


class TaskProgressTracker:
    """Track both current and historical satisfaction for every instruction."""

    def __init__(self, config: dict):
        configured_tasks = config.get("tasks") or []
        if configured_tasks:
            tasks = configured_tasks
        else:
            tasks = [
                {
                    "task_id": config.get("scenario_id", "task_1"),
                    "instruction": config.get("goal_instruction", ""),
                    "success_condition": config.get("success_condition", {}),
                }
            ]

        self.tasks = [
            {
                "task_id": task.get("task_id", f"task_{index + 1}"),
                "instruction": task.get("instruction", ""),
                "success_condition": copy.deepcopy(
                    task.get("success_condition", {})
                ),
                "currently_satisfied": False,
                "ever_satisfied": False,
                "first_satisfied_step": None,
            }
            for index, task in enumerate(tasks)
        ]

    def update(self, graph, step, check_success, logger=None):
        for task in self.tasks:
            was_satisfied = task["currently_satisfied"]
            is_satisfied = bool(
                check_success(graph, task["success_condition"])
            )
            task["currently_satisfied"] = is_satisfied
            if is_satisfied and not task["ever_satisfied"]:
                task["ever_satisfied"] = True
                task["first_satisfied_step"] = int(step)
                if logger:
                    logger.info(
                        f"✅ TASK SATISFIED: {task['task_id']} at step {step}."
                    )
            elif was_satisfied and not is_satisfied and logger:
                logger.info(
                    f"↩️ TASK REGRESSED: {task['task_id']} at step {step}."
                )

    def as_log_info(self):
        """Return evaluator progress for result logging, never agent input."""
        return [
            {
                "task_id": task["task_id"],
                "currently_satisfied": task["currently_satisfied"],
            }
            for task in self.tasks
        ]

    def as_agent_info(self):
        """Expose only neutral task IDs and completion booleans to the agent."""
        return [
            {
                "task_id": f"task_{index}",
                "currently_satisfied": task["currently_satisfied"],
            }
            for index, task in enumerate(self.tasks, 1)
        ]

    def as_metrics(self):
        total = len(self.tasks)
        completed = sum(
            1 for task in self.tasks if task["currently_satisfied"]
        )
        first_steps = [
            task["first_satisfied_step"]
            for task in self.tasks
            if task["first_satisfied_step"] is not None
        ]
        mean_completion_step = (
            round(sum(first_steps) / len(first_steps), 4)
            if first_steps
            else None
        )
        task_records = []
        for task in self.tasks:
            record = copy.deepcopy(task)
            # Compatibility aliases now reflect current evaluator truth.
            record["completed"] = task["currently_satisfied"]
            record["completion_step"] = task["first_satisfied_step"]
            task_records.append(record)

        return {
            "task_total": total,
            "task_completed": completed,
            # Retained for old consumers; raw counts above remain authoritative.
            "sr": 1.0 if total and completed == total else 0.0,
            "ps": round(completed / total, 4) if total else 0.0,
            "mean_completion_step": mean_completion_step,
            "tasks": task_records,
        }
