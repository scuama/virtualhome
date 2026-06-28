"""
e2e_env_test.py — VirtualHome 场景配置合法性校验器

功能：
  1. 静态校验（无需 Unity）：字段格式、类名、一致性检查
  2. 动态校验（需启动 Unity）：在引擎中实际重置场景并验证初始条件

用法：
  python3 e2e_env_test.py                     # 静态 + 动态全量校验 (g_class/)
  python3 e2e_env_test.py --static-only        # 仅静态校验，不启动 Unity
  python3 e2e_env_test.py --dynamic-only       # 仅动态校验（需 Unity 已就绪）
  python3 e2e_env_test.py --dir m_class        # 指定目录
  python3 e2e_env_test.py --file G1_01.json    # 指定单文件
"""

import json
import os
import sys
import argparse
import glob

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# ───────────────────────────────────────────
#  已知 class_name 白名单（来自 env_objects.json 探测结果）
# ───────────────────────────────────────────
KNOWN_CLASS_NAMES = {
    'alcohol', 'amplifier', 'apple', 'bananas', 'barsoap', 'bathroom',
    'bathroomcabinet', 'bathroomcounter', 'bathtub', 'bed', 'bedroom',
    'bellpepper', 'bench', 'boardgame', 'book', 'bookshelf', 'bottlewater',
    'box', 'breadslice', 'cabinet', 'candle', 'candybar', 'ceiling',
    'ceilingfan', 'ceilinglamp', 'cellphone', 'cereal', 'chair', 'character',
    'chicken', 'chips', 'chocolatesyrup', 'clock', 'closet', 'closetdrawer',
    'clothespants', 'clothespile', 'clothesshirt', 'coffeemaker', 'coffeepot',
    'coffeetable', 'computer', 'condimentbottle', 'condimentshaker',
    'cookingpot', 'cpuscreen', 'crackers', 'crayons', 'creamybuns', 'cupcake',
    'curtains', 'cutleryfork', 'cutleryknife', 'cutlets', 'deodorant', 'desk',
    'dishbowl', 'dishwasher', 'dishwashingliquid', 'door', 'doorjamb',
    'facecream', 'faucet', 'floor', 'folder', 'fridge', 'fryingpan',
    'garbagecan', 'guitar', 'hairproduct', 'hanger', 'juice', 'keyboard',
    'kitchen', 'kitchencabinet', 'kitchencounter', 'kitchencounterdrawer',
    'kitchentable', 'knifeblock', 'lightswitch', 'lime', 'livingroom',
    'magazine', 'microwave', 'milk', 'milkshake', 'mincedmeat', 'mouse',
    'mousemat', 'mug', 'nightstand', 'notes', 'orchid', 'oventray',
    'painkillers', 'pancake', 'paper', 'papertray', 'peach', 'pear',
    'perfume', 'photoframe', 'pie', 'pillow', 'plate', 'plum', 'poundcake',
    'powersocket', 'pudding', 'radio', 'remotecontrol', 'rug', 'salmon',
    'sink', 'slippers', 'sofa', 'speaker', 'stall', 'stove', 'stovefan',
    'sundae', 'tablelamp', 'toaster', 'toilet', 'toiletpaper', 'toothbrush',
    'toothpaste', 'towel', 'towelrack', 'toy', 'tv', 'tvstand', 'wall',
    'walllamp', 'wallphone', 'wallpictureframe', 'wallshelf', 'washingmachine',
    'washingsponge', 'waterglass', 'whippedcream', 'window', 'wine', 'wineglass'
}

# 合法的 check_type 值
VALID_CHECK_TYPES = {'state', 'physical_state', 'relation', 'agent_action'}

# 合法的 relation 类型（Unity graph edge relation_type）
VALID_RELATIONS = {'ON', 'INSIDE', 'CLOSE', 'HOLDS_RH', 'HOLDS_LH', 'BETWEEN',
                   'FACING', 'SITTINGRELATION', 'LYINGON', 'IN_FRONT_OF'}

# 合法的 state 值
VALID_STATES = {'ON', 'OFF', 'OPEN', 'CLOSED', 'DIRTY', 'CLEAN', 'FULL',
                'EMPTY', 'HOT', 'COLD', 'WARM', 'COOKED', 'BROKEN', 'FILLED',
                'PLUGGED_OUT', 'PLUGGED_IN', 'SITTING', 'LYING', 'HAS_SWITCH'}

VALID_QUANTIFIERS = {'any', 'all'}


# ───────────────────────────────────────────────────────────────
# STATIC VALIDATOR
# ───────────────────────────────────────────────────────────────

def validate_class_name(name, field_path, errors):
    """Check that a class name exists in the known whitelist."""
    if name.lower() not in KNOWN_CLASS_NAMES:
        errors.append(
            f"[CLASS_NAME] '{name}' in '{field_path}' is not a known VirtualHome class. "
            f"Check spelling — common issues: 'remote_control' → 'remotecontrol', "
            f"'table_lamp' → 'tablelamp', 'kitchen_table' → 'kitchentable'."
        )


def validate_relation_type(rel, field_path, errors):
    if rel not in VALID_RELATIONS:
        errors.append(f"[RELATION_TYPE] '{rel}' in '{field_path}' is not a known relation type. Valid: {VALID_RELATIONS}")


def validate_state(state, field_path, errors, warnings):
    if state.upper() not in VALID_STATES:
        warnings.append(f"[STATE] '{state}' in '{field_path}' is not a commonly known state. Verify it is supported by Unity engine.")


def validate_config_static(config, scenario_id):
    """
    Perform static (no-Unity) validation of a scenario JSON config.
    Returns (errors, warnings) lists.
    """
    errors = []
    warnings = []

    # ── environment_id ──────────────────────────────────────────
    env_id = config.get('environment_id')
    if env_id is None:
        errors.append("[MISSING] 'environment_id' is required.")
    elif env_id not in [0, 1, 2, 3, 4, 6]:
        errors.append(f"[ENV_ID] environment_id={env_id} is not a known valid environment. "
                      f"Valid: [0, 1, 2, 3, 4, 6] (5 is unstable).")

    # ── goal_instruction ───────────────────────────────────────
    if not config.get('goal_instruction'):
        errors.append("[MISSING] 'goal_instruction' is required.")

    # ── initial_relations_override ─────────────────────────────
    for i, rel in enumerate(config.get('initial_relations_override', [])):
        prefix = f"initial_relations_override[{i}]"
        for field in ('subject', 'relation', 'object'):
            if field not in rel:
                errors.append(f"[MISSING] '{field}' missing in {prefix}")
        subj = rel.get('subject', '')
        obj  = rel.get('object', '')
        rel_type = rel.get('relation', '')
        if subj:
            validate_class_name(subj, f"{prefix}.subject", errors)
        if obj:
            validate_class_name(obj, f"{prefix}.object", errors)
        if rel_type:
            validate_relation_type(rel_type, f"{prefix}.relation", errors)
        if subj != 'character' and rel.get('count', 1) < 1:
            errors.append(f"[COUNT] {prefix}.count must be >= 1.")

    # ── initial_states_override ────────────────────────────────
    for i, ov in enumerate(config.get('initial_states_override', [])):
        prefix = f"initial_states_override[{i}]"
        if 'target_classes' not in ov:
            errors.append(f"[MISSING] 'target_classes' missing in {prefix}")
        for cls in ov.get('target_classes', []):
            validate_class_name(cls, f"{prefix}.target_classes", errors)
        # Must have at least one of add_states / remove_states
        if not ov.get('add_states') and not ov.get('remove_states'):
            errors.append(f"[MISSING] {prefix} must have at least 'add_states' or 'remove_states'.")
        for state in ov.get('add_states', []):
            validate_state(state, f"{prefix}.add_states", errors, warnings)
        for state in ov.get('remove_states', []):
            validate_state(state, f"{prefix}.remove_states", errors, warnings)
        # in_room: must be a valid room name if specified
        if 'in_room' in ov:
            valid_rooms = {'kitchen', 'bedroom', 'livingroom', 'bathroom'}
            if ov['in_room'].lower() not in valid_rooms:
                errors.append(f"[IN_ROOM] {prefix}.in_room='{ov['in_room']}' invalid. Valid: {valid_rooms}")


    # ── success_condition ──────────────────────────────────────
    sc = config.get('success_condition')
    if not sc:
        errors.append("[MISSING] 'success_condition' is required.")
    else:
        check_type = sc.get('check_type', '')
        if check_type not in VALID_CHECK_TYPES:
            errors.append(f"[CHECK_TYPE] success_condition.check_type='{check_type}' is invalid. "
                          f"Valid: {VALID_CHECK_TYPES}")

        if check_type in ('state', 'physical_state'):
            if 'target_class' not in sc:
                errors.append("[MISSING] success_condition.target_class required for state/physical_state check.")
            else:
                validate_class_name(sc['target_class'], 'success_condition.target_class', errors)
            # Must have require_state OR require_states
            if not sc.get('require_states') and not sc.get('require_state'):
                errors.append("[MISSING] success_condition must have 'require_states' (list) or 'require_state' (str).")
            for s in sc.get('require_states', []):
                validate_state(s, 'success_condition.require_states', errors, warnings)
            if sc.get('quantifier') and sc['quantifier'] not in VALID_QUANTIFIERS:
                errors.append(f"[QUANTIFIER] success_condition.quantifier='{sc['quantifier']}' invalid. Valid: {VALID_QUANTIFIERS}")

        elif check_type == 'relation':
            # Reject legacy array format — must use flat fields now
            if 'require_relation' in sc and isinstance(sc['require_relation'], list):
                errors.append(
                    "[FORMAT] success_condition.require_relation array format is deprecated. "
                    "Use flat fields: 'subject', 'relation', 'object' instead."
                )
            else:
                subject = sc.get('subject', sc.get('target_class', ''))
                relation = sc.get('relation', '')
                obj = sc.get('object', sc.get('destination_class', ''))
                if not subject:
                    errors.append("[MISSING] success_condition.subject (or target_class) required for relation check.")
                else:
                    validate_class_name(subject, 'success_condition.subject', errors)
                if not relation:
                    errors.append("[MISSING] success_condition.relation required for relation check.")
                else:
                    validate_relation_type(relation, 'success_condition.relation', errors)
                if not obj:
                    errors.append("[MISSING] success_condition.object (or destination_class) required for relation check.")
                else:
                    validate_class_name(obj, 'success_condition.object', errors)

                # Flat-field fallback
                if sc.get('fallback_relation_subject'):
                    validate_class_name(sc['fallback_relation_subject'], 'success_condition.fallback_relation_subject', errors)
                    validate_relation_type(sc.get('fallback_relation', ''), 'success_condition.fallback_relation', errors)
                    validate_class_name(sc.get('fallback_relation_object', ''), 'success_condition.fallback_relation_object', errors)

        elif check_type == 'agent_action':
            if not sc.get('require_action'):
                errors.append("[MISSING] success_condition.require_action required for agent_action check.")

    # ── failure_condition ──────────────────────────────────────
    fc = config.get('failure_condition')
    if fc:
        fc_type = fc.get('check_type', '')
        if fc_type not in VALID_CHECK_TYPES:
            errors.append(f"[CHECK_TYPE] failure_condition.check_type='{fc_type}' invalid.")
        if 'start_step' not in fc or 'end_step' not in fc:
            warnings.append("[FAILURE_COND] failure_condition should have 'start_step' and 'end_step'.")

    # ── hidden_broken_classes ──────────────────────────────────
    for cls in config.get('hidden_broken_classes', []):
        validate_class_name(cls, 'hidden_broken_classes', errors)

    # ── scheduled_rules ────────────────────────────────────────
    for i, rule in enumerate(config.get('scheduled_rules', [])):
        if 'start_step' not in rule or 'end_step' not in rule:
            errors.append(f"[MISSING] scheduled_rules[{i}] must have 'start_step' and 'end_step'.")
        if not rule.get('rule_text'):
            errors.append(f"[MISSING] scheduled_rules[{i}].rule_text is required.")

    return errors, warnings


# ───────────────────────────────────────────────────────────────
# DYNAMIC VALIDATOR (Unity)
# ───────────────────────────────────────────────────────────────

def get_node_by_class(graph, class_name):
    return [n for n in graph['nodes'] if n['class_name'].lower() == class_name.lower()]


def validate_config_dynamic(env, config, scenario_id):
    """
    Dynamic validation: reset Unity scene and verify initial conditions hold.
    Returns (passed, issues) where passed is bool and issues is list of strings.
    """
    issues = []

    env_id = config.get('environment_id', 0)
    print(f"  Resetting env {env_id}...")
    env.reset(environment_id=env_id)

    graph = env.get_graph()

    # 1. Verify all required classes exist in the scene
    required_classes = set()
    for rel in config.get('initial_relations_override', []):
        if rel.get('subject') and rel['subject'] != 'character':
            required_classes.add(rel['subject'].lower())
        if rel.get('object') and rel['object'] not in ('kitchen', 'bedroom', 'livingroom', 'bathroom', 'floor'):
            required_classes.add(rel['object'].lower())
    for ov in config.get('initial_states_override', []):
        for cls in ov.get('target_classes', []):
            required_classes.add(cls.lower())
    sc = config.get('success_condition', {})
    for field in ('target_class', 'subject', 'object', 'destination_class'):
        if sc.get(field) and sc[field] not in ('character',):
            required_classes.add(sc[field].lower())

    for cls in required_classes:
        nodes = get_node_by_class(graph, cls)
        if not nodes:
            issues.append(f"[MISSING_IN_ENV] '{cls}' not found in environment {env_id}.")
        else:
            print(f"  ✓ '{cls}' present ({len(nodes)} instance(s))")

    # 2. Verify count constraints: initial_relations_override count <= available instances
    for rel in config.get('initial_relations_override', []):
        subj = rel.get('subject', '')
        if subj == 'character':
            continue
        count = rel.get('count', 1)
        nodes = get_node_by_class(graph, subj)
        if len(nodes) < count:
            issues.append(
                f"[COUNT_MISMATCH] '{subj}' requires count={count} but only {len(nodes)} "
                f"instance(s) exist in env {env_id}. "
                f"Consider using a different environment_id."
            )
        else:
            print(f"  ✓ '{subj}' count OK: {len(nodes)} >= {count}")

    passed = len(issues) == 0
    return passed, issues


# ───────────────────────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='VirtualHome Config Validator')
    parser.add_argument('--static-only', action='store_true', help='Only run static validation')
    parser.add_argument('--dynamic-only', action='store_true', help='Only run dynamic (Unity) validation')
    parser.add_argument('--dir', type=str, default='g_class', help='Config subdirectory (default: g_class)')
    parser.add_argument('--file', type=str, default=None, help='Single config file to validate')
    args = parser.parse_args()

    base_dir = os.path.dirname(__file__)

    # Collect configs
    if args.file:
        config_paths = [os.path.join(base_dir, args.dir, args.file)]
        if not os.path.exists(config_paths[0]):
            config_paths = [os.path.join(base_dir, args.file)]
    else:
        config_dir = os.path.join(base_dir, args.dir)
        config_paths = sorted(glob.glob(os.path.join(config_dir, '*.json')))

    if not config_paths:
        print(f"No configs found in '{args.dir}'. Check the --dir argument.")
        return

    do_static  = not args.dynamic_only
    do_dynamic = not args.static_only

    # ── Static phase ──────────────────────────────────────────
    static_results = {}  # scenario_id -> (errors, warnings)
    if do_static:
        print("\n══════════════════════════════════════════")
        print("  PHASE 1: STATIC VALIDATION")
        print("══════════════════════════════════════════")
        for path in config_paths:
            sid = os.path.basename(path).replace('.json', '')
            with open(path, encoding='utf-8') as f:
                config = json.load(f)
            errors, warnings = validate_config_static(config, sid)
            static_results[sid] = (errors, warnings)
            if errors:
                print(f"\n  ❌ {sid}")
                for e in errors:
                    print(f"     ERROR: {e}")
                for w in warnings:
                    print(f"     WARN:  {w}")
            elif warnings:
                print(f"\n  ⚠️  {sid}")
                for w in warnings:
                    print(f"     WARN:  {w}")
            else:
                print(f"  ✅ {sid} — OK")

        total_err = sum(1 for e, _ in static_results.values() if e)
        print(f"\n  Static: {len(config_paths) - total_err}/{len(config_paths)} passed, {total_err} with errors.\n")

        # If static errors, don't run dynamic unless forced
        if total_err > 0 and not args.dynamic_only:
            print("  ⚠️  Fix static errors before running dynamic validation.")
            return

    # ── Dynamic phase ─────────────────────────────────────────
    if do_dynamic:
        from virtualhome.simulation.environment.unity_environment import UnityEnvironment

        print("\n══════════════════════════════════════════")
        print("  PHASE 2: DYNAMIC VALIDATION (Unity)")
        print("══════════════════════════════════════════")

        exec_path = os.path.abspath(os.path.join(
            base_dir, '../../virtualhome/simulation/unity_simulator/macos_exec.v2.3.0.app'))
        env = UnityEnvironment(
            num_agents=1,
            observation_types=['partial'],
            executable_args={'file_name': exec_path, 'no_graphics': True}
        )

        all_passed = True
        for path in config_paths:
            sid = os.path.basename(path).replace('.json', '')
            print(f"\n  [{sid}]")
            with open(path, encoding='utf-8') as f:
                config = json.load(f)
            try:
                passed, issues = validate_config_dynamic(env, config, sid)
            except Exception as ex:
                passed = False
                issues = [f"Exception: {ex}"]

            if passed:
                print(f"  ✅ {sid} — Dynamic validation PASSED")
            else:
                print(f"  ❌ {sid} — Dynamic validation FAILED")
                for iss in issues:
                    print(f"     {iss}")
                all_passed = False

        if all_passed:
            print("\n\n✅ ALL SCENARIOS DYNAMICALLY VERIFIED IN UNITY ENGINE.")
        else:
            print("\n\n❌ SOME SCENARIOS FAILED DYNAMIC VALIDATION.")


if __name__ == "__main__":
    main()
