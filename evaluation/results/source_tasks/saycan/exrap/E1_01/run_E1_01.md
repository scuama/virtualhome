# 🚀 VirtualHome Agent Episode Log


### [SayCanVersion] Output
```json
{
  "version": "SAYCAN-VH-v3.0-2026-07-16",
  "implementation": "SayCan (VirtualHome adaptation)",
  "say_score_mode": "explicit_candidate_relevance",
  "can_score_mode": "symbolic_task_independent_affordance",
  "say_context_mode": "state_summary",
  "task_semantics_in_can": false
}
```

### [SayCanScoring] Output
```json
{
  "selected_action": "[walk] <wallphone> (56)",
  "top_candidates": [
    {
      "action": "[walk] <wallphone> (56)",
      "say": 0.02,
      "can": 1.0,
      "combined": 0.02
    },
    {
      "action": "[grab] <wallphone> (56)",
      "say": 0.01,
      "can": 0.0,
      "combined": 0.0
    },
    {
      "action": "[switchon] <wallphone> (56)",
      "say": 0.03,
      "can": 0.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <tvstand> (157)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[plugin] <wallphone> (56)",
      "say": 0.0,
      "can": 0.0,
      "combined": 0.0
    },
    {
      "action": "[plugout] <wallphone> (56)",
      "say": 0.0,
      "can": 0.0,
      "combined": 0.0
    },
    {
      "action": "[grab] <plate> (104)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[grab] <candle> (124)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[grab] <wallpictureframe> (126)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[switchon] <candle> (124)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    }
  ]
}
```
## Step 0
- **Action**: `[walk] <wallphone> (56)`
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [SayCanScoring] Output
```json
{
  "selected_action": "[switchon] <wallphone> (56)",
  "top_candidates": [
    {
      "action": "[switchon] <wallphone> (56)",
      "say": 0.95,
      "can": 1.0,
      "combined": 0.95
    },
    {
      "action": "[grab] <wallphone> (56)",
      "say": 0.2,
      "can": 1.0,
      "combined": 0.2
    },
    {
      "action": "[plugin] <wallphone> (56)",
      "say": 0.1,
      "can": 1.0,
      "combined": 0.1
    },
    {
      "action": "[walk] <wallphone> (56)",
      "say": 0.05,
      "can": 1.0,
      "combined": 0.0175
    },
    {
      "action": "[walk] <powersocket> (57)",
      "say": 0.01,
      "can": 1.0,
      "combined": 0.01
    },
    {
      "action": "[walk] <lightswitch> (58)",
      "say": 0.01,
      "can": 1.0,
      "combined": 0.01
    },
    {
      "action": "[plugout] <wallphone> (56)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[switchoff] <lightswitch> (58)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[plugin] <lightswitch> (58)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[plugout] <lightswitch> (58)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    }
  ]
}
```
## Step 1
- **Action**: `[switchon] <wallphone> (56)`
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [SayCanScoring] Output
```json
{
  "selected_action": "[switchoff] <lightswitch> (58)",
  "top_candidates": [
    {
      "action": "[switchoff] <lightswitch> (58)",
      "say": 0.2,
      "can": 1.0,
      "combined": 0.2
    },
    {
      "action": "[walk] <wallphone> (56)",
      "say": 0.1,
      "can": 1.0,
      "combined": 0.1
    },
    {
      "action": "[grab] <wallphone> (56)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[switchoff] <wallphone> (56)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[plugin] <wallphone> (56)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[plugout] <wallphone> (56)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <powersocket> (57)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <lightswitch> (58)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[plugin] <lightswitch> (58)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[plugout] <lightswitch> (58)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    }
  ]
}
```
## Step 2
- **Action**: `[switchoff] <lightswitch> (58)`
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [SayCanScoring] Output
```json
{
  "selected_action": "[switchon] <lightswitch> (58)",
  "top_candidates": [
    {
      "action": "[switchon] <lightswitch> (58)",
      "say": 0.95,
      "can": 1.0,
      "combined": 0.95
    },
    {
      "action": "[plugin] <wallphone> (56)",
      "say": 0.05,
      "can": 1.0,
      "combined": 0.05
    },
    {
      "action": "[walk] <wallphone> (56)",
      "say": 0.02,
      "can": 1.0,
      "combined": 0.02
    },
    {
      "action": "[plugin] <lightswitch> (58)",
      "say": 0.02,
      "can": 1.0,
      "combined": 0.02
    },
    {
      "action": "[grab] <wallphone> (56)",
      "say": 0.01,
      "can": 1.0,
      "combined": 0.01
    },
    {
      "action": "[plugout] <wallphone> (56)",
      "say": 0.01,
      "can": 1.0,
      "combined": 0.01
    },
    {
      "action": "[walk] <powersocket> (57)",
      "say": 0.01,
      "can": 1.0,
      "combined": 0.01
    },
    {
      "action": "[walk] <lightswitch> (58)",
      "say": 0.01,
      "can": 1.0,
      "combined": 0.01
    },
    {
      "action": "[switchoff] <wallphone> (56)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[grab] <waterglass> (80)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    }
  ]
}
```
## Step 3
- **Action**: `[switchon] <lightswitch> (58)`
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [SayCanScoring] Output
```json
{
  "selected_action": "[grab] <wallphone> (56)",
  "top_candidates": [
    {
      "action": "[grab] <wallphone> (56)",
      "say": 0.05,
      "can": 1.0,
      "combined": 0.05
    },
    {
      "action": "[walk] <wallphone> (56)",
      "say": 0.05,
      "can": 1.0,
      "combined": 0.05
    },
    {
      "action": "[switchoff] <wallphone> (56)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[plugin] <wallphone> (56)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[plugout] <wallphone> (56)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[grab] <waterglass> (80)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[grab] <cutleryknife> (81)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[grab] <cutleryfork> (102)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <powersocket> (57)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <lightswitch> (58)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    }
  ]
}
```
