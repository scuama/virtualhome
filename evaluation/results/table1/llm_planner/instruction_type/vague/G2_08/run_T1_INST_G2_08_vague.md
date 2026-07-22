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
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put the chilled bowl on the counter\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject bowl, CloseObject cabinet, Navigation fridge, OpenObject fridge\nVisible objects are fridge, countertop, bowl\nNext Plans: PutObject bowl fridge, CloseObject fridge, OpenObject fridge, PickupObject bowl, CloseObject fridge, Navigation countertop, PutObject bowl countertop\n\nTask description: Move a spoon and cup from a table to the counter.\nCompleted plans: Navigation diningtable, PickupObject cup, Navigation countertop\nVisible objects are cup, countertop\nNext Plans: PutObject cup countertop\n\nTask description: Throw away a heated slice of bread.\nCompleted plans: Navigation sinkbasin\nVisible objects are garbagecan, microwave, breadsliced, knife, drawer\nNext Plans: PickupObject knife, Navigation bread, SliceObject bread, Navigation drawer, OpenObject drawer, PutObject knife drawer, CloseObject drawer, Navigation countertop, PickupObject breadsliced, Navigation microwave, OpenObject microwave, PutObject breadsliced microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject breadsliced, CloseObject microwave, Navigation garbagecan, PutObject breadsliced garbagecan\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop, PickupObject winebottle, Navigation fridge, OpenObject fridge\nVisible objects are fridge, cabinet, winebottle\nNext Plans: PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject vase, CloseObject cabinet, Navigation box, PutObject vase box, PickupObject box, Navigation diningtable\nVisible objects are box, vase, diningtable\nNext Plans: PutObject box diningtable\n\nTask description: To cool a potato slice and place it in the microwave.\nCompleted plans: Navigation countertop, PickupObject knife, Navigation potato, SliceObject potato, Navigation microwave, OpenObject microwave, PutObject knife microwave, CloseObject microwave, Navigation countertop, PickupObject potatosliced, Navigation fridge, OpenObject fridge, PutObject potatosliced fridge, CloseObject fridge, OpenObject fridge\nVisible objects are fridge, microwave, knife, potatosliced\nNext Plans: PickupObject potatosliced, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject potatosliced microwave, CloseObject microwave\n\nTask description: Put a heated egg in the sink.\nCompleted plans: Navigation fridge, OpenObject fridge, PickupObject egg, CloseObject fridge, Navigation microwave, OpenObject microwave\nVisible objects are egg, microwave, sink\nNext Plans: PutObject egg microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject egg, CloseObject microwave, Navigation sinkbasin, PutObject egg sink\n\nTask description: To heat a piece of apple and place it on the edge of the white table.\nCompleted plans: Navigation diningtable, PickupObject butterknife, Navigation apple, OpenObject fridge, SliceObject apple, PutObject butterknife fridge, PickupObject applesliced, CloseObject fridge, Navigation microwave\nVisible objects are applesliced, fridge, microwave, butterknife, diningtable\nNext Plans: OpenObject microwave, PutObject applesliced microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject applesliced, CloseObject microwave, Navigation diningtable, PutObject applesliced diningtable\n\nTask description: Put a heated plate down in a corner cabinet. \nCompleted plans: Navigation fridge, OpenObject fridge, PickupObject plate, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject plate microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject plate, CloseObject microwave, Navigation cabinet, OpenObject cabinet\nVisible objects are plate, cabinet, microwave\nNext Plans: PutObject plate cabinet, CloseObject cabinet\n\nTask description: Warm up the dairy beverage and bring it to me.\nCompleted plans: \nVisible objects are bananas, bench, bookshelf, candle, ceiling, ceilinglamp, chair, coffeemaker, condimentbottle, condimentshaker, cookingpot, curtains, cutleryfork, cutleryknife, cutlets, dishbowl, dishwasher, door, doorjamb, faucet, floor, fridge, fryingpan, juice, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, knifeblock, lightswitch, microwave, milk, mincedmeat, orchid, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tvstand, wall, walllamp, wallphone, wallpictureframe, waterglass, window\nNext Plans:",
  "raw_output": "Navigation fridge, OpenObject fridge, PickupObject milk, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject milk microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject milk, CloseObject microwave, Navigation kitchentable, PutObject milk kitchentable",
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
    ],
    [
      "Navigation",
      "kitchentable"
    ],
    [
      "PutObject",
      "milk",
      "kitchentable"
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
- **Task Progress**: G2_08=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 1
- **Action**: `[walk] <fridge> (162)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G2_08=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 2
- **Action**: `[open] <fridge> (162)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G2_08=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 3
- **Action**: `[walk] <milk> (176)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G2_08=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 4
- **Action**: `[grab] <milk> (176)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G2_08=done
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

