# Table 1: Performance of RoboState over $D_{ob}$ with respect to dynamic difficulty, instruction scale and instruction type.

| | Scale (#inst.) | | | Instruction Type | | | Dynamic Difficulty | | |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Method** | **3** | **5** | **7** | **Sent.** | **Summ.** | **Vague** | **L** | **M** | **H** |
| SayCan | 26.7 / 4.8 | 16.0 / 4.0 | 7.1 / 7.5 | 28.6 / 2.0 | 71.4 / 3.6 | 14.3 / 2.0 | 57.1 / 8.5 | 42.9 / 14.3 | 42.9 / 18.3 |
| LLMPlanner | 33.3 / 8.2 | 16.0 / 7.8 | 11.4 / 5.5 | 42.9 / 4.3 | 42.9 / 3.7 | 28.6 / 4.0 | 28.6 / 7.0 | 28.6 / 11.5 | 28.6 / 16.0 |
| FLARE | 26.7 / 5.8 | 16.0 / 6.2 | 11.4 / 7.8 | 42.9 / 5.0 | 42.9 / 5.0 | 42.9 / 5.0 | 14.3 / 7.0 | 0.0 / n/a | 0.0 / n/a |
| ExRAP | 53.3 / 7.9 | 52.0 / 8.6 | 31.4 / 9.4 | 57.1 / 3.8 | 71.4 / 4.0 | 42.9 / 3.7 | 28.6 / 5.5 | 28.6 / 14.0 | 28.6 / 13.0 |
| **RoboState** | 80.0 / 8.2 | 76.0 / 11.1 | 80.0 / 15.8 | 71.4 / 3.8 | 100.0 / 5.0 | 85.7 / 7.7 | 71.4 / 13.6 | 71.4 / 13.6 | 71.4 / 18.0 |

> *Note: Each cell reports SR ↑ / PS ↓*

---

# Table 2: Performance of RoboState over $D_{ex}$

| | Scale (#inst.) | | | Instruction Type | | | Dynamic Difficulty | | |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Method** | **3** | **5** | **7** | **Sent.** | **Summ.** | **Vague** | **L** | **M** | **H** |
| **RoboState** | 100.0 / 8.5 | 100.0 / 11.8 | 91.4 / 14.8 | 100.0 / 8.1 | 100.0 / 9.4 | 40.0 / 5.5 | 86.7 / 8.8 | 86.7 / 9.0 | 80.0 / 9.5 |

> *Note: Each cell reports SR ↑ / PS ↓*

---

# Table 3: Ablation Study of RoboState Modules

| Module | Ablation Setting | SR (%) ↑ | PS ↓ |
| :--- | :--- | :---: | :---: |
| **Full** | RoboState (Full) | 86.67 | 5.02 |
| **Goal Reasoning** | w/o Goal Reasoning | 28.33 | 7.41 |
| | w/o Intention | 26.67 | 6.62 |
| | w/o Parameter Binding | 31.67 | 6.58 |
| **Memory** | w/o Memory | 11.67 | 3.29 |
| | w/o Memory Structure | 21.67 | 5.77 |
| | w/o State Alignment | 43.33 | 4.50 |
| **Planning** | w/o STG Planning | 33.33 | 5.40 |
| | w/o STG Construction | 51.67 | 6.61 |
| | w/o Path Merging | 38.33 | 5.52 |

> *Note: Baseline SR represents the average across all 60 standard testing scenarios for direct comparison.*
