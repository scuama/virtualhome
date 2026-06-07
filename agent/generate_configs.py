import json
import os

configs = [
    {
        "id": "scene_01",
        "instruction": "擦干净电视。",
        "tags": ["M3", "P3"],
        "setup": {
            "init_room": "livingroom",
            "modify_states": {"tv": ["ON", "DIRTY"]}
        },
        "global_rules": ["NO_WIPE_WHILE_ON"]
    },
    {
        "id": "scene_02",
        "instruction": "把那个放到桌子上。",
        "tags": ["G2"],
        "setup": {
            "init_room": "livingroom"
        }
    },
    {
        "id": "scene_03",
        "instruction": "如果冰箱开着，就把苹果放进去。",
        "tags": ["G3"],
        "setup": {
            "init_room": "kitchen",
            "modify_properties": {"fridge": {"remove": ["CAN_OPEN"]}}
        }
    },
    {
        "id": "scene_04",
        "instruction": "去书房拿一本书。",
        "tags": ["M3"],
        "setup": {
            "init_room": "bedroom"
        },
        "global_rules": ["MUST_CLOSE_DOORS"]
    },
    {
        "id": "scene_05",
        "instruction": "去把桌上的盘子拿过来。",
        "tags": ["M1"],
        "setup": {
            "init_room": "kitchen"
        },
        "dynamic_events": [{
            "target_class": "plate",
            "trigger_distance": 2.5,
            "action": "vanish_reappear",
            "duration_steps": 2
        }]
    },
    {
        "id": "scene_06",
        "instruction": "把茶几上的两本书给我拿来。",
        "tags": ["P2"],
        "setup": {
            "init_room": "livingroom",
            "add_nodes": [
                {"class_name": "book", "location": "coffeetable"},
                {"class_name": "book", "location": "coffeetable"}
            ]
        }
    },
    {
        "id": "scene_07",
        "instruction": "把水杯拿给我。",
        "tags": ["M2"],
        "setup": {
            "init_room": "kitchen",
            "add_nodes": [
                {"class_name": "waterglass", "states": ["CLEAN"]},
                {"class_name": "waterglass", "states": ["DIRTY"]},
                {"class_name": "waterglass", "states": ["DIRTY"]},
                {"class_name": "waterglass", "states": ["DIRTY"]}
            ]
        }
    },
    {
        "id": "scene_08",
        "instruction": "给我拿个苹果吃。",
        "tags": ["G4"],
        "setup": {
            "init_room": "livingroom",
            "remove_nodes": ["apple"],
            "add_nodes": [{"class_name": "cupcake", "location": "coffeetable"}]
        }
    },
    {
        "id": "scene_09",
        "instruction": "帮我整理一下那边。",
        "tags": ["G2"],
        "setup": {
            "init_room": "livingroom"
        }
    },
    {
        "id": "scene_10",
        "instruction": "把桌上的苹果拿给我。",
        "tags": ["P1"],
        "setup": {
            "init_room": "livingroom",
            "agent_inventory": ["book", "book"]
        }
    },
    {
        "id": "scene_11",
        "instruction": "如果有盘子乱放，就把它们收了。",
        "tags": ["G1", "P2"],
        "setup": {
            "init_room": "kitchen",
            "modify_states": {"plate": ["DIRTY"]}
        }
    },
    {
        "id": "scene_12",
        "instruction": "把沙发上的外套拿过来。",
        "tags": ["M4"],
        "setup": {
            "init_room": "livingroom"
        },
        "dynamic_events": [{
            "target_class": "jacket",
            "trigger_distance": 2.5,
            "action": "teleport",
            "destination_class": "floor"
        }]
    },
    {
        "id": "scene_13",
        "instruction": "把手里的盒子放柜子上。",
        "tags": ["G4", "P1"],
        "setup": {
            "init_room": "bedroom",
            "remove_nodes": ["cabinet"],
            "agent_inventory": ["box"]
        }
    },
    {
        "id": "scene_14",
        "instruction": "如果抽屉开着，就把书锁进抽屉。",
        "tags": ["G3"],
        "setup": {
            "init_room": "bedroom",
            "modify_properties": {"drawer": {"remove": ["CAN_OPEN"]}}
        }
    },
    {
        "id": "scene_15",
        "instruction": "用微波炉热一杯牛奶。",
        "tags": ["P1", "P3"],
        "setup": {
            "init_room": "kitchen",
            "modify_states": {"microwave": ["PLUGGED_OUT"]},
            "add_nodes": [{"class_name": "plate", "location": "microwave"}]
        }
    },
    {
        "id": "scene_16",
        "instruction": "把水杯收起来。",
        "tags": ["M3"],
        "setup": {
            "init_room": "kitchen"
        },
        "global_rules": ["MUG_ALWAYS_ON_COFFEETABLE"]
    },
    {
        "id": "scene_17",
        "instruction": "如果你的电脑没开，把它打开。",
        "tags": ["G1", "M4", "P1"],
        "setup": {
            "init_room": "bedroom",
            "modify_states": {"computer": ["OFF"]},
            "agent_inventory": ["book", "book"]
        },
        "dynamic_events": [{
            "target_class": "computer",
            "trigger_distance": 2.5,
            "action": "teleport",
            "destination_class": "floor"
        }]
    },
    {
        "id": "scene_18",
        "instruction": "拿两个苹果过来。",
        "tags": ["P2"],
        "setup": {
            "init_room": "kitchen"
        }
    },
    {
        "id": "scene_19",
        "instruction": "把这几个盘子处理一下。",
        "tags": ["M3"],
        "setup": {
            "init_room": "kitchen"
        },
        "global_rules": ["STERILIZE_PLATES_IN_MICROWAVE"]
    },
    {
        "id": "scene_20",
        "instruction": "用微波炉加热个蛋糕给我吃。",
        "tags": ["M2", "P3"],
        "setup": {
            "init_room": "kitchen",
            "add_nodes": [
                {"class_name": "cupcake", "states": ["CLEAN"]},
                {"class_name": "cupcake", "states": ["DIRTY"]}
            ]
        }
    }
]

os.makedirs('/mnt/disk1/decom/virtualhome/agent/configs', exist_ok=True)
for c in configs:
    # Set global environment id
    c["environment_id"] = 0
    with open(f"/mnt/disk1/decom/virtualhome/agent/configs/{c['id']}.json", "w") as f:
        json.dump(c, f, indent=4, ensure_ascii=False)
print(f"Generated {len(configs)} config files in agent/configs")
