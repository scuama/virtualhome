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
  "selected_action": "[walk] <kitchencabinet> (234)",
  "top_candidates": [
    {
      "action": "[walk] <kitchencabinet> (234)",
      "say": 0.85,
      "can": 1.0,
      "combined": 0.85
    },
    {
      "action": "[walk] <kitchencabinet> (235)",
      "say": 0.8,
      "can": 1.0,
      "combined": 0.8
    },
    {
      "action": "[walk] <kitchencabinet> (236)",
      "say": 0.8,
      "can": 1.0,
      "combined": 0.8
    },
    {
      "action": "[walk] <kitchencabinet> (237)",
      "say": 0.8,
      "can": 1.0,
      "combined": 0.8
    },
    {
      "action": "[walk] <sink> (247)",
      "say": 0.2,
      "can": 1.0,
      "combined": 0.2
    },
    {
      "action": "[grab] <waterglass> (270)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[grab] <waterglass> (281)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <mug> (194)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <waterglass> (270)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <waterglass> (274)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    }
  ]
}
```
## Step 0
- **Action**: `[walk] <kitchencabinet> (234)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_05=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [SayCanScoring] Output
```json
{
  "selected_action": "[open] <kitchencabinet> (234)",
  "top_candidates": [
    {
      "action": "[open] <kitchencabinet> (234)",
      "say": 0.95,
      "can": 1.0,
      "combined": 0.95
    },
    {
      "action": "[open] <kitchencabinet> (235)",
      "say": 0.9,
      "can": 1.0,
      "combined": 0.9
    },
    {
      "action": "[walk] <mug> (194)",
      "say": 0.2,
      "can": 1.0,
      "combined": 0.2
    },
    {
      "action": "[walk] <kitchencabinet> (235)",
      "say": 0.05,
      "can": 1.0,
      "combined": 0.05
    },
    {
      "action": "[walk] <kitchencabinet> (234)",
      "say": 0.05,
      "can": 1.0,
      "combined": 0.0175
    },
    {
      "action": "[walk] <kitchencabinet> (236)",
      "say": 0.01,
      "can": 1.0,
      "combined": 0.01
    },
    {
      "action": "[walk] <kitchencabinet> (237)",
      "say": 0.01,
      "can": 1.0,
      "combined": 0.01
    },
    {
      "action": "[walk] <waterglass> (270)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <waterglass> (274)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <waterglass> (281)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    }
  ]
}
```
