import json
import os

CONFIGS_DIR = os.path.join(os.path.dirname(__file__), "..", "configs")
os.makedirs(CONFIGS_DIR, exist_ok=True)

wait_padding = ["[WAIT]"] * 5

tasks = [
    {
        "task_name": "maintenance_tv_turn_on",
        "instruction": "If no one is watching the TV, turn it on.",
        "max_steps": 50,
        "use_state_machine": True,
        "init_graph_modifiers": [],
        "npc_scripts": wait_padding + ["[WALK] <tv> (1)", "[SWITCHOFF] <tv> (1)"]
    },
    {
        "task_name": "maintenance_apple_desk",
        "instruction": "If you have an apple somewhere, bring it to your desk.",
        "max_steps": 50,
        "use_state_machine": True,
        "init_graph_modifiers": [],
        "npc_scripts": wait_padding + ["[WALK] <apple> (1)", "[GRAB] <apple> (1)", "[WALK] <kitchencounter> (1)", "[DROP] <apple> (1)"]
    },
    {
        "task_name": "maintenance_book_sofa",
        "instruction": "If you see a book somewhere unorganized, bring it to the sofa.",
        "max_steps": 50,
        "use_state_machine": True,
        "init_graph_modifiers": [],
        "npc_scripts": wait_padding + ["[WALK] <book> (1)", "[GRAB] <book> (1)", "[WALK] <floor> (1)", "[DROP] <book> (1)"]
    },
    {
        "task_name": "maintenance_dishwasher_open",
        "instruction": "The dishwasher must always be open to dry the dishwasher.",
        "max_steps": 50,
        "use_state_machine": True,
        "init_graph_modifiers": [],
        "npc_scripts": wait_padding + ["[WALK] <dishwasher> (1)", "[CLOSE] <dishwasher> (1)"]
    },
    {
        "task_name": "maintenance_microwave_open",
        "instruction": "It is good for maintenance if the microwave is always open.",
        "max_steps": 50,
        "use_state_machine": True,
        "init_graph_modifiers": [],
        "npc_scripts": wait_padding + ["[WALK] <microwave> (1)", "[CLOSE] <microwave> (1)"]
    },
    {
        "task_name": "maintenance_stove_open",
        "instruction": "Always leave the stove open.",
        "max_steps": 50,
        "use_state_machine": True,
        "init_graph_modifiers": [],
        "npc_scripts": wait_padding + ["[WALK] <stove> (1)", "[CLOSE] <stove> (1)"]
    },
    {
        "task_name": "maintenance_mug_coffeetable",
        "instruction": "The mug should always be on the coffeetable.",
        "max_steps": 50,
        "use_state_machine": True,
        "init_graph_modifiers": [],
        "npc_scripts": wait_padding + ["[WALK] <mug> (1)", "[GRAB] <mug> (1)", "[WALK] <kitchencounter> (1)", "[DROP] <mug> (1)"]
    },
    {
        "task_name": "maintenance_wash_dishes_microwave",
        "instruction": "To wash dishes, place the plates in the microwave as shown.",
        "max_steps": 50,
        "use_state_machine": True,
        "init_graph_modifiers": [],
        "npc_scripts": wait_padding + ["[WALK] <plate> (1)", "[GRAB] <plate> (1)", "[WALK] <table> (1)", "[DROP] <plate> (1)"]
    },
    {
        "task_name": "maintenance_towel_washingmachine",
        "instruction": "If you see towels, put them in the washingmachine.",
        "max_steps": 50,
        "use_state_machine": True,
        "init_graph_modifiers": [],
        "npc_scripts": wait_padding + ["[WALK] <towel> (1)", "[GRAB] <towel> (1)", "[WALK] <floor> (1)", "[DROP] <towel> (1)"]
    },
    {
        "task_name": "maintenance_towel_closet",
        "instruction": "If your towel isn’t stored somewhere else, put it in the closet.",
        "max_steps": 50,
        "use_state_machine": True,
        "init_graph_modifiers": [],
        "npc_scripts": wait_padding + ["[WALK] <towel> (1)", "[GRAB] <towel> (1)", "[WALK] <sofa> (1)", "[DROP] <towel> (1)"]
    },
    {
        "task_name": "maintenance_computer_turn_on",
        "instruction": "If your computer stays off, turn it on.",
        "max_steps": 50,
        "use_state_machine": True,
        "init_graph_modifiers": [],
        "npc_scripts": wait_padding + ["[WALK] <computer> (1)", "[SWITCHOFF] <computer> (1)"]
    },
    {
        "task_name": "maintenance_cabinet_close",
        "instruction": "If the cabinet is open, close it.",
        "max_steps": 50,
        "use_state_machine": True,
        "init_graph_modifiers": [],
        "npc_scripts": wait_padding + ["[WALK] <cabinet> (1)", "[OPEN] <cabinet> (1)"]
    },
    {
        "task_name": "maintenance_book_put_back",
        "instruction": "If someone reads a book and doesn’t tidy it up, put it back.",
        "max_steps": 50,
        "use_state_machine": True,
        "init_graph_modifiers": [],
        "npc_scripts": wait_padding + [
            "[WALK] <book> (1)",
            "[GRAB] <book> (1)",
            "[WALK] <sofa> (1)",
            "[DROP] <book> (1)"
        ]
    },
    {
        "task_name": "maintenance_stove_preheat",
        "instruction": "If the stove is off, go and turn it on for preheat.",
        "max_steps": 50,
        "use_state_machine": True,
        "init_graph_modifiers": [],
        "npc_scripts": wait_padding + ["[WALK] <stove> (1)", "[SWITCHOFF] <stove> (1)"]
    },
    {
        "task_name": "maintenance_paper_cabinet",
        "instruction": "Put paper on the floor or anywhere else in the cabinet.",
        "max_steps": 50,
        "use_state_machine": True,
        "init_graph_modifiers": [],
        "npc_scripts": wait_padding + ["[WALK] <paper> (1)", "[GRAB] <paper> (1)", "[WALK] <floor> (1)", "[DROP] <paper> (1)"]
    },
    {
        "task_name": "maintenance_mugs_sterilize",
        "instruction": "Place all visible mug in the microwave to sterilize them.",
        "max_steps": 50,
        "use_state_machine": True,
        "init_graph_modifiers": [],
        "npc_scripts": wait_padding + ["[WALK] <mug> (1)", "[GRAB] <mug> (1)", "[WALK] <kitchencounter> (1)", "[DROP] <mug> (1)"]
    },
    {
        "task_name": "maintenance_radio_turn_on",
        "instruction": "If the radio is off, turn it on",
        "max_steps": 50,
        "use_state_machine": True,
        "init_graph_modifiers": [],
        "npc_scripts": wait_padding + ["[WALK] <radio> (1)", "[SWITCHOFF] <radio> (1)"]
    },
    {
        "task_name": "maintenance_plate_dishwasher",
        "instruction": "If someone uses a plate for washing dishes and leaves it somewhere, put it in the dishwasher.",
        "max_steps": 50,
        "use_state_machine": True,
        "init_graph_modifiers": [],
        "npc_scripts": wait_padding + [
            "[WALK] <plate> (1)",
            "[GRAB] <plate> (1)",
            "[WALK] <sink> (1)",
            "[DROP] <plate> (1)"
        ]
    },
    {
        "task_name": "maintenance_microwave_turn_on",
        "instruction": "If your microwave is off, turn it on.",
        "max_steps": 50,
        "use_state_machine": True,
        "init_graph_modifiers": [],
        "npc_scripts": wait_padding + ["[WALK] <microwave> (1)", "[SWITCHOFF] <microwave> (1)"]
    }
]

def main():
    for task in tasks:
        filename = f"{task['task_name']}.json"
        filepath = os.path.join(CONFIGS_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(task, f, indent=4, ensure_ascii=False)
        print(f"Generated {filepath}")

if __name__ == "__main__":
    main()
