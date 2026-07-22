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
  "selected_action": "[walk] <bedroom> (346)",
  "top_candidates": [
    {
      "action": "[walk] <bedroom> (346)",
      "say": 0.9,
      "can": 1.0,
      "combined": 0.9
    },
    {
      "action": "[walk] <kitchen> (11)",
      "say": 0.1,
      "can": 1.0,
      "combined": 0.1
    },
    {
      "action": "[walk] <livingroom> (183)",
      "say": 0.1,
      "can": 1.0,
      "combined": 0.1
    },
    {
      "action": "[walk] <door> (254)",
      "say": 0.1,
      "can": 1.0,
      "combined": 0.1
    },
    {
      "action": "[walk] <bathroom> (285)",
      "say": 0.1,
      "can": 1.0,
      "combined": 0.1
    }
  ]
}
```
## Step 0
- **Action**: `[walk] <bedroom> (346)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: E1_11=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [SayCanScoring] Output
```json
{
  "selected_action": "[walk] <computer> (397)",
  "top_candidates": [
    {
      "action": "[walk] <computer> (397)",
      "say": 1.0,
      "can": 1.0,
      "combined": 1.0
    }
  ]
}
```
## Step 1
- **Action**: `[walk] <computer> (397)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: E1_11=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [SayCanScoring] Output
```json
{
  "selected_action": "[switchon] <computer> (397)",
  "top_candidates": [
    {
      "action": "[switchon] <computer> (397)",
      "say": 1.0,
      "can": 1.0,
      "combined": 1.0
    },
    {
      "action": "[walk] <computer> (397)",
      "say": 0.01,
      "can": 1.0,
      "combined": 0.0035
    }
  ]
}
```
## Step 2
- **Action**: `[switchon] <computer> (397)`
- **Action Success**: `True`
- **Action Message**: Faked switch operation in Python layer (bypassed Unity failure)
- **Task Progress**: E1_11=done
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

