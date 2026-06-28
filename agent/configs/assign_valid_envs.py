import os
import json

def assign_envs():
    config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'g_class'))
    env_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'env_objects.json'))
    
    with open(env_file, 'r', encoding='utf-8') as f:
        env_objects = json.load(f)
        
    for fname in sorted(os.listdir(config_dir)):
        if not fname.endswith('.json'): continue
        path = os.path.join(config_dir, fname)
        
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        required_classes = set()
        
        # from success condition
        if 'success_condition' in config:
            sc = config['success_condition']
            if 'target_class' in sc:
                required_classes.add(sc['target_class'].lower())
        
        # from initial overrides
        if 'initial_relations_override' in config:
            for rel in config['initial_relations_override']:
                if rel.get('subject') and rel['subject'] != 'character':
                    required_classes.add(rel['subject'].lower())
                if rel.get('object') and rel['object'] not in ['kitchen', 'bedroom', 'livingroom', 'bathroom']:
                    required_classes.add(rel['object'].lower())
                    
        # find valid env
        valid_env = None
        for env_id_str, class_counts in env_objects.items():
            if env_id_str == '5': continue # skip 5 since it crashed
            
            is_valid = True
            for req in required_classes:
                if req not in class_counts:
                    is_valid = False
                    break
            
            if is_valid:
                valid_env = int(env_id_str)
                break
                
        if valid_env is not None:
            config['environment_id'] = valid_env
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            print(f"Assigned {fname} to env {valid_env} (Required: {required_classes})")
        else:
            print(f"FAILED to find env for {fname}! Required: {required_classes}")

if __name__ == '__main__':
    assign_envs()
