# 🚀 VirtualHome Agent Episode Log


### [LLMPlannerVersion] Output
```json
{
  "version": "LLM-PLANNER-VH-OFFICIAL-HLP-v1.0-2026-07-16",
  "planner_core": "official OSU HLP prompt generator and kNN",
  "controller": "VirtualHome grounding and primitive executor",
  "knn_k": 9,
  "embedding_model": "paraphrase-MiniLM-L6-v2"
}
```

### [LLMPlannerHLP] Output
```json
{
  "official_hlp_file": "/Users/rushy/program/virtualhome/third_party/LLM-Planner/hlp/hlp_planner.py",
  "official_knn_file": "/Users/rushy/program/virtualhome/third_party/LLM-Planner/hlp/knn_set.pkl",
  "knn_k": 9,
  "embedding_model": "paraphrase-MiniLM-L6-v2",
  "visible_objects": [
    "book",
    "bookshelf",
    "box",
    "candle",
    "ceiling",
    "ceilinglamp",
    "coffeetable",
    "cupcake",
    "curtains",
    "doorjamb",
    "floor",
    "lightswitch",
    "orchid",
    "photoframe",
    "pillow",
    "plate",
    "powersocket",
    "rug",
    "sofa",
    "tv",
    "tvstand",
    "wall",
    "walllamp",
    "wallpictureframe",
    "wallshelf",
    "window"
  ],
  "completed_plans": [],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Move a spoon and cup from a table to the counter.\nCompleted plans: Navigation diningtable, PickupObject cup, Navigation countertop\nVisible objects are cup, countertop\nNext Plans: PutObject cup countertop\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject vase, CloseObject cabinet, Navigation box, PutObject vase box\nVisible objects are box, vase, diningtable\nNext Plans: PickupObject box, Navigation diningtable, PutObject box diningtable\n\nTask description: Move a laptop from a coffee table to an armchair.\nCompleted plans: \nVisible objects are armchair, laptop\nNext Plans: Navigation coffeetable, CloseObject laptop, PickupObject laptop, Navigation armchair, PutObject laptop armchair\n\nTask description: Place a box with the credit card on the blue sofa chair.\nCompleted plans: Navigation box, PickupObject box, Navigation armchair, PutObject box armchair\nVisible objects are box, creditcard, armchair\nNext Plans: Navigation coffeetable, PickupObject creditcard, Navigation box, PutObject creditcard box, CloseObject box\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop, PickupObject winebottle, Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle\nVisible objects are fridge, cabinet, winebottle\nNext Plans: CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Put a heated plate down in a corner cabinet. \nCompleted plans: Navigation fridge, OpenObject fridge, PickupObject plate, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject plate microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject plate, CloseObject microwave, Navigation cabinet, OpenObject cabinet\nVisible objects are plate, cabinet, microwave\nNext Plans: PutObject plate cabinet, CloseObject cabinet\n\nTask description: Put the chilled bowl on the counter\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject bowl, CloseObject cabinet, Navigation fridge, OpenObject fridge\nVisible objects are fridge, countertop, bowl\nNext Plans: PutObject bowl fridge, CloseObject fridge, OpenObject fridge, PickupObject bowl, CloseObject fridge, Navigation countertop, PutObject bowl countertop\n\nTask description: To turn on a lamp and pick up a pen. \nCompleted plans: Navigation desklamp\nVisible objects are \nNext Plans: ToggleObjectOn desklamp, PickupObject pen\n\nTask description: put the spoon and the plate into the door under the sink\nCompleted plans: Navigation sinkbasin, PickupObject ladle, Navigation bowl, PutObject ladle bowl, PickupObject bowl, Navigation cabinet, OpenObject cabinet\nVisible objects are cabinet, ladle, bowl\nNext Plans: PutObject bowl cabinet, CloseObject cabinet\n\nTask description: The mug should always be on the coffeetable.\nCompleted plans: \nVisible objects are book, bookshelf, box, candle, ceiling, ceilinglamp, coffeetable, cupcake, curtains, doorjamb, floor, lightswitch, orchid, photoframe, pillow, plate, powersocket, rug, sofa, tv, tvstand, wall, walllamp, wallpictureframe, wallshelf, window\nNext Plans:",
  "raw_output": "PickupObject spoon, Navigation countertop, PutObject spoon countertop",
  "parsed_plan": [
    [
      "PickupObject",
      "spoon"
    ],
    [
      "Navigation",
      "countertop"
    ],
    [
      "PutObject",
      "spoon",
      "countertop"
    ]
  ],
  "replan_count": 1,
  "reason": "initial planning"
}
```
## Step 0
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: E1_07=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [LLMPlannerHLP] Output
```json
{
  "official_hlp_file": "/Users/rushy/program/virtualhome/third_party/LLM-Planner/hlp/hlp_planner.py",
  "official_knn_file": "/Users/rushy/program/virtualhome/third_party/LLM-Planner/hlp/knn_set.pkl",
  "knn_k": 9,
  "embedding_model": "paraphrase-MiniLM-L6-v2",
  "visible_objects": [
    "book",
    "bookshelf",
    "box",
    "candle",
    "ceiling",
    "ceilinglamp",
    "coffeetable",
    "cupcake",
    "curtains",
    "doorjamb",
    "floor",
    "lightswitch",
    "orchid",
    "photoframe",
    "pillow",
    "plate",
    "powersocket",
    "rug",
    "sofa",
    "tv",
    "tvstand",
    "wall",
    "walllamp",
    "wallpictureframe",
    "wallshelf",
    "window"
  ],
  "completed_plans": [],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Move a spoon and cup from a table to the counter.\nCompleted plans: Navigation diningtable\nVisible objects are cup, countertop\nNext Plans: PickupObject cup, Navigation countertop, PutObject cup countertop\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet\nVisible objects are box, vase, diningtable\nNext Plans: OpenObject cabinet, PickupObject vase, CloseObject cabinet, Navigation box, PutObject vase box, PickupObject box, Navigation diningtable, PutObject box diningtable\n\nTask description: Move a laptop from a coffee table to an armchair.\nCompleted plans: Navigation coffeetable, CloseObject laptop\nVisible objects are armchair, laptop\nNext Plans: PickupObject laptop, Navigation armchair, PutObject laptop armchair\n\nTask description: Place a box with the credit card on the blue sofa chair.\nCompleted plans: Navigation box\nVisible objects are box, creditcard, armchair\nNext Plans: PickupObject box, Navigation armchair, PutObject box armchair, Navigation coffeetable, PickupObject creditcard, Navigation box, PutObject creditcard box, CloseObject box\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop, PickupObject winebottle, Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge\nVisible objects are fridge, cabinet, winebottle\nNext Plans: PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Put a heated plate down in a corner cabinet. \nCompleted plans: Navigation fridge, OpenObject fridge, PickupObject plate, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject plate microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject plate, CloseObject microwave, Navigation cabinet\nVisible objects are plate, cabinet, microwave\nNext Plans: OpenObject cabinet, PutObject plate cabinet, CloseObject cabinet\n\nTask description: Put the chilled bowl on the counter\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject bowl, CloseObject cabinet, Navigation fridge, OpenObject fridge, PutObject bowl fridge\nVisible objects are fridge, countertop, bowl\nNext Plans: CloseObject fridge, OpenObject fridge, PickupObject bowl, CloseObject fridge, Navigation countertop, PutObject bowl countertop\n\nTask description: To turn on a lamp and pick up a pen. \nCompleted plans: Navigation desklamp, ToggleObjectOn desklamp\nVisible objects are \nNext Plans: PickupObject pen\n\nTask description: put the spoon and the plate into the door under the sink\nCompleted plans: Navigation sinkbasin, PickupObject ladle, Navigation bowl, PutObject ladle bowl, PickupObject bowl, Navigation cabinet\nVisible objects are cabinet, ladle, bowl\nNext Plans: OpenObject cabinet, PutObject bowl cabinet, CloseObject cabinet\n\nTask description: The mug should always be on the coffeetable.\nCompleted plans: \nVisible objects are book, bookshelf, box, candle, ceiling, ceilinglamp, coffeetable, cupcake, curtains, doorjamb, floor, lightswitch, orchid, photoframe, pillow, plate, powersocket, rug, sofa, tv, tvstand, wall, walllamp, wallpictureframe, wallshelf, window\nNext Plans:",
  "raw_output": "Navigation coffeetable, PickupObject mug, PutObject mug coffeetable",
  "parsed_plan": [
    [
      "Navigation",
      "coffeetable"
    ],
    [
      "PickupObject",
      "mug"
    ],
    [
      "PutObject",
      "mug",
      "coffeetable"
    ]
  ],
  "replan_count": 2,
  "reason": "high-level skill failed: PickupObject spoon; reason: PickupObject target not found: spoon"
}
```
## Step 1
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: E1_07=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [LLMPlannerHLP] Output
```json
{
  "official_hlp_file": "/Users/rushy/program/virtualhome/third_party/LLM-Planner/hlp/hlp_planner.py",
  "official_knn_file": "/Users/rushy/program/virtualhome/third_party/LLM-Planner/hlp/knn_set.pkl",
  "knn_k": 9,
  "embedding_model": "paraphrase-MiniLM-L6-v2",
  "visible_objects": [
    "book",
    "bookshelf",
    "box",
    "candle",
    "ceiling",
    "ceilinglamp",
    "coffeetable",
    "cupcake",
    "curtains",
    "doorjamb",
    "floor",
    "lightswitch",
    "orchid",
    "photoframe",
    "pillow",
    "plate",
    "powersocket",
    "rug",
    "sofa",
    "tv",
    "tvstand",
    "wall",
    "walllamp",
    "wallpictureframe",
    "wallshelf",
    "window"
  ],
  "completed_plans": [
    [
      "Navigation",
      "coffeetable"
    ]
  ],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Move a spoon and cup from a table to the counter.\nCompleted plans: \nVisible objects are cup, countertop\nNext Plans: Navigation diningtable, PickupObject cup, Navigation countertop, PutObject cup countertop\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet\nVisible objects are box, vase, diningtable\nNext Plans: OpenObject cabinet, PickupObject vase, CloseObject cabinet, Navigation box, PutObject vase box, PickupObject box, Navigation diningtable, PutObject box diningtable\n\nTask description: Move a laptop from a coffee table to an armchair.\nCompleted plans: \nVisible objects are armchair, laptop\nNext Plans: Navigation coffeetable, CloseObject laptop, PickupObject laptop, Navigation armchair, PutObject laptop armchair\n\nTask description: Place a box with the credit card on the blue sofa chair.\nCompleted plans: Navigation box, PickupObject box, Navigation armchair, PutObject box armchair, Navigation coffeetable\nVisible objects are box, creditcard, armchair\nNext Plans: PickupObject creditcard, Navigation box, PutObject creditcard box, CloseObject box\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop, PickupObject winebottle\nVisible objects are fridge, cabinet, winebottle\nNext Plans: Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Put a heated plate down in a corner cabinet. \nCompleted plans: Navigation fridge, OpenObject fridge, PickupObject plate, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject plate microwave, CloseObject microwave, ToggleObjectOn microwave\nVisible objects are plate, cabinet, microwave\nNext Plans: ToggleObjectOff microwave, OpenObject microwave, PickupObject plate, CloseObject microwave, Navigation cabinet, OpenObject cabinet, PutObject plate cabinet, CloseObject cabinet\n\nTask description: Put the chilled bowl on the counter\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject bowl, CloseObject cabinet\nVisible objects are fridge, countertop, bowl\nNext Plans: Navigation fridge, OpenObject fridge, PutObject bowl fridge, CloseObject fridge, OpenObject fridge, PickupObject bowl, CloseObject fridge, Navigation countertop, PutObject bowl countertop\n\nTask description: To turn on a lamp and pick up a pen. \nCompleted plans: Navigation desklamp, ToggleObjectOn desklamp\nVisible objects are \nNext Plans: PickupObject pen\n\nTask description: put the spoon and the plate into the door under the sink\nCompleted plans: Navigation sinkbasin, PickupObject ladle, Navigation bowl\nVisible objects are cabinet, ladle, bowl\nNext Plans: PutObject ladle bowl, PickupObject bowl, Navigation cabinet, OpenObject cabinet, PutObject bowl cabinet, CloseObject cabinet\n\nTask description: The mug should always be on the coffeetable.\nCompleted plans: Navigation coffeetable\nVisible objects are book, bookshelf, box, candle, ceiling, ceilinglamp, coffeetable, cupcake, curtains, doorjamb, floor, lightswitch, orchid, photoframe, pillow, plate, powersocket, rug, sofa, tv, tvstand, wall, walllamp, wallpictureframe, wallshelf, window\nNext Plans:",
  "raw_output": "Navigation coffeetable, PickupObject mug, PutObject mug coffeetable",
  "parsed_plan": [
    [
      "Navigation",
      "coffeetable"
    ],
    [
      "PickupObject",
      "mug"
    ],
    [
      "PutObject",
      "mug",
      "coffeetable"
    ]
  ],
  "replan_count": 3,
  "reason": "high-level skill failed: PickupObject mug; reason: PickupObject target not found: mug"
}
```
## Step 2
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: E1_07=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [LLMPlannerHLP] Output
```json
{
  "official_hlp_file": "/Users/rushy/program/virtualhome/third_party/LLM-Planner/hlp/hlp_planner.py",
  "official_knn_file": "/Users/rushy/program/virtualhome/third_party/LLM-Planner/hlp/knn_set.pkl",
  "knn_k": 9,
  "embedding_model": "paraphrase-MiniLM-L6-v2",
  "visible_objects": [
    "book",
    "bookshelf",
    "box",
    "candle",
    "ceiling",
    "ceilinglamp",
    "coffeetable",
    "cupcake",
    "curtains",
    "doorjamb",
    "floor",
    "lightswitch",
    "orchid",
    "photoframe",
    "pillow",
    "plate",
    "powersocket",
    "rug",
    "sofa",
    "tv",
    "tvstand",
    "wall",
    "walllamp",
    "wallpictureframe",
    "wallshelf",
    "window"
  ],
  "completed_plans": [
    [
      "Navigation",
      "coffeetable"
    ],
    [
      "Navigation",
      "coffeetable"
    ]
  ],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Move a spoon and cup from a table to the counter.\nCompleted plans: Navigation diningtable\nVisible objects are cup, countertop\nNext Plans: PickupObject cup, Navigation countertop, PutObject cup countertop\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject vase, CloseObject cabinet, Navigation box, PutObject vase box, PickupObject box, Navigation diningtable\nVisible objects are box, vase, diningtable\nNext Plans: PutObject box diningtable\n\nTask description: Move a laptop from a coffee table to an armchair.\nCompleted plans: Navigation coffeetable\nVisible objects are armchair, laptop\nNext Plans: CloseObject laptop, PickupObject laptop, Navigation armchair, PutObject laptop armchair\n\nTask description: Place a box with the credit card on the blue sofa chair.\nCompleted plans: Navigation box, PickupObject box, Navigation armchair, PutObject box armchair, Navigation coffeetable\nVisible objects are box, creditcard, armchair\nNext Plans: PickupObject creditcard, Navigation box, PutObject creditcard box, CloseObject box\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop, PickupObject winebottle, Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge\nVisible objects are fridge, cabinet, winebottle\nNext Plans: Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Put a heated plate down in a corner cabinet. \nCompleted plans: Navigation fridge, OpenObject fridge, PickupObject plate, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject plate microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject plate, CloseObject microwave, Navigation cabinet, OpenObject cabinet\nVisible objects are plate, cabinet, microwave\nNext Plans: PutObject plate cabinet, CloseObject cabinet\n\nTask description: Put the chilled bowl on the counter\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject bowl, CloseObject cabinet, Navigation fridge, OpenObject fridge, PutObject bowl fridge, CloseObject fridge, OpenObject fridge, PickupObject bowl\nVisible objects are fridge, countertop, bowl\nNext Plans: CloseObject fridge, Navigation countertop, PutObject bowl countertop\n\nTask description: To turn on a lamp and pick up a pen. \nCompleted plans: Navigation desklamp, ToggleObjectOn desklamp\nVisible objects are \nNext Plans: PickupObject pen\n\nTask description: put the spoon and the plate into the door under the sink\nCompleted plans: Navigation sinkbasin\nVisible objects are cabinet, ladle, bowl\nNext Plans: PickupObject ladle, Navigation bowl, PutObject ladle bowl, PickupObject bowl, Navigation cabinet, OpenObject cabinet, PutObject bowl cabinet, CloseObject cabinet\n\nTask description: The mug should always be on the coffeetable.\nCompleted plans: Navigation coffeetable, Navigation coffeetable\nVisible objects are book, bookshelf, box, candle, ceiling, ceilinglamp, coffeetable, cupcake, curtains, doorjamb, floor, lightswitch, orchid, photoframe, pillow, plate, powersocket, rug, sofa, tv, tvstand, wall, walllamp, wallpictureframe, wallshelf, window\nNext Plans:",
  "raw_output": "PickupObject cup, Navigation countertop, PutObject cup countertop",
  "parsed_plan": [
    [
      "PickupObject",
      "cup"
    ],
    [
      "Navigation",
      "countertop"
    ],
    [
      "PutObject",
      "cup",
      "countertop"
    ]
  ],
  "replan_count": 4,
  "reason": "high-level skill failed: PickupObject mug; reason: PickupObject target not found: mug"
}
```
## Step 3
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: E1_07=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 4
- **Action**: `[grab] <cupcake> (225)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: E1_07=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [LLMPlannerHLP] Output
```json
{
  "official_hlp_file": "/Users/rushy/program/virtualhome/third_party/LLM-Planner/hlp/hlp_planner.py",
  "official_knn_file": "/Users/rushy/program/virtualhome/third_party/LLM-Planner/hlp/knn_set.pkl",
  "knn_k": 9,
  "embedding_model": "paraphrase-MiniLM-L6-v2",
  "visible_objects": [
    "book",
    "bookshelf",
    "box",
    "candle",
    "ceiling",
    "ceilinglamp",
    "coffeetable",
    "cupcake",
    "curtains",
    "doorjamb",
    "floor",
    "lightswitch",
    "orchid",
    "photoframe",
    "pillow",
    "plate",
    "powersocket",
    "rug",
    "sofa",
    "tv",
    "tvstand",
    "wall",
    "walllamp",
    "wallpictureframe",
    "wallshelf",
    "window"
  ],
  "completed_plans": [
    [
      "Navigation",
      "coffeetable"
    ],
    [
      "Navigation",
      "coffeetable"
    ]
  ],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Move a spoon and cup from a table to the counter.\nCompleted plans: Navigation diningtable\nVisible objects are cup, countertop\nNext Plans: PickupObject cup, Navigation countertop, PutObject cup countertop\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject vase, CloseObject cabinet\nVisible objects are box, vase, diningtable\nNext Plans: Navigation box, PutObject vase box, PickupObject box, Navigation diningtable, PutObject box diningtable\n\nTask description: Move a laptop from a coffee table to an armchair.\nCompleted plans: \nVisible objects are armchair, laptop\nNext Plans: Navigation coffeetable, CloseObject laptop, PickupObject laptop, Navigation armchair, PutObject laptop armchair\n\nTask description: Place a box with the credit card on the blue sofa chair.\nCompleted plans: Navigation box, PickupObject box, Navigation armchair, PutObject box armchair, Navigation coffeetable, PickupObject creditcard\nVisible objects are box, creditcard, armchair\nNext Plans: Navigation box, PutObject creditcard box, CloseObject box\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop, PickupObject winebottle, Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge\nVisible objects are fridge, cabinet, winebottle\nNext Plans: PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Put a heated plate down in a corner cabinet. \nCompleted plans: Navigation fridge, OpenObject fridge, PickupObject plate, CloseObject fridge\nVisible objects are plate, cabinet, microwave\nNext Plans: Navigation microwave, OpenObject microwave, PutObject plate microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject plate, CloseObject microwave, Navigation cabinet, OpenObject cabinet, PutObject plate cabinet, CloseObject cabinet\n\nTask description: Put the chilled bowl on the counter\nCompleted plans: Navigation cabinet\nVisible objects are fridge, countertop, bowl\nNext Plans: OpenObject cabinet, PickupObject bowl, CloseObject cabinet, Navigation fridge, OpenObject fridge, PutObject bowl fridge, CloseObject fridge, OpenObject fridge, PickupObject bowl, CloseObject fridge, Navigation countertop, PutObject bowl countertop\n\nTask description: To turn on a lamp and pick up a pen. \nCompleted plans: \nVisible objects are \nNext Plans: Navigation desklamp, ToggleObjectOn desklamp, PickupObject pen\n\nTask description: put the spoon and the plate into the door under the sink\nCompleted plans: \nVisible objects are cabinet, ladle, bowl\nNext Plans: Navigation sinkbasin, PickupObject ladle, Navigation bowl, PutObject ladle bowl, PickupObject bowl, Navigation cabinet, OpenObject cabinet, PutObject bowl cabinet, CloseObject cabinet\n\nTask description: The mug should always be on the coffeetable.\nCompleted plans: Navigation coffeetable, Navigation coffeetable\nVisible objects are book, bookshelf, box, candle, ceiling, ceilinglamp, coffeetable, cupcake, curtains, doorjamb, floor, lightswitch, orchid, photoframe, pillow, plate, powersocket, rug, sofa, tv, tvstand, wall, walllamp, wallpictureframe, wallshelf, window\nNext Plans:",
  "raw_output": "PickupObject spoon, Navigation countertop, PutObject spoon countertop, PickupObject cup, Navigation countertop, PutObject cup countertop",
  "parsed_plan": [
    [
      "PickupObject",
      "spoon"
    ],
    [
      "Navigation",
      "countertop"
    ],
    [
      "PutObject",
      "spoon",
      "countertop"
    ],
    [
      "PickupObject",
      "cup"
    ],
    [
      "Navigation",
      "countertop"
    ],
    [
      "PutObject",
      "cup",
      "countertop"
    ]
  ],
  "replan_count": 5,
  "reason": "high-level skill failed: Navigation countertop; reason: Navigation target not found: countertop"
}
```
## Step 5
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: E1_07=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [LLMPlannerHLP] Output
```json
{
  "official_hlp_file": "/Users/rushy/program/virtualhome/third_party/LLM-Planner/hlp/hlp_planner.py",
  "official_knn_file": "/Users/rushy/program/virtualhome/third_party/LLM-Planner/hlp/knn_set.pkl",
  "knn_k": 9,
  "embedding_model": "paraphrase-MiniLM-L6-v2",
  "visible_objects": [
    "book",
    "bookshelf",
    "box",
    "candle",
    "ceiling",
    "ceilinglamp",
    "coffeetable",
    "cupcake",
    "curtains",
    "doorjamb",
    "floor",
    "lightswitch",
    "orchid",
    "photoframe",
    "pillow",
    "plate",
    "powersocket",
    "rug",
    "sofa",
    "tv",
    "tvstand",
    "wall",
    "walllamp",
    "wallpictureframe",
    "wallshelf",
    "window"
  ],
  "completed_plans": [
    [
      "Navigation",
      "coffeetable"
    ],
    [
      "Navigation",
      "coffeetable"
    ]
  ],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Move a spoon and cup from a table to the counter.\nCompleted plans: Navigation diningtable, PickupObject cup\nVisible objects are cup, countertop\nNext Plans: Navigation countertop, PutObject cup countertop\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject vase, CloseObject cabinet, Navigation box\nVisible objects are box, vase, diningtable\nNext Plans: PutObject vase box, PickupObject box, Navigation diningtable, PutObject box diningtable\n\nTask description: Move a laptop from a coffee table to an armchair.\nCompleted plans: Navigation coffeetable, CloseObject laptop, PickupObject laptop, Navigation armchair\nVisible objects are armchair, laptop\nNext Plans: PutObject laptop armchair\n\nTask description: Place a box with the credit card on the blue sofa chair.\nCompleted plans: \nVisible objects are box, creditcard, armchair\nNext Plans: Navigation box, PickupObject box, Navigation armchair, PutObject box armchair, Navigation coffeetable, PickupObject creditcard, Navigation box, PutObject creditcard box, CloseObject box\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop, PickupObject winebottle, Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge\nVisible objects are fridge, cabinet, winebottle\nNext Plans: PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Put a heated plate down in a corner cabinet. \nCompleted plans: Navigation fridge, OpenObject fridge, PickupObject plate, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject plate microwave\nVisible objects are plate, cabinet, microwave\nNext Plans: CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject plate, CloseObject microwave, Navigation cabinet, OpenObject cabinet, PutObject plate cabinet, CloseObject cabinet\n\nTask description: Put the chilled bowl on the counter\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject bowl, CloseObject cabinet, Navigation fridge, OpenObject fridge, PutObject bowl fridge, CloseObject fridge, OpenObject fridge, PickupObject bowl\nVisible objects are fridge, countertop, bowl\nNext Plans: CloseObject fridge, Navigation countertop, PutObject bowl countertop\n\nTask description: To turn on a lamp and pick up a pen. \nCompleted plans: \nVisible objects are \nNext Plans: Navigation desklamp, ToggleObjectOn desklamp, PickupObject pen\n\nTask description: put the spoon and the plate into the door under the sink\nCompleted plans: Navigation sinkbasin, PickupObject ladle\nVisible objects are cabinet, ladle, bowl\nNext Plans: Navigation bowl, PutObject ladle bowl, PickupObject bowl, Navigation cabinet, OpenObject cabinet, PutObject bowl cabinet, CloseObject cabinet\n\nTask description: The mug should always be on the coffeetable.\nCompleted plans: Navigation coffeetable, Navigation coffeetable\nVisible objects are book, bookshelf, box, candle, ceiling, ceilinglamp, coffeetable, cupcake, curtains, doorjamb, floor, lightswitch, orchid, photoframe, pillow, plate, powersocket, rug, sofa, tv, tvstand, wall, walllamp, wallpictureframe, wallshelf, window\nNext Plans:",
  "raw_output": "PickupObject spoon, Navigation countertop, PutObject spoon countertop",
  "parsed_plan": [
    [
      "PickupObject",
      "spoon"
    ],
    [
      "Navigation",
      "countertop"
    ],
    [
      "PutObject",
      "spoon",
      "countertop"
    ]
  ],
  "replan_count": 6,
  "reason": "high-level skill failed: PickupObject spoon; reason: PickupObject target not found: spoon"
}
```
## Step 6
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: E1_07=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [LLMPlannerHLP] Output
```json
{
  "official_hlp_file": "/Users/rushy/program/virtualhome/third_party/LLM-Planner/hlp/hlp_planner.py",
  "official_knn_file": "/Users/rushy/program/virtualhome/third_party/LLM-Planner/hlp/knn_set.pkl",
  "knn_k": 9,
  "embedding_model": "paraphrase-MiniLM-L6-v2",
  "visible_objects": [
    "book",
    "bookshelf",
    "box",
    "candle",
    "ceiling",
    "ceilinglamp",
    "coffeetable",
    "cupcake",
    "curtains",
    "doorjamb",
    "floor",
    "lightswitch",
    "orchid",
    "photoframe",
    "pillow",
    "plate",
    "powersocket",
    "rug",
    "sofa",
    "tv",
    "tvstand",
    "wall",
    "walllamp",
    "wallpictureframe",
    "wallshelf",
    "window"
  ],
  "completed_plans": [
    [
      "Navigation",
      "coffeetable"
    ],
    [
      "Navigation",
      "coffeetable"
    ]
  ],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Move a spoon and cup from a table to the counter.\nCompleted plans: \nVisible objects are cup, countertop\nNext Plans: Navigation diningtable, PickupObject cup, Navigation countertop, PutObject cup countertop\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject vase, CloseObject cabinet, Navigation box, PutObject vase box, PickupObject box\nVisible objects are box, vase, diningtable\nNext Plans: Navigation diningtable, PutObject box diningtable\n\nTask description: Move a laptop from a coffee table to an armchair.\nCompleted plans: Navigation coffeetable, CloseObject laptop\nVisible objects are armchair, laptop\nNext Plans: PickupObject laptop, Navigation armchair, PutObject laptop armchair\n\nTask description: Place a box with the credit card on the blue sofa chair.\nCompleted plans: \nVisible objects are box, creditcard, armchair\nNext Plans: Navigation box, PickupObject box, Navigation armchair, PutObject box armchair, Navigation coffeetable, PickupObject creditcard, Navigation box, PutObject creditcard box, CloseObject box\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: \nVisible objects are fridge, cabinet, winebottle\nNext Plans: Navigation countertop, PickupObject winebottle, Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Put a heated plate down in a corner cabinet. \nCompleted plans: Navigation fridge, OpenObject fridge, PickupObject plate, CloseObject fridge\nVisible objects are plate, cabinet, microwave\nNext Plans: Navigation microwave, OpenObject microwave, PutObject plate microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject plate, CloseObject microwave, Navigation cabinet, OpenObject cabinet, PutObject plate cabinet, CloseObject cabinet\n\nTask description: Put the chilled bowl on the counter\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject bowl, CloseObject cabinet, Navigation fridge, OpenObject fridge, PutObject bowl fridge, CloseObject fridge, OpenObject fridge, PickupObject bowl\nVisible objects are fridge, countertop, bowl\nNext Plans: CloseObject fridge, Navigation countertop, PutObject bowl countertop\n\nTask description: To turn on a lamp and pick up a pen. \nCompleted plans: Navigation desklamp, ToggleObjectOn desklamp\nVisible objects are \nNext Plans: PickupObject pen\n\nTask description: put the spoon and the plate into the door under the sink\nCompleted plans: Navigation sinkbasin, PickupObject ladle, Navigation bowl, PutObject ladle bowl, PickupObject bowl, Navigation cabinet, OpenObject cabinet\nVisible objects are cabinet, ladle, bowl\nNext Plans: PutObject bowl cabinet, CloseObject cabinet\n\nTask description: The mug should always be on the coffeetable.\nCompleted plans: Navigation coffeetable, Navigation coffeetable\nVisible objects are book, bookshelf, box, candle, ceiling, ceilinglamp, coffeetable, cupcake, curtains, doorjamb, floor, lightswitch, orchid, photoframe, pillow, plate, powersocket, rug, sofa, tv, tvstand, wall, walllamp, wallpictureframe, wallshelf, window\nNext Plans:",
  "raw_output": "PickupObject spoon, Navigation countertop, PutObject spoon countertop",
  "parsed_plan": [
    [
      "PickupObject",
      "spoon"
    ],
    [
      "Navigation",
      "countertop"
    ],
    [
      "PutObject",
      "spoon",
      "countertop"
    ]
  ],
  "replan_count": 7,
  "reason": "high-level skill failed: PickupObject spoon; reason: PickupObject target not found: spoon"
}
```
## Step 7
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: E1_07=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [LLMPlannerHLP] Output
```json
{
  "official_hlp_file": "/Users/rushy/program/virtualhome/third_party/LLM-Planner/hlp/hlp_planner.py",
  "official_knn_file": "/Users/rushy/program/virtualhome/third_party/LLM-Planner/hlp/knn_set.pkl",
  "knn_k": 9,
  "embedding_model": "paraphrase-MiniLM-L6-v2",
  "visible_objects": [
    "book",
    "bookshelf",
    "box",
    "candle",
    "ceiling",
    "ceilinglamp",
    "coffeetable",
    "cupcake",
    "curtains",
    "doorjamb",
    "floor",
    "lightswitch",
    "orchid",
    "photoframe",
    "pillow",
    "plate",
    "powersocket",
    "rug",
    "sofa",
    "tv",
    "tvstand",
    "wall",
    "walllamp",
    "wallpictureframe",
    "wallshelf",
    "window"
  ],
  "completed_plans": [
    [
      "Navigation",
      "coffeetable"
    ],
    [
      "Navigation",
      "coffeetable"
    ]
  ],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Move a spoon and cup from a table to the counter.\nCompleted plans: Navigation diningtable, PickupObject cup\nVisible objects are cup, countertop\nNext Plans: Navigation countertop, PutObject cup countertop\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet, OpenObject cabinet\nVisible objects are box, vase, diningtable\nNext Plans: PickupObject vase, CloseObject cabinet, Navigation box, PutObject vase box, PickupObject box, Navigation diningtable, PutObject box diningtable\n\nTask description: Move a laptop from a coffee table to an armchair.\nCompleted plans: Navigation coffeetable, CloseObject laptop, PickupObject laptop\nVisible objects are armchair, laptop\nNext Plans: Navigation armchair, PutObject laptop armchair\n\nTask description: Place a box with the credit card on the blue sofa chair.\nCompleted plans: \nVisible objects are box, creditcard, armchair\nNext Plans: Navigation box, PickupObject box, Navigation armchair, PutObject box armchair, Navigation coffeetable, PickupObject creditcard, Navigation box, PutObject creditcard box, CloseObject box\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop\nVisible objects are fridge, cabinet, winebottle\nNext Plans: PickupObject winebottle, Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Put a heated plate down in a corner cabinet. \nCompleted plans: Navigation fridge, OpenObject fridge, PickupObject plate\nVisible objects are plate, cabinet, microwave\nNext Plans: CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject plate microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject plate, CloseObject microwave, Navigation cabinet, OpenObject cabinet, PutObject plate cabinet, CloseObject cabinet\n\nTask description: Put the chilled bowl on the counter\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject bowl, CloseObject cabinet, Navigation fridge\nVisible objects are fridge, countertop, bowl\nNext Plans: OpenObject fridge, PutObject bowl fridge, CloseObject fridge, OpenObject fridge, PickupObject bowl, CloseObject fridge, Navigation countertop, PutObject bowl countertop\n\nTask description: To turn on a lamp and pick up a pen. \nCompleted plans: Navigation desklamp, ToggleObjectOn desklamp\nVisible objects are \nNext Plans: PickupObject pen\n\nTask description: put the spoon and the plate into the door under the sink\nCompleted plans: \nVisible objects are cabinet, ladle, bowl\nNext Plans: Navigation sinkbasin, PickupObject ladle, Navigation bowl, PutObject ladle bowl, PickupObject bowl, Navigation cabinet, OpenObject cabinet, PutObject bowl cabinet, CloseObject cabinet\n\nTask description: The mug should always be on the coffeetable.\nCompleted plans: Navigation coffeetable, Navigation coffeetable\nVisible objects are book, bookshelf, box, candle, ceiling, ceilinglamp, coffeetable, cupcake, curtains, doorjamb, floor, lightswitch, orchid, photoframe, pillow, plate, powersocket, rug, sofa, tv, tvstand, wall, walllamp, wallpictureframe, wallshelf, window\nNext Plans:",
  "raw_output": "PickupObject spoon, Navigation countertop, PutObject spoon countertop",
  "parsed_plan": [
    [
      "PickupObject",
      "spoon"
    ],
    [
      "Navigation",
      "countertop"
    ],
    [
      "PutObject",
      "spoon",
      "countertop"
    ]
  ],
  "replan_count": 8,
  "reason": "high-level skill failed: PickupObject spoon; reason: PickupObject target not found: spoon"
}
```
## Step 8
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: E1_07=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 


### [LLMPlannerHLP] Output
```json
{
  "official_hlp_file": "/Users/rushy/program/virtualhome/third_party/LLM-Planner/hlp/hlp_planner.py",
  "official_knn_file": "/Users/rushy/program/virtualhome/third_party/LLM-Planner/hlp/knn_set.pkl",
  "knn_k": 9,
  "embedding_model": "paraphrase-MiniLM-L6-v2",
  "visible_objects": [
    "book",
    "bookshelf",
    "box",
    "candle",
    "ceiling",
    "ceilinglamp",
    "coffeetable",
    "cupcake",
    "curtains",
    "doorjamb",
    "floor",
    "lightswitch",
    "orchid",
    "photoframe",
    "pillow",
    "plate",
    "powersocket",
    "rug",
    "sofa",
    "tv",
    "tvstand",
    "wall",
    "walllamp",
    "wallpictureframe",
    "wallshelf",
    "window"
  ],
  "completed_plans": [
    [
      "Navigation",
      "coffeetable"
    ],
    [
      "Navigation",
      "coffeetable"
    ]
  ],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Move a spoon and cup from a table to the counter.\nCompleted plans: Navigation diningtable\nVisible objects are cup, countertop\nNext Plans: PickupObject cup, Navigation countertop, PutObject cup countertop\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject vase, CloseObject cabinet, Navigation box\nVisible objects are box, vase, diningtable\nNext Plans: PutObject vase box, PickupObject box, Navigation diningtable, PutObject box diningtable\n\nTask description: Move a laptop from a coffee table to an armchair.\nCompleted plans: Navigation coffeetable, CloseObject laptop, PickupObject laptop\nVisible objects are armchair, laptop\nNext Plans: Navigation armchair, PutObject laptop armchair\n\nTask description: Place a box with the credit card on the blue sofa chair.\nCompleted plans: Navigation box, PickupObject box\nVisible objects are box, creditcard, armchair\nNext Plans: Navigation armchair, PutObject box armchair, Navigation coffeetable, PickupObject creditcard, Navigation box, PutObject creditcard box, CloseObject box\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop, PickupObject winebottle, Navigation fridge\nVisible objects are fridge, cabinet, winebottle\nNext Plans: OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Put a heated plate down in a corner cabinet. \nCompleted plans: Navigation fridge\nVisible objects are plate, cabinet, microwave\nNext Plans: OpenObject fridge, PickupObject plate, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject plate microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject plate, CloseObject microwave, Navigation cabinet, OpenObject cabinet, PutObject plate cabinet, CloseObject cabinet\n\nTask description: Put the chilled bowl on the counter\nCompleted plans: Navigation cabinet\nVisible objects are fridge, countertop, bowl\nNext Plans: OpenObject cabinet, PickupObject bowl, CloseObject cabinet, Navigation fridge, OpenObject fridge, PutObject bowl fridge, CloseObject fridge, OpenObject fridge, PickupObject bowl, CloseObject fridge, Navigation countertop, PutObject bowl countertop\n\nTask description: To turn on a lamp and pick up a pen. \nCompleted plans: \nVisible objects are \nNext Plans: Navigation desklamp, ToggleObjectOn desklamp, PickupObject pen\n\nTask description: put the spoon and the plate into the door under the sink\nCompleted plans: Navigation sinkbasin, PickupObject ladle, Navigation bowl\nVisible objects are cabinet, ladle, bowl\nNext Plans: PutObject ladle bowl, PickupObject bowl, Navigation cabinet, OpenObject cabinet, PutObject bowl cabinet, CloseObject cabinet\n\nTask description: The mug should always be on the coffeetable.\nCompleted plans: Navigation coffeetable, Navigation coffeetable\nVisible objects are book, bookshelf, box, candle, ceiling, ceilinglamp, coffeetable, cupcake, curtains, doorjamb, floor, lightswitch, orchid, photoframe, pillow, plate, powersocket, rug, sofa, tv, tvstand, wall, walllamp, wallpictureframe, wallshelf, window\nNext Plans:",
  "raw_output": "Navigation countert op, PickupObject cup, Navigation countertop, PutObject cup countertop",
  "parsed_plan": [
    [
      "Navigation",
      "countert"
    ],
    [
      "PickupObject",
      "cup"
    ],
    [
      "Navigation",
      "countertop"
    ],
    [
      "PutObject",
      "cup",
      "countertop"
    ]
  ],
  "replan_count": 9,
  "reason": "high-level skill failed: PickupObject spoon; reason: PickupObject target not found: spoon"
}
```
