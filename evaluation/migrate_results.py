import os
import shutil
from pathlib import Path
import json

def migrate():
    base_dir = Path(__file__).parent.parent
    results_dir = base_dir / "evaluation" / "results"
    configs_dir = base_dir / "evaluation" / "configs"
    
    if not results_dir.exists():
        print("No results directory found.")
        return

    # Build scenario -> subclass mapping
    scenario_to_subclass = {}
    source_tasks_dir = configs_dir / "source_tasks"
    if source_tasks_dir.exists():
        for p in source_tasks_dir.rglob("*.json"):
            subclass = p.parent.name
            scenario_id = p.stem
            scenario_to_subclass[scenario_id] = subclass

    # 1. Migrate Table 1
    table1_dir = results_dir / "table1"
    if table1_dir.exists():
        print("Migrating Table 1...")
        for axis_dir in list(table1_dir.iterdir()):
            if not axis_dir.is_dir() or axis_dir.name in ("robostate", "saycan", "llm_planner", "re_act"):
                continue # Already migrated or method dir
            
            axis = axis_dir.name
            new_axis = "dynamic" if axis == "dynamic_difficulty" else axis
            
            for setting_dir in axis_dir.iterdir():
                if not setting_dir.is_dir(): continue
                setting = setting_dir.name
                
                for method_dir in setting_dir.iterdir():
                    if not method_dir.is_dir(): continue
                    method = method_dir.name
                    
                    for sample_dir in method_dir.iterdir():
                        if not sample_dir.is_dir(): continue
                        
                        target_dir = table1_dir / method / new_axis / setting / sample_dir.name
                        target_dir.parent.mkdir(parents=True, exist_ok=True)
                        if not target_dir.exists():
                            shutil.move(str(sample_dir), str(target_dir))
                            print(f"Moved T1: {sample_dir} -> {target_dir}")
        
        # Cleanup old table1
        for axis_dir in list(table1_dir.iterdir()):
            if axis_dir.is_dir() and axis_dir.name not in ("robostate", "saycan", "llm_planner", "re_act"):
                try:
                    shutil.rmtree(axis_dir)
                except Exception as e:
                    pass
                    
    # 2. Migrate Table 3
    table3_dir = results_dir / "table3"
    if table3_dir.exists():
        print("Migrating Table 3...")
        for ablation_dir in list(table3_dir.iterdir()):
            if ablation_dir.name == "runs": continue
            if not ablation_dir.is_dir(): continue
            
            profile = ablation_dir.name
            
            for method_dir in ablation_dir.iterdir():
                if not method_dir.is_dir(): continue
                method = method_dir.name # we drop this!
                
                for sample_dir in method_dir.iterdir():
                    if not sample_dir.is_dir(): continue
                    
                    target_dir = table3_dir / "runs" / profile / sample_dir.name
                    target_dir.parent.mkdir(parents=True, exist_ok=True)
                    if not target_dir.exists():
                        shutil.move(str(sample_dir), str(target_dir))
                        print(f"Moved T3: {sample_dir} -> {target_dir}")
                        
        # Cleanup old table3
        for ablation_dir in list(table3_dir.iterdir()):
            if ablation_dir.name != "runs":
                try:
                    shutil.rmtree(ablation_dir)
                except:
                    pass

    # 3. Migrate Source Tasks (Legacy standard directories)
    print("Migrating Source Tasks...")
    methods = ["robostate", "saycan", "llm_planner", "re_act"]
    for method in methods:
        method_dir = results_dir / method
        if not method_dir.exists(): continue
        
        for outcome in ["success", "fail"]:
            outcome_dir = method_dir / outcome
            if not outcome_dir.exists(): continue
            
            for scenario_dir in outcome_dir.iterdir():
                if not scenario_dir.is_dir(): continue
                scenario_id = scenario_dir.name
                
                subclass = scenario_to_subclass.get(scenario_id)
                if subclass is None:
                    # Could be table 2? Let's check table 2 configs!
                    table2_dir_configs = configs_dir / "table2"
                    is_t2 = False
                    if table2_dir_configs.exists():
                        for p in table2_dir_configs.rglob("*.json"):
                            if p.stem == scenario_id:
                                is_t2 = True
                                break
                    if is_t2:
                        print(f"Skipping {scenario_id} as it looks like a Table 2 scenario. (Wait, Table 2 config task_id might differ. Either way, will skip)")
                        continue
                    
                    subclass = "unknown"
                    
                target_dir = results_dir / "source_tasks" / method / subclass / scenario_id
                target_dir.parent.mkdir(parents=True, exist_ok=True)
                if not target_dir.exists():
                    shutil.move(str(scenario_dir), str(target_dir))
                    print(f"Moved Source Task: {scenario_dir} -> {target_dir}")
                    
            try:
                shutil.rmtree(outcome_dir)
            except:
                pass
                
        # Clean up method dir if it's empty (aside from success/fail which should be removed)
        try:
            if not any(method_dir.iterdir()):
                method_dir.rmdir()
        except:
            pass

    # 4. Migrate Table 2 Raw Results
    table2_raw_dir = results_dir / "robostate" / "raw"
    if table2_raw_dir.exists():
        print("Migrating Table 2 Raw Results...")
        table2_dir_configs = configs_dir / "table2"
        t2_config_info = {}
        if table2_dir_configs.exists():
            for p in table2_dir_configs.rglob("*.json"):
                try:
                    with open(p, 'r') as f:
                        cfg = json.load(f)
                    axis = cfg.get("experiment_axis", "unknown")
                    if axis == "dynamic_difficulty":
                        axis = "non_stationarity"
                    
                    setting = cfg.get("setting", "unknown")
                    if setting == "unknown":
                        if axis == "non_stationarity":
                            setting = str(cfg.get('dynamic_difficulty', 'unknown'))
                        elif axis == "scale":
                            scale_val = cfg.get('instruction_scale', 'unknown')
                            setting = f"S{scale_val}" if scale_val != 'unknown' else 'unknown'
                        elif axis == "instruction_type":
                            setting = str(cfg.get('instruction_type', 'unknown'))
                            
                    t2_config_info[p.stem] = (axis, setting)
                except Exception as e:
                    pass
        
        for md_file in table2_raw_dir.glob("run_*.md"):
            scenario_id = md_file.stem[4:]  # remove 'run_' prefix
            if scenario_id in t2_config_info:
                axis, setting = t2_config_info[scenario_id]
                target_dir = results_dir / "table2" / "robostate" / axis / setting / scenario_id
                target_dir.mkdir(parents=True, exist_ok=True)
                
                target_file = target_dir / md_file.name
                if not target_file.exists():
                    shutil.move(str(md_file), str(target_file))
                    print(f"Moved T2 Raw: {md_file.name} -> {target_dir}")

    print("Migration complete!")

if __name__ == "__main__":
    migrate()
