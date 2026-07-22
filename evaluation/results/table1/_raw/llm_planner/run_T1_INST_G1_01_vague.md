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
    "bananas",
    "bench",
    "bookshelf",
    "candle",
    "ceiling",
    "ceilinglamp",
    "chair",
    "coffeemaker",
    "condimentbottle",
    "condimentshaker",
    "cookingpot",
    "curtains",
    "cutleryfork",
    "cutleryknife",
    "cutlets",
    "dishbowl",
    "dishwasher",
    "door",
    "doorjamb",
    "faucet",
    "floor",
    "fridge",
    "fryingpan",
    "juice",
    "kitchencabinet",
    "kitchencounter",
    "kitchencounterdrawer",
    "kitchentable",
    "knifeblock",
    "lightswitch",
    "microwave",
    "milk",
    "mincedmeat",
    "orchid",
    "plate",
    "powersocket",
    "rug",
    "salmon",
    "sink",
    "stove",
    "stovefan",
    "toaster",
    "tvstand",
    "wall",
    "walllamp",
    "wallphone",
    "wallpictureframe",
    "waterglass",
    "window"
  ],
  "completed_plans": [],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put the chilled bowl on the counter\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject bowl, CloseObject cabinet, Navigation fridge, OpenObject fridge\nVisible objects are fridge, countertop, bowl\nNext Plans: PutObject bowl fridge, CloseObject fridge, OpenObject fridge, PickupObject bowl, CloseObject fridge, Navigation countertop, PutObject bowl countertop\n\nTask description: Put a heated potato slice in the fridge.\nCompleted plans: Navigation diningtable, PickupObject knife, Navigation potato, SliceObject potato, Navigation microwave, OpenObject microwave, PutObject knife microwave, CloseObject microwave, Navigation diningtable, PickupObject potatosliced, Navigation microwave, OpenObject microwave, PutObject potatosliced microwave\nVisible objects are fridge, microwave, knife, potatosliced\nNext Plans: CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject potatosliced, CloseObject microwave, Navigation fridge, OpenObject fridge, PutObject potatosliced fridge, CloseObject fridge\n\nTask description: Put a heated plate down in a corner cabinet. \nCompleted plans: Navigation fridge\nVisible objects are plate, cabinet, microwave\nNext Plans: OpenObject fridge, PickupObject plate, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject plate microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject plate, CloseObject microwave, Navigation cabinet, OpenObject cabinet, PutObject plate cabinet, CloseObject cabinet\n\nTask description: Heat up a slice of tomato in the microwave to put in the fridge.\nCompleted plans: Navigation diningtable, PickupObject knife, Navigation tomato, OpenObject fridge, SliceObject tomato, CloseObject fridge, Navigation fridge, OpenObject fridge\nVisible objects are tomatosliced, knife, microwave, fridge\nNext Plans: PutObject knife fridge, CloseObject fridge, Navigation fridge, OpenObject fridge, PickupObject tomatosliced, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject tomatosliced microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject tomatosliced, CloseObject microwave, Navigation fridge, OpenObject fridge, PutObject tomatosliced fridge, CloseObject fridge\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop, PickupObject winebottle, Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle\nVisible objects are fridge, cabinet, winebottle\nNext Plans: CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Place cold bread on the counter.\nCompleted plans: Navigation sinkbasin, PickupObject butterknife, Navigation bread, SliceObject bread, Navigation fridge, OpenObject fridge, PutObject butterknife fridge, CloseObject fridge, Navigation countertop, PickupObject breadsliced, Navigation fridge, OpenObject fridge, PutObject breadsliced fridge, CloseObject fridge, OpenObject fridge\nVisible objects are fridge, breadsliced, countertop, butterknife\nNext Plans: PickupObject breadsliced, CloseObject fridge, Navigation countertop, PutObject breadsliced countertop\n\nTask description: put a cooled potato slice inside of the microwave\nCompleted plans: Navigation countertop, PickupObject knife, Navigation potato, OpenObject microwave, SliceObject potato, CloseObject microwave, Navigation microwave, OpenObject microwave, PutObject knife microwave, CloseObject microwave, Navigation microwave, OpenObject microwave\nVisible objects are fridge, microwave, knife, potatosliced\nNext Plans: PickupObject potatosliced, CloseObject microwave, Navigation fridge, OpenObject fridge, PutObject potatosliced fridge, CloseObject fridge, OpenObject fridge, PickupObject potatosliced, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject potatosliced microwave, CloseObject microwave\n\nTask description: Put a slice of bread in the fridge.\nCompleted plans: Navigation sinkbasin, PickupObject knife, SliceObject bread, PutObject knife sink, PickupObject breadsliced, Navigation fridge, OpenObject fridge, PutObject breadsliced fridge, CloseObject fridge\nVisible objects are sink, fridge, breadsliced, butterknife, knife\nNext Plans: Navigation countertop, PickupObject butterknife, Navigation bread, SliceObject bread, Navigation fridge, OpenObject fridge, PutObject butterknife fridge, CloseObject fridge, Navigation countertop, PickupObject breadsliced, Navigation fridge, OpenObject fridge, PutObject breadsliced fridge, CloseObject fridge\n\nTask description: Put a chilled tomato slice into the microwave.\nCompleted plans: Navigation countertop, PickupObject tomato, Navigation countertop, PutObject tomato countertop, PickupObject butterknife, SliceObject tomato, PutObject butterknife countertop, PickupObject tomatosliced, Navigation fridge, OpenObject fridge, PutObject tomatosliced fridge, CloseObject fridge, OpenObject fridge, PickupObject tomatosliced, CloseObject fridge\nVisible objects are fridge, microwave, tomatosliced, butterknife, tomato, countertop\nNext Plans: Navigation microwave, OpenObject microwave, PutObject tomatosliced microwave, CloseObject microwave\n\nTask description: If the chilled dairy drink is in cold storage, heat one cup of it in the food-heating appliance.\nCompleted plans: \nVisible objects are bananas, bench, bookshelf, candle, ceiling, ceilinglamp, chair, coffeemaker, condimentbottle, condimentshaker, cookingpot, curtains, cutleryfork, cutleryknife, cutlets, dishbowl, dishwasher, door, doorjamb, faucet, floor, fridge, fryingpan, juice, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, knifeblock, lightswitch, microwave, milk, mincedmeat, orchid, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tvstand, wall, walllamp, wallphone, wallpictureframe, waterglass, window\nNext Plans:",
  "raw_output": "Navigation fridge, OpenObject fridge, PickupObject milk, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject milk microwave, CloseObject microwave",
  "parsed_plan": [
    [
      "Navigation",
      "fridge"
    ],
    [
      "OpenObject",
      "fridge"
    ],
    [
      "PickupObject",
      "milk"
    ],
    [
      "CloseObject",
      "fridge"
    ],
    [
      "Navigation",
      "microwave"
    ],
    [
      "OpenObject",
      "microwave"
    ],
    [
      "PutObject",
      "milk",
      "microwave"
    ],
    [
      "CloseObject",
      "microwave"
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
- **Task Progress**: G1_01=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 1
- **Action**: `[walk] <fridge> (162)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_01=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 2
- **Action**: `[open] <fridge> (162)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_01=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 3
- **Action**: `[grab] <milk> (176)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_01=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 4
- **Action**: `[close] <fridge> (162)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_01=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 5
- **Action**: `[walk] <microwave> (171)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_01=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 6
- **Action**: `[open] <microwave> (171)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_01=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 7
- **Action**: `[putin] <milk> (176) <microwave> (171)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_01=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 8
- **Action**: `[close] <microwave> (171)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_01=pending
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
    "bananas",
    "bench",
    "bookshelf",
    "candle",
    "ceiling",
    "ceilinglamp",
    "chair",
    "coffeemaker",
    "condimentbottle",
    "condimentshaker",
    "cookingpot",
    "curtains",
    "cutleryfork",
    "cutleryknife",
    "cutlets",
    "dishbowl",
    "dishwasher",
    "door",
    "doorjamb",
    "faucet",
    "floor",
    "fridge",
    "fryingpan",
    "juice",
    "kitchencabinet",
    "kitchencounter",
    "kitchencounterdrawer",
    "kitchentable",
    "knifeblock",
    "lightswitch",
    "microwave",
    "milk",
    "mincedmeat",
    "orchid",
    "plate",
    "powersocket",
    "rug",
    "salmon",
    "sink",
    "stove",
    "stovefan",
    "toaster",
    "tvstand",
    "wall",
    "walllamp",
    "wallphone",
    "wallpictureframe",
    "waterglass",
    "window"
  ],
  "completed_plans": [],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put the chilled bowl on the counter\nCompleted plans: Navigation cabinet, OpenObject cabinet\nVisible objects are fridge, countertop, bowl\nNext Plans: PickupObject bowl, CloseObject cabinet, Navigation fridge, OpenObject fridge, PutObject bowl fridge, CloseObject fridge, OpenObject fridge, PickupObject bowl, CloseObject fridge, Navigation countertop, PutObject bowl countertop\n\nTask description: Put a heated potato slice in the fridge.\nCompleted plans: Navigation diningtable, PickupObject knife, Navigation potato, SliceObject potato, Navigation microwave, OpenObject microwave, PutObject knife microwave, CloseObject microwave, Navigation diningtable, PickupObject potatosliced, Navigation microwave, OpenObject microwave, PutObject potatosliced microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject potatosliced\nVisible objects are fridge, microwave, knife, potatosliced\nNext Plans: CloseObject microwave, Navigation fridge, OpenObject fridge, PutObject potatosliced fridge, CloseObject fridge\n\nTask description: Put a heated plate down in a corner cabinet. \nCompleted plans: Navigation fridge, OpenObject fridge\nVisible objects are plate, cabinet, microwave\nNext Plans: PickupObject plate, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject plate microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject plate, CloseObject microwave, Navigation cabinet, OpenObject cabinet, PutObject plate cabinet, CloseObject cabinet\n\nTask description: Heat up a slice of tomato in the microwave to put in the fridge.\nCompleted plans: Navigation diningtable, PickupObject knife, Navigation tomato, OpenObject fridge, SliceObject tomato, CloseObject fridge, Navigation fridge, OpenObject fridge\nVisible objects are tomatosliced, knife, microwave, fridge\nNext Plans: PutObject knife fridge, CloseObject fridge, Navigation fridge, OpenObject fridge, PickupObject tomatosliced, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject tomatosliced microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject tomatosliced, CloseObject microwave, Navigation fridge, OpenObject fridge, PutObject tomatosliced fridge, CloseObject fridge\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop\nVisible objects are fridge, cabinet, winebottle\nNext Plans: PickupObject winebottle, Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Place cold bread on the counter.\nCompleted plans: Navigation sinkbasin, PickupObject butterknife, Navigation bread, SliceObject bread, Navigation fridge, OpenObject fridge, PutObject butterknife fridge, CloseObject fridge, Navigation countertop, PickupObject breadsliced, Navigation fridge, OpenObject fridge, PutObject breadsliced fridge, CloseObject fridge, OpenObject fridge\nVisible objects are fridge, breadsliced, countertop, butterknife\nNext Plans: PickupObject breadsliced, CloseObject fridge, Navigation countertop, PutObject breadsliced countertop\n\nTask description: put a cooled potato slice inside of the microwave\nCompleted plans: Navigation countertop, PickupObject knife, Navigation potato, OpenObject microwave, SliceObject potato, CloseObject microwave, Navigation microwave, OpenObject microwave, PutObject knife microwave, CloseObject microwave, Navigation microwave, OpenObject microwave, PickupObject potatosliced, CloseObject microwave, Navigation fridge, OpenObject fridge, PutObject potatosliced fridge, CloseObject fridge, OpenObject fridge, PickupObject potatosliced, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject potatosliced microwave\nVisible objects are fridge, microwave, knife, potatosliced\nNext Plans: CloseObject microwave\n\nTask description: Put a slice of bread in the fridge.\nCompleted plans: Navigation sinkbasin, PickupObject knife, SliceObject bread, PutObject knife sink, PickupObject breadsliced, Navigation fridge, OpenObject fridge, PutObject breadsliced fridge, CloseObject fridge, Navigation countertop, PickupObject butterknife, Navigation bread, SliceObject bread, Navigation fridge\nVisible objects are sink, fridge, breadsliced, butterknife, knife\nNext Plans: OpenObject fridge, PutObject butterknife fridge, CloseObject fridge, Navigation countertop, PickupObject breadsliced, Navigation fridge, OpenObject fridge, PutObject breadsliced fridge, CloseObject fridge\n\nTask description: Put a chilled tomato slice into the microwave.\nCompleted plans: Navigation countertop, PickupObject tomato, Navigation countertop, PutObject tomato countertop, PickupObject butterknife, SliceObject tomato, PutObject butterknife countertop, PickupObject tomatosliced, Navigation fridge, OpenObject fridge, PutObject tomatosliced fridge, CloseObject fridge, OpenObject fridge, PickupObject tomatosliced, CloseObject fridge\nVisible objects are fridge, microwave, tomatosliced, butterknife, tomato, countertop\nNext Plans: Navigation microwave, OpenObject microwave, PutObject tomatosliced microwave, CloseObject microwave\n\nTask description: If the chilled dairy drink is in cold storage, heat one cup of it in the food-heating appliance.\nCompleted plans: \nVisible objects are bananas, bench, bookshelf, candle, ceiling, ceilinglamp, chair, coffeemaker, condimentbottle, condimentshaker, cookingpot, curtains, cutleryfork, cutleryknife, cutlets, dishbowl, dishwasher, door, doorjamb, faucet, floor, fridge, fryingpan, juice, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, knifeblock, lightswitch, microwave, milk, mincedmeat, orchid, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tvstand, wall, walllamp, wallphone, wallpictureframe, waterglass, window\nNext Plans:",
  "raw_output": "Navigation fridge, OpenObject fridge, PickupObject milk, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject milk microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject milk, CloseObject microwave",
  "parsed_plan": [
    [
      "Navigation",
      "fridge"
    ],
    [
      "OpenObject",
      "fridge"
    ],
    [
      "PickupObject",
      "milk"
    ],
    [
      "CloseObject",
      "fridge"
    ],
    [
      "Navigation",
      "microwave"
    ],
    [
      "OpenObject",
      "microwave"
    ],
    [
      "PutObject",
      "milk",
      "microwave"
    ],
    [
      "CloseObject",
      "microwave"
    ],
    [
      "ToggleObjectOn",
      "microwave"
    ],
    [
      "ToggleObjectOff",
      "microwave"
    ],
    [
      "OpenObject",
      "microwave"
    ],
    [
      "PickupObject",
      "milk"
    ],
    [
      "CloseObject",
      "microwave"
    ]
  ],
  "replan_count": 2,
  "reason": "initial planning"
}
```
## Step 9
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: G1_01=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 10
- **Action**: `[walk] <fridge> (162)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_01=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 11
- **Action**: `[open] <fridge> (162)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_01=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 12
- **Action**: `[walk] <milk> (177)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_01=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 13
- **Action**: `[grab] <milk> (177)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_01=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 14
- **Action**: `[walk] <fridge> (162)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_01=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

