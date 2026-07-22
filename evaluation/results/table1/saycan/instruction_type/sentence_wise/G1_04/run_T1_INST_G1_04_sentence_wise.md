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
  "selected_action": "[walk] <tablelamp> (102)",
  "top_candidates": [
    {
      "action": "[walk] <tablelamp> (102)",
      "say": 0.95,
      "can": 1.0,
      "combined": 0.95
    },
    {
      "action": "[walk] <tablelamp> (103)",
      "say": 0.95,
      "can": 1.0,
      "combined": 0.95
    },
    {
      "action": "[walk] <coffeetable> (111)",
      "say": 0.05,
      "can": 1.0,
      "combined": 0.05
    },
    {
      "action": "[walk] <nightstand> (104)",
      "say": 0.05,
      "can": 1.0,
      "combined": 0.05
    },
    {
      "action": "[walk] <nightstand> (106)",
      "say": 0.05,
      "can": 1.0,
      "combined": 0.05
    },
    {
      "action": "[walk] <ceilinglamp> (101)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[grab] <candle> (181)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[grab] <cellphone> (188)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[grab] <wineglass> (197)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[grab] <wineglass> (198)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    }
  ]
}
```
## Step 0
- **Action**: `[walk] <tablelamp> (102)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_04=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [SayCanScoring] Output
```json
{
  "selected_action": "[switchoff] <tablelamp> (102)",
  "top_candidates": [
    {
      "action": "[switchoff] <tablelamp> (102)",
      "say": 1.0,
      "can": 1.0,
      "combined": 1.0
    },
    {
      "action": "[walk] <tablelamp> (102)",
      "say": 0.05,
      "can": 1.0,
      "combined": 0.0175
    },
    {
      "action": "[walk] <tablelamp> (103)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <coffeetable> (111)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <ceilinglamp> (101)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[open] <nightstand> (104)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <floor> (78)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <nightstand> (104)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <nightstand> (106)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    },
    {
      "action": "[walk] <candle> (181)",
      "say": 0.0,
      "can": 1.0,
      "combined": 0.0
    }
  ]
}
```
## Step 1
- **Action**: `[switchoff] <tablelamp> (102)`
- **Action Success**: `True`
- **Action Message**: Faked switch operation in Python layer (bypassed Unity failure)
- **Task Progress**: G1_04=done
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

