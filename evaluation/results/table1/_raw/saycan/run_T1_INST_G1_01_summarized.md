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
  "selected_action": "[walk] <fridge> (162)",
  "top_candidates": [
    {
      "action": "[walk] <fridge> (162)",
      "say": 0.95,
      "can": 1.0,
      "combined": 0.95
    },
    {
      "action": "[walk] <microwave> (171)",
      "say": 0.1,
      "can": 1.0,
      "combined": 0.1
    },
    {
      "action": "[walk] <milk> (176)",
      "say": 0.05,
      "can": 1.0,
      "combined": 0.05
    },
    {
      "action": "[walk] <milk> (177)",
      "say": 0.05,
      "can": 1.0,
      "combined": 0.05
    },
    {
      "action": "[walk] <wallphone> (56)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <fryingpan> (62)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <cookingpot> (63)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <kitchencounter> (146)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <kitchencounterdrawer> (152)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <stove> (163)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    }
  ]
}
```
## Step 0
- **Action**: `[walk] <fridge> (162)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_01=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [SayCanScoring] Output
```json
{
  "selected_action": "[grab] <milk> (176)",
  "top_candidates": [
    {
      "action": "[grab] <milk> (176)",
      "say": 0.95,
      "can": 1.0,
      "combined": 0.95
    },
    {
      "action": "[walk] <microwave> (171)",
      "say": 0.2,
      "can": 1.0,
      "combined": 0.2
    },
    {
      "action": "[walk] <milk> (176)",
      "say": 0.1,
      "can": 1.0,
      "combined": 0.1
    },
    {
      "action": "[close] <fridge> (162)",
      "say": 0.05,
      "can": 1.0,
      "combined": 0.05
    },
    {
      "action": "[walk] <milk> (177)",
      "say": 0.05,
      "can": 1.0,
      "combined": 0.05
    },
    {
      "action": "[walk] <fridge> (162)",
      "say": 0.05,
      "can": 1.0,
      "combined": 0.0175
    },
    {
      "action": "[walk] <wallphone> (56)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[switchon] <toaster> (166)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <fryingpan> (62)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <cookingpot> (63)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    }
  ]
}
```
## Step 1
- **Action**: `[grab] <milk> (176)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_01=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [SayCanScoring] Output
```json
{
  "selected_action": "[walk] <microwave> (171)",
  "top_candidates": [
    {
      "action": "[walk] <microwave> (171)",
      "say": 1.0,
      "can": 1.0,
      "combined": 1.0
    },
    {
      "action": "[putin] <milk> (176) <fridge> (162)",
      "say": 0.05,
      "can": 1.0,
      "combined": 0.05
    },
    {
      "action": "[walk] <fridge> (162)",
      "say": 0.1,
      "can": 1.0,
      "combined": 0.008
    },
    {
      "action": "[putin] <milk> (176) <toaster> (166)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[close] <fridge> (162)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <wallphone> (56)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <milk> (177)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[switchon] <toaster> (166)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <fryingpan> (62)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <cookingpot> (63)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    }
  ]
}
```
## Step 2
- **Action**: `[walk] <microwave> (171)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_01=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [SayCanScoring] Output
```json
{
  "selected_action": "[switchon] <microwave> (171)",
  "top_candidates": [
    {
      "action": "[switchon] <microwave> (171)",
      "say": 0.95,
      "can": 1.0,
      "combined": 0.95
    },
    {
      "action": "[open] <microwave> (171)",
      "say": 0.8,
      "can": 1.0,
      "combined": 0.8
    },
    {
      "action": "[grab] <milk> (177)",
      "say": 0.15,
      "can": 1.0,
      "combined": 0.15
    },
    {
      "action": "[walk] <wallphone> (56)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <fridge> (162)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <microwave> (171)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <milk> (177)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[plugin] <microwave> (171)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[grab] <cutlets> (175)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <fryingpan> (62)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    }
  ]
}
```
## Step 3
- **Action**: `[switchon] <microwave> (171)`
- **Action Success**: `True`
- **Action Message**: Faked switch operation in Python layer (bypassed Unity failure)
- **Task Progress**: G1_01=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [SayCanScoring] Output
```json
{
  "selected_action": "[open] <microwave> (171)",
  "top_candidates": [
    {
      "action": "[open] <microwave> (171)",
      "say": 0.95,
      "can": 1.0,
      "combined": 0.95
    },
    {
      "action": "[grab] <milk> (177)",
      "say": 0.15,
      "can": 1.0,
      "combined": 0.15
    },
    {
      "action": "[walk] <microwave> (171)",
      "say": 0.05,
      "can": 1.0,
      "combined": 0.004
    },
    {
      "action": "[walk] <wallphone> (56)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <fridge> (162)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <milk> (177)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[plugin] <microwave> (171)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[grab] <cutlets> (175)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <fryingpan> (62)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <cookingpot> (63)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    }
  ]
}
```
## Step 4
- **Action**: `[open] <microwave> (171)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_01=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [SayCanScoring] Output
```json
{
  "selected_action": "[putin] <milk> (176) <microwave> (171)",
  "top_candidates": [
    {
      "action": "[putin] <milk> (176) <microwave> (171)",
      "say": 1.0,
      "can": 1.0,
      "combined": 1.0
    },
    {
      "action": "[grab] <milk> (177)",
      "say": 0.01,
      "can": 1.0,
      "combined": 0.01
    },
    {
      "action": "[close] <microwave> (171)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <wallphone> (56)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <fridge> (162)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <microwave> (171)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <milk> (177)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[plugin] <microwave> (171)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[grab] <dishbowl> (172)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[grab] <cutlets> (175)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    }
  ]
}
```
## Step 5
- **Action**: `[putin] <milk> (176) <microwave> (171)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_01=done
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

