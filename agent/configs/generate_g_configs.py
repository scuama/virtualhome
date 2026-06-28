import json
import os

configs_dir = "/Users/rushy/program/virtualhome/agent/configs/g_class"
os.makedirs(configs_dir, exist_ok=True)

def write_config(filename, data):
    with open(os.path.join(configs_dir, filename), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- G1 (正常条件触发) ---
write_config("G1_01.json", {
    "environment_id": 1,
    "goal_instruction": "如果冰箱里有牛奶，就帮我用微波炉热一杯。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "kitchen"},
        {"subject": "milk", "relation": "INSIDE", "object": "fridge", "count": 1}
    ],
    "success_condition": {
        "check_type": "physical_state",
        "target_class": "milk",
        "require_states": ["HOT"]
    }
})

write_config("G1_02.json", {
    "environment_id": 1,
    "goal_instruction": "如果桌上有苹果，帮我洗干净拿过来。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "kitchen"},
        {"subject": "apple", "relation": "ON", "object": "kitchen_table", "count": 1}
    ],
    "initial_states_override": [
        {"target_classes": ["apple"], "remove_states": ["CLEAN"], "add_states": ["DIRTY"]},
        {"target_classes": ["faucet"], "add_states": ["ON"]}
    ],
    "success_condition": {
        "check_type": "physical_state",
        "target_class": "apple",
        "require_states": ["CLEAN"]
    }
})

write_config("G1_03.json", {
    "environment_id": 1,
    "goal_instruction": "如果电视机开着，就把遥控器拿过来。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "livingroom"},
        {"subject": "remote_control", "relation": "ON", "object": "sofa", "count": 1}
    ],
    "initial_states_override": [
        {"target_classes": ["tv"], "add_states": ["ON"]}
    ],
    "success_condition": {
        "check_type": "relation",
        "require_relation": ["HOLDS_RH", "character", "remote_control"],
        "fallback_relation": ["HOLDS_LH", "character", "remote_control"]
    }
})

write_config("G1_04.json", {
    "environment_id": 1,
    "goal_instruction": "如果灯亮着，就关掉它。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "bedroom"},
        {"subject": "table_lamp", "relation": "INSIDE", "object": "bedroom", "count": 1}
    ],
    "initial_states_override": [
        {"target_classes": ["table_lamp"], "add_states": ["ON"]}
    ],
    "success_condition": {
        "check_type": "physical_state",
        "target_class": "table_lamp",
        "require_states": ["OFF"],
        "quantifier": "all"
    }
})

write_config("G1_05.json", {
    "environment_id": 1,
    "goal_instruction": "如果杯子里有水，就倒掉放进柜子里。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "kitchen"},
        {"subject": "mug", "relation": "ON", "object": "kitchen_table", "count": 1}
    ],
    "initial_states_override": [
        {"target_classes": ["cabinet"], "remove_states": ["OPEN"], "add_states": ["CLOSED"]},
        {"target_classes": ["mug"], "add_states": ["FULL"]}
    ],
    "success_condition": {
        "check_type": "relation",
        "require_relation": ["INSIDE", "mug", "cabinet"]
    }
})


# --- G2 (意图模糊/需问答补充) ---
write_config("G2_06.json", {
    "environment_id": 1,
    "goal_instruction": "如果电视开着，把灯调到合适的状态。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "livingroom"},
        {"subject": "table_lamp", "relation": "INSIDE", "object": "livingroom", "count": 1}
    ],
    "initial_states_override": [
        {"target_classes": ["tv"], "add_states": ["ON"]},
        {"target_classes": ["table_lamp"], "remove_states": ["ON"], "add_states": ["OFF"]}
    ],
    "user_clarification_reply": "把灯打开就行。",
    "success_condition": {
        "check_type": "physical_state",
        "target_class": "table_lamp",
        "require_states": ["ON"],
        "quantifier": "all",
        "require_ask": True
    }
})

write_config("G2_07.json", {
    "environment_id": 1,
    "goal_instruction": "如果看到桌上的杯子，把它放到该放的地方去。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "kitchen"},
        {"subject": "mug", "relation": "ON", "object": "kitchen_table", "count": 1}
    ],
    "user_clarification_reply": "放到柜子里。",
    "success_condition": {
        "check_type": "relation",
        "require_relation": ["INSIDE", "mug", "cabinet"],
        "require_ask": True
    }
})

write_config("G2_08.json", {
    "environment_id": 1,
    "goal_instruction": "如果看到牛奶，拿一杯温度合适的过来。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "kitchen"},
        {"subject": "milk", "relation": "ON", "object": "kitchen_table", "count": 2}
    ],
    "initial_states_override": [
        {"target_classes": ["milk"], "target_index": 0, "add_states": ["COLD"]},
        {"target_classes": ["milk"], "target_index": 1, "add_states": ["HOT"]}
    ],
    "user_clarification_reply": "热的。",
    "success_condition": {
        "check_type": "relation",
        "require_relation": ["HOLDS_RH", "character", "milk"], 
        "fallback_relation": ["HOLDS_LH", "character", "milk"],
        "require_target_state": ["HOT"],
        "require_ask": True
    }
})

write_config("G2_09.json", {
    "environment_id": 1,
    "goal_instruction": "如果书掉到地上了，帮我收拾整齐。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "bedroom"},
        {"subject": "book", "relation": "ON", "object": "floor", "count": 3}
    ],
    "user_clarification_reply": "全部捡起来放在桌上。",
    "success_condition": {
        "check_type": "relation",
        "require_relation": ["ON", "book", "desk"],
        "require_ask": True
    }
})

write_config("G2_10.json", {
    "environment_id": 1,
    "goal_instruction": "如果厨房里没有人，确保厨房是安全的。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "kitchen"}
    ],
    "initial_states_override": [
        {"target_classes": ["stove"], "add_states": ["ON"]}
    ],
    "user_clarification_reply": "把炉子关掉。",
    "success_condition": {
        "check_type": "physical_state",
        "target_class": "stove",
        "require_states": ["OFF"],
        "require_ask": True
    }
})

# --- G3 (条件恒不满足) ---
g3_common_success = {
    "check_type": "agent_action",
    "require_action": "[ask]",
    "require_message_contains": ["impossible", "broken", "not exist", "cannot", "fail", "坏", "不可能", "没有"]
}

write_config("G3_11.json", {
    "environment_id": 1,
    "goal_instruction": "如果冰箱里有牛奶，就帮我用微波炉热一杯。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "kitchen"}
    ],
    "initial_states_override": [
        {"target_classes": ["fridge"], "add_states": ["BROKEN"]}
    ],
    "success_condition": g3_common_success
})

write_config("G3_12.json", {
    "environment_id": 1,
    "goal_instruction": "如果电视开着，就把它关了。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "livingroom"}
    ],
    "initial_states_override": [
        {"target_classes": ["tv"], "remove_states": ["ON"], "add_states": ["OFF", "BROKEN"]}
    ],
    "success_condition": g3_common_success
})

write_config("G3_13.json", {
    "environment_id": 1,
    "goal_instruction": "如果电视机开着，就把遥控器拿过来。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "livingroom"}
    ],
    "initial_states_override": [
        {"target_classes": ["tv"], "remove_states": ["ON"], "add_states": ["OFF", "BROKEN"]}
    ],
    "success_condition": g3_common_success
})

write_config("G3_14.json", {
    "environment_id": 1,
    "goal_instruction": "如果灯亮着，就关掉它。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "bedroom"},
        {"subject": "table_lamp", "relation": "INSIDE", "object": "bedroom", "count": 1}
    ],
    "initial_states_override": [
        {"target_classes": ["table_lamp"], "remove_states": ["ON"], "add_states": ["OFF", "BROKEN"]}
    ],
    "success_condition": g3_common_success
})

write_config("G3_15.json", {
    "environment_id": 1,
    "goal_instruction": "如果炉子开着，就帮我热一杯牛奶和一杯咖啡拿到桌上。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "kitchen"}
    ],
    "initial_states_override": [
        {"target_classes": ["stove"], "remove_states": ["ON"], "add_states": ["OFF", "BROKEN"]}
    ],
    "success_condition": g3_common_success
})

# --- G4 (发现途径失效，需寻找物理替代) ---
write_config("G4_16.json", {
    "environment_id": 1,
    "goal_instruction": "如果冰箱里有牛奶，就帮我用微波炉热一杯。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "kitchen"},
        {"subject": "milk", "relation": "INSIDE", "object": "fridge", "count": 1}
    ],
    "hidden_broken_classes": ["microwave"],
    "success_condition": {
        "check_type": "physical_state",
        "target_class": "milk",
        "require_states": ["HOT"]
    }
})

write_config("G4_17.json", {
    "environment_id": 1,
    "goal_instruction": "如果桌上有苹果，帮我开水龙头冲一冲，洗一个拿过来。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "kitchen"},
        {"subject": "apple", "relation": "ON", "object": "kitchen_table", "count": 1}
    ],
    "initial_states_override": [
        {"target_classes": ["apple"], "remove_states": ["CLEAN"], "add_states": ["DIRTY"]}
    ],
    "hidden_broken_classes": ["faucet"],
    "success_condition": {
        "check_type": "physical_state",
        "target_class": "apple",
        "require_states": ["CLEAN"]
    }
})

write_config("G4_18.json", {
    "environment_id": 1,
    "goal_instruction": "如果电视开着，就用遥控器把电视关了。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "livingroom"}
    ],
    "initial_states_override": [
        {"target_classes": ["tv"], "add_states": ["ON"]}
    ],
    "hidden_broken_classes": ["remote_control"],
    "success_condition": {
        "check_type": "physical_state",
        "target_class": "tv",
        "require_states": ["OFF"]
    }
})

write_config("G4_19.json", {
    "environment_id": 1,
    "goal_instruction": "如果台灯亮着，就关了。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "bedroom"},
        {"subject": "table_lamp", "relation": "INSIDE", "object": "bedroom", "count": 1}
    ],
    "initial_states_override": [
        {"target_classes": ["table_lamp"], "add_states": ["ON"]}
    ],
    "hidden_broken_classes": ["table_lamp"],
    "success_condition": {
        "check_type": "physical_state",
        "target_class": "table_lamp",
        "require_states": ["OFF"],
        "quantifier": "all"
    }
})

write_config("G4_20.json", {
    "environment_id": 1,
    "goal_instruction": "如果桌子上有水壶，就给我倒杯水过来。",
    "initial_relations_override": [
        {"subject": "character", "relation": "INSIDE", "object": "kitchen"},
        {"subject": "dish_bowl", "relation": "ON", "object": "kitchen_table", "count": 1}
    ],
    "hidden_broken_classes": ["mug", "mug"], 
    "success_condition": {
        "check_type": "physical_state",
        "target_class": "dish_bowl",
        "require_states": ["FILLED", "FULL"],
        "fallback_require_states": ["WATER"]
    }
})

print("Successfully generated all 20 G-class configuration JSON files in agent/configs/g_class")
