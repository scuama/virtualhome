# 🚀 VirtualHome Agent Episode Log


### [SayCanVersion] Output
```json
{
  "version": "SAYCAN-VH-v3.3-EXPLORATION-2026-07-17",
  "implementation": "SayCan (VirtualHome adaptation)",
  "interface": "BaseAgent.get_action",
  "say_score_mode": "explicit_candidate_relevance",
  "can_score_mode": "symbolic_task_independent_affordance",
  "say_context_mode": "state_summary",
  "task_semantics_in_can": false
}
```

### [SayCanScoring] Output
```json
{
  "selected_action": "[walk] <remotecontrol> (452)",
  "top_candidates": [
    {
      "action": "[walk] <remotecontrol> (452)",
      "say": 1.0,
      "can": 1.0,
      "combined": 1.0
    },
    {
      "action": "[walk] <sofa> (368)",
      "say": 0.01,
      "can": 1.0,
      "combined": 0.01
    }
  ]
}
```
## Step 0
- **Action**: `[walk] <remotecontrol> (452)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_03=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [SayCanScoring] Output
```json
{
  "selected_action": "[grab] <remotecontrol> (452)",
  "top_candidates": [
    {
      "action": "[grab] <remotecontrol> (452)",
      "say": 1.0,
      "can": 1.0,
      "combined": 1.0
    },
    {
      "action": "[walk] <remotecontrol> (452)",
      "say": 0.05,
      "can": 1.0,
      "combined": 0.0175
    },
    {
      "action": "[walk] <sofa> (368)",
      "say": 0.01,
      "can": 1.0,
      "combined": 0.01
    }
  ]
}
```
## Step 1
- **Action**: `[grab] <remotecontrol> (452)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_03=done
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

