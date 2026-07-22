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
    "bellpepper",
    "bench",
    "book",
    "bookshelf",
    "box",
    "candybar",
    "ceiling",
    "ceilinglamp",
    "cereal",
    "chips",
    "chocolatesyrup",
    "clock",
    "coffeemaker",
    "crackers",
    "creamybuns",
    "cutleryfork",
    "cutleryknife",
    "dishbowl",
    "dishwashingliquid",
    "door",
    "faucet",
    "floor",
    "fridge",
    "fryingpan",
    "garbagecan",
    "kitchencabinet",
    "kitchencounter",
    "kitchencounterdrawer",
    "kitchentable",
    "lightswitch",
    "microwave",
    "mug",
    "orchid",
    "photoframe",
    "pie",
    "plate",
    "powersocket",
    "rug",
    "salmon",
    "sink",
    "stove",
    "stovefan",
    "toaster",
    "tv",
    "tvstand",
    "wall",
    "walllamp",
    "wallphone",
    "wallpictureframe",
    "wallshelf",
    "washingsponge",
    "waterglass",
    "whippedcream",
    "wineglass"
  ],
  "completed_plans": [],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop, PickupObject winebottle, Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge\nVisible objects are fridge, cabinet, winebottle\nNext Plans: OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Move a spoon and cup from a table to the counter.\nCompleted plans: Navigation diningtable, PickupObject cup, Navigation countertop\nVisible objects are cup, countertop\nNext Plans: PutObject cup countertop\n\nTask description: place a pot with a sponge in it in a kitchen cabinet\nCompleted plans: \nVisible objects are dishsponge, cabinet, pot\nNext Plans: Navigation cabinet, OpenObject cabinet, PickupObject dishsponge, CloseObject cabinet, Navigation pot, PutObject dishsponge pot, PickupObject pot, Navigation cabinet, OpenObject cabinet, PutObject pot cabinet, CloseObject cabinet\n\nTask description: put the spoon and the plate into the door under the sink\nCompleted plans: Navigation sinkbasin, PickupObject ladle, Navigation bowl, PutObject ladle bowl\nVisible objects are cabinet, ladle, bowl\nNext Plans: PickupObject bowl, Navigation cabinet, OpenObject cabinet, PutObject bowl cabinet, CloseObject cabinet\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject vase, CloseObject cabinet, Navigation box, PutObject vase box, PickupObject box, Navigation diningtable\nVisible objects are box, vase, diningtable\nNext Plans: PutObject box diningtable\n\nTask description: Put a heated plate down in a corner cabinet. \nCompleted plans: Navigation fridge, OpenObject fridge, PickupObject plate, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject plate microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject plate, CloseObject microwave, Navigation cabinet, OpenObject cabinet\nVisible objects are plate, cabinet, microwave\nNext Plans: PutObject plate cabinet, CloseObject cabinet\n\nTask description: Put the chilled bowl on the counter\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject bowl, CloseObject cabinet, Navigation fridge, OpenObject fridge\nVisible objects are fridge, countertop, bowl\nNext Plans: PutObject bowl fridge, CloseObject fridge, OpenObject fridge, PickupObject bowl, CloseObject fridge, Navigation countertop, PutObject bowl countertop\n\nTask description: Wash the soap that you found in the cabinet and place it back in the cabinet\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject soapbar, PutObject soapbar sink\nVisible objects are cabinet, sink, soapbar\nNext Plans: ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject soapbar, Navigation cabinet, PutObject soapbar cabinet, CloseObject cabinet\n\nTask description: Place a wet bar of soap under the sink.\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject soapbar, PutObject soapbar sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject soapbar\nVisible objects are cabinet, sink, soapbar\nNext Plans: Navigation cabinet, OpenObject cabinet, PutObject soapbar cabinet, CloseObject cabinet\n\nTask description: If there is water in the mug, pour it out and put the mug in the cabinet.\nCompleted plans: \nVisible objects are bellpepper, bench, book, bookshelf, box, candybar, ceiling, ceilinglamp, cereal, chips, chocolatesyrup, clock, coffeemaker, crackers, creamybuns, cutleryfork, cutleryknife, dishbowl, dishwashingliquid, door, faucet, floor, fridge, fryingpan, garbagecan, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, lightswitch, microwave, mug, orchid, photoframe, pie, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tv, tvstand, wall, walllamp, wallphone, wallpictureframe, wallshelf, washingsponge, waterglass, whippedcream, wineglass\nNext Plans:",
  "raw_output": "PickupObject mug, Navigation sink, PutObject mug sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject mug, Navigation kitchencabinet, OpenObject kitchencabinet, PutObject mug kitchencabinet, CloseObject kitchencabinet",
  "parsed_plan": [
    [
      "PickupObject",
      "mug"
    ],
    [
      "Navigation",
      "sink"
    ],
    [
      "PutObject",
      "mug",
      "sink"
    ],
    [
      "ToggleObjectOn",
      "faucet"
    ],
    [
      "ToggleObjectOff",
      "faucet"
    ],
    [
      "PickupObject",
      "mug"
    ],
    [
      "Navigation",
      "kitchencabinet"
    ],
    [
      "OpenObject",
      "kitchencabinet"
    ],
    [
      "PutObject",
      "mug",
      "kitchencabinet"
    ],
    [
      "CloseObject",
      "kitchencabinet"
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
- **Task Progress**: G1_05=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 1
- **Action**: `[walk] <mug> (194)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_05=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 2
- **Action**: `[grab] <mug> (194)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_05=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 3
- **Action**: `[walk] <sink> (247)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_05=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 4
- **Action**: `[putin] <mug> (194) <sink> (247)`
- **Action Success**: `False`
- **Action Message**: {'0': {'message': 'ScriptExcutor 0: EXECUTION_GENERAL: Script is impossible to execute\n\n'}}
- **Task Progress**: G1_05=pending
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
    "bellpepper",
    "bench",
    "book",
    "bookshelf",
    "box",
    "candybar",
    "ceiling",
    "ceilinglamp",
    "cereal",
    "chips",
    "chocolatesyrup",
    "clock",
    "coffeemaker",
    "crackers",
    "creamybuns",
    "cutleryfork",
    "cutleryknife",
    "dishbowl",
    "dishwashingliquid",
    "door",
    "faucet",
    "floor",
    "fridge",
    "fryingpan",
    "garbagecan",
    "kitchencabinet",
    "kitchencounter",
    "kitchencounterdrawer",
    "kitchentable",
    "lightswitch",
    "microwave",
    "mug",
    "orchid",
    "photoframe",
    "pie",
    "plate",
    "powersocket",
    "rug",
    "salmon",
    "sink",
    "stove",
    "stovefan",
    "toaster",
    "tv",
    "tvstand",
    "wall",
    "walllamp",
    "wallphone",
    "wallpictureframe",
    "wallshelf",
    "washingsponge",
    "waterglass",
    "whippedcream",
    "wineglass"
  ],
  "completed_plans": [],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop, PickupObject winebottle\nVisible objects are fridge, cabinet, winebottle\nNext Plans: Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Move a spoon and cup from a table to the counter.\nCompleted plans: \nVisible objects are cup, countertop\nNext Plans: Navigation diningtable, PickupObject cup, Navigation countertop, PutObject cup countertop\n\nTask description: place a pot with a sponge in it in a kitchen cabinet\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject dishsponge, CloseObject cabinet\nVisible objects are dishsponge, cabinet, pot\nNext Plans: Navigation pot, PutObject dishsponge pot, PickupObject pot, Navigation cabinet, OpenObject cabinet, PutObject pot cabinet, CloseObject cabinet\n\nTask description: put the spoon and the plate into the door under the sink\nCompleted plans: Navigation sinkbasin\nVisible objects are cabinet, ladle, bowl\nNext Plans: PickupObject ladle, Navigation bowl, PutObject ladle bowl, PickupObject bowl, Navigation cabinet, OpenObject cabinet, PutObject bowl cabinet, CloseObject cabinet\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject vase, CloseObject cabinet, Navigation box, PutObject vase box, PickupObject box\nVisible objects are box, vase, diningtable\nNext Plans: Navigation diningtable, PutObject box diningtable\n\nTask description: Put a heated plate down in a corner cabinet. \nCompleted plans: Navigation fridge, OpenObject fridge, PickupObject plate, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject plate microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject plate, CloseObject microwave, Navigation cabinet\nVisible objects are plate, cabinet, microwave\nNext Plans: OpenObject cabinet, PutObject plate cabinet, CloseObject cabinet\n\nTask description: Put the chilled bowl on the counter\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject bowl, CloseObject cabinet, Navigation fridge, OpenObject fridge, PutObject bowl fridge\nVisible objects are fridge, countertop, bowl\nNext Plans: CloseObject fridge, OpenObject fridge, PickupObject bowl, CloseObject fridge, Navigation countertop, PutObject bowl countertop\n\nTask description: Wash the soap that you found in the cabinet and place it back in the cabinet\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject soapbar, PutObject soapbar sink, ToggleObjectOn faucet, ToggleObjectOff faucet\nVisible objects are cabinet, sink, soapbar\nNext Plans: PickupObject soapbar, Navigation cabinet, PutObject soapbar cabinet, CloseObject cabinet\n\nTask description: Place a wet bar of soap under the sink.\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject soapbar\nVisible objects are cabinet, sink, soapbar\nNext Plans: PutObject soapbar sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject soapbar, Navigation cabinet, OpenObject cabinet, PutObject soapbar cabinet, CloseObject cabinet\n\nTask description: If there is water in the mug, pour it out and put the mug in the cabinet.\nCompleted plans: \nVisible objects are bellpepper, bench, book, bookshelf, box, candybar, ceiling, ceilinglamp, cereal, chips, chocolatesyrup, clock, coffeemaker, crackers, creamybuns, cutleryfork, cutleryknife, dishbowl, dishwashingliquid, door, faucet, floor, fridge, fryingpan, garbagecan, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, lightswitch, microwave, mug, orchid, photoframe, pie, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tv, tvstand, wall, walllamp, wallphone, wallpictureframe, wallshelf, washingsponge, waterglass, whippedcream, wineglass\nNext Plans:",
  "raw_output": "Navigation mug, PickupObject mug, Navigation sink, PutObject mug sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject mug, Navigation kitchencabinet, OpenObject kitchencabinet, PutObject mug kitchencabinet, CloseObject kitchencabinet",
  "parsed_plan": [
    [
      "Navigation",
      "mug"
    ],
    [
      "PickupObject",
      "mug"
    ],
    [
      "Navigation",
      "sink"
    ],
    [
      "PutObject",
      "mug",
      "sink"
    ],
    [
      "ToggleObjectOn",
      "faucet"
    ],
    [
      "ToggleObjectOff",
      "faucet"
    ],
    [
      "PickupObject",
      "mug"
    ],
    [
      "Navigation",
      "kitchencabinet"
    ],
    [
      "OpenObject",
      "kitchencabinet"
    ],
    [
      "PutObject",
      "mug",
      "kitchencabinet"
    ],
    [
      "CloseObject",
      "kitchencabinet"
    ]
  ],
  "replan_count": 2,
  "reason": "previous action failed: [putin] <mug> (194) <sink> (247)"
}
```
## Step 5
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: G1_05=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 6
- **Action**: `[grab] <mug> (194)`
- **Action Success**: `False`
- **Action Message**: {'0': {'message': 'ScriptExcutor 0: EXECUTION_GENERAL: Script is impossible to execute\n\n'}}
- **Task Progress**: G1_05=pending
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
    "bellpepper",
    "bench",
    "book",
    "bookshelf",
    "box",
    "candybar",
    "ceiling",
    "ceilinglamp",
    "cereal",
    "chips",
    "chocolatesyrup",
    "clock",
    "coffeemaker",
    "crackers",
    "creamybuns",
    "cutleryfork",
    "cutleryknife",
    "dishbowl",
    "dishwashingliquid",
    "door",
    "faucet",
    "floor",
    "fridge",
    "fryingpan",
    "garbagecan",
    "kitchencabinet",
    "kitchencounter",
    "kitchencounterdrawer",
    "kitchentable",
    "lightswitch",
    "microwave",
    "mug",
    "orchid",
    "photoframe",
    "pie",
    "plate",
    "powersocket",
    "rug",
    "salmon",
    "sink",
    "stove",
    "stovefan",
    "toaster",
    "tv",
    "tvstand",
    "wall",
    "walllamp",
    "wallphone",
    "wallpictureframe",
    "wallshelf",
    "washingsponge",
    "waterglass",
    "whippedcream",
    "wineglass"
  ],
  "completed_plans": [
    [
      "Navigation",
      "mug"
    ]
  ],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: \nVisible objects are fridge, cabinet, winebottle\nNext Plans: Navigation countertop, PickupObject winebottle, Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Move a spoon and cup from a table to the counter.\nCompleted plans: \nVisible objects are cup, countertop\nNext Plans: Navigation diningtable, PickupObject cup, Navigation countertop, PutObject cup countertop\n\nTask description: place a pot with a sponge in it in a kitchen cabinet\nCompleted plans: Navigation cabinet\nVisible objects are dishsponge, cabinet, pot\nNext Plans: OpenObject cabinet, PickupObject dishsponge, CloseObject cabinet, Navigation pot, PutObject dishsponge pot, PickupObject pot, Navigation cabinet, OpenObject cabinet, PutObject pot cabinet, CloseObject cabinet\n\nTask description: put the spoon and the plate into the door under the sink\nCompleted plans: Navigation sinkbasin, PickupObject ladle, Navigation bowl, PutObject ladle bowl, PickupObject bowl\nVisible objects are cabinet, ladle, bowl\nNext Plans: Navigation cabinet, OpenObject cabinet, PutObject bowl cabinet, CloseObject cabinet\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet, OpenObject cabinet\nVisible objects are box, vase, diningtable\nNext Plans: PickupObject vase, CloseObject cabinet, Navigation box, PutObject vase box, PickupObject box, Navigation diningtable, PutObject box diningtable\n\nTask description: Put a heated plate down in a corner cabinet. \nCompleted plans: Navigation fridge, OpenObject fridge, PickupObject plate, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject plate microwave, CloseObject microwave, ToggleObjectOn microwave\nVisible objects are plate, cabinet, microwave\nNext Plans: ToggleObjectOff microwave, OpenObject microwave, PickupObject plate, CloseObject microwave, Navigation cabinet, OpenObject cabinet, PutObject plate cabinet, CloseObject cabinet\n\nTask description: Put the chilled bowl on the counter\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject bowl, CloseObject cabinet\nVisible objects are fridge, countertop, bowl\nNext Plans: Navigation fridge, OpenObject fridge, PutObject bowl fridge, CloseObject fridge, OpenObject fridge, PickupObject bowl, CloseObject fridge, Navigation countertop, PutObject bowl countertop\n\nTask description: Wash the soap that you found in the cabinet and place it back in the cabinet\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject soapbar, PutObject soapbar sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject soapbar, Navigation cabinet, PutObject soapbar cabinet\nVisible objects are cabinet, sink, soapbar\nNext Plans: CloseObject cabinet\n\nTask description: Place a wet bar of soap under the sink.\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject soapbar\nVisible objects are cabinet, sink, soapbar\nNext Plans: PutObject soapbar sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject soapbar, Navigation cabinet, OpenObject cabinet, PutObject soapbar cabinet, CloseObject cabinet\n\nTask description: If there is water in the mug, pour it out and put the mug in the cabinet.\nCompleted plans: Navigation mug\nVisible objects are bellpepper, bench, book, bookshelf, box, candybar, ceiling, ceilinglamp, cereal, chips, chocolatesyrup, clock, coffeemaker, crackers, creamybuns, cutleryfork, cutleryknife, dishbowl, dishwashingliquid, door, faucet, floor, fridge, fryingpan, garbagecan, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, lightswitch, microwave, mug, orchid, photoframe, pie, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tv, tvstand, wall, walllamp, wallphone, wallpictureframe, wallshelf, washingsponge, waterglass, whippedcream, wineglass\nNext Plans:",
  "raw_output": "OpenObject mug",
  "parsed_plan": [
    [
      "OpenObject",
      "mug"
    ]
  ],
  "replan_count": 3,
  "reason": "previous action failed: [grab] <mug> (194)"
}
```
## Step 7
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: G1_05=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 8
- **Action**: `[open] <mug> (194)`
- **Action Success**: `False`
- **Action Message**: {'0': {'message': 'ScriptExcutor 0: EXECUTION_GENERAL: Script is impossible to execute\n\n'}}
- **Task Progress**: G1_05=pending
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
    "bellpepper",
    "bench",
    "book",
    "bookshelf",
    "box",
    "candybar",
    "ceiling",
    "ceilinglamp",
    "cereal",
    "chips",
    "chocolatesyrup",
    "clock",
    "coffeemaker",
    "crackers",
    "creamybuns",
    "cutleryfork",
    "cutleryknife",
    "dishbowl",
    "dishwashingliquid",
    "door",
    "faucet",
    "floor",
    "fridge",
    "fryingpan",
    "garbagecan",
    "kitchencabinet",
    "kitchencounter",
    "kitchencounterdrawer",
    "kitchentable",
    "lightswitch",
    "microwave",
    "mug",
    "orchid",
    "photoframe",
    "pie",
    "plate",
    "powersocket",
    "rug",
    "salmon",
    "sink",
    "stove",
    "stovefan",
    "toaster",
    "tv",
    "tvstand",
    "wall",
    "walllamp",
    "wallphone",
    "wallpictureframe",
    "wallshelf",
    "washingsponge",
    "waterglass",
    "whippedcream",
    "wineglass"
  ],
  "completed_plans": [
    [
      "Navigation",
      "mug"
    ]
  ],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop, PickupObject winebottle, Navigation fridge\nVisible objects are fridge, cabinet, winebottle\nNext Plans: OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Move a spoon and cup from a table to the counter.\nCompleted plans: Navigation diningtable\nVisible objects are cup, countertop\nNext Plans: PickupObject cup, Navigation countertop, PutObject cup countertop\n\nTask description: place a pot with a sponge in it in a kitchen cabinet\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject dishsponge, CloseObject cabinet, Navigation pot\nVisible objects are dishsponge, cabinet, pot\nNext Plans: PutObject dishsponge pot, PickupObject pot, Navigation cabinet, OpenObject cabinet, PutObject pot cabinet, CloseObject cabinet\n\nTask description: put the spoon and the plate into the door under the sink\nCompleted plans: Navigation sinkbasin, PickupObject ladle, Navigation bowl, PutObject ladle bowl, PickupObject bowl, Navigation cabinet, OpenObject cabinet\nVisible objects are cabinet, ladle, bowl\nNext Plans: PutObject bowl cabinet, CloseObject cabinet\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet\nVisible objects are box, vase, diningtable\nNext Plans: OpenObject cabinet, PickupObject vase, CloseObject cabinet, Navigation box, PutObject vase box, PickupObject box, Navigation diningtable, PutObject box diningtable\n\nTask description: Put a heated plate down in a corner cabinet. \nCompleted plans: \nVisible objects are plate, cabinet, microwave\nNext Plans: Navigation fridge, OpenObject fridge, PickupObject plate, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject plate microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject plate, CloseObject microwave, Navigation cabinet, OpenObject cabinet, PutObject plate cabinet, CloseObject cabinet\n\nTask description: Put the chilled bowl on the counter\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject bowl, CloseObject cabinet, Navigation fridge, OpenObject fridge, PutObject bowl fridge\nVisible objects are fridge, countertop, bowl\nNext Plans: CloseObject fridge, OpenObject fridge, PickupObject bowl, CloseObject fridge, Navigation countertop, PutObject bowl countertop\n\nTask description: Wash the soap that you found in the cabinet and place it back in the cabinet\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject soapbar, PutObject soapbar sink\nVisible objects are cabinet, sink, soapbar\nNext Plans: ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject soapbar, Navigation cabinet, PutObject soapbar cabinet, CloseObject cabinet\n\nTask description: Place a wet bar of soap under the sink.\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject soapbar, PutObject soapbar sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject soapbar, Navigation cabinet\nVisible objects are cabinet, sink, soapbar\nNext Plans: OpenObject cabinet, PutObject soapbar cabinet, CloseObject cabinet\n\nTask description: If there is water in the mug, pour it out and put the mug in the cabinet.\nCompleted plans: Navigation mug\nVisible objects are bellpepper, bench, book, bookshelf, box, candybar, ceiling, ceilinglamp, cereal, chips, chocolatesyrup, clock, coffeemaker, crackers, creamybuns, cutleryfork, cutleryknife, dishbowl, dishwashingliquid, door, faucet, floor, fridge, fryingpan, garbagecan, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, lightswitch, microwave, mug, orchid, photoframe, pie, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tv, tvstand, wall, walllamp, wallphone, wallpictureframe, wallshelf, washingsponge, waterglass, whippedcream, wineglass\nNext Plans:",
  "raw_output": "PickupObject mug, Navigation kitchencabinet, OpenObject kitchencabinet, PutObject mug kitchencabinet, CloseObject kitchencabinet",
  "parsed_plan": [
    [
      "PickupObject",
      "mug"
    ],
    [
      "Navigation",
      "kitchencabinet"
    ],
    [
      "OpenObject",
      "kitchencabinet"
    ],
    [
      "PutObject",
      "mug",
      "kitchencabinet"
    ],
    [
      "CloseObject",
      "kitchencabinet"
    ]
  ],
  "replan_count": 4,
  "reason": "previous action failed: [open] <mug> (194)"
}
```
## Step 9
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: G1_05=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 10
- **Action**: `[grab] <mug> (194)`
- **Action Success**: `False`
- **Action Message**: {'0': {'message': 'ScriptExcutor 0: EXECUTION_GENERAL: Script is impossible to execute\n\n'}}
- **Task Progress**: G1_05=pending
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
    "bellpepper",
    "bench",
    "book",
    "bookshelf",
    "box",
    "candybar",
    "ceiling",
    "ceilinglamp",
    "cereal",
    "chips",
    "chocolatesyrup",
    "clock",
    "coffeemaker",
    "crackers",
    "creamybuns",
    "cutleryfork",
    "cutleryknife",
    "dishbowl",
    "dishwashingliquid",
    "door",
    "faucet",
    "floor",
    "fridge",
    "fryingpan",
    "garbagecan",
    "kitchencabinet",
    "kitchencounter",
    "kitchencounterdrawer",
    "kitchentable",
    "lightswitch",
    "microwave",
    "mug",
    "orchid",
    "photoframe",
    "pie",
    "plate",
    "powersocket",
    "rug",
    "salmon",
    "sink",
    "stove",
    "stovefan",
    "toaster",
    "tv",
    "tvstand",
    "wall",
    "walllamp",
    "wallphone",
    "wallpictureframe",
    "wallshelf",
    "washingsponge",
    "waterglass",
    "whippedcream",
    "wineglass"
  ],
  "completed_plans": [
    [
      "Navigation",
      "mug"
    ]
  ],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop, PickupObject winebottle, Navigation fridge\nVisible objects are fridge, cabinet, winebottle\nNext Plans: OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Move a spoon and cup from a table to the counter.\nCompleted plans: Navigation diningtable, PickupObject cup\nVisible objects are cup, countertop\nNext Plans: Navigation countertop, PutObject cup countertop\n\nTask description: place a pot with a sponge in it in a kitchen cabinet\nCompleted plans: Navigation cabinet\nVisible objects are dishsponge, cabinet, pot\nNext Plans: OpenObject cabinet, PickupObject dishsponge, CloseObject cabinet, Navigation pot, PutObject dishsponge pot, PickupObject pot, Navigation cabinet, OpenObject cabinet, PutObject pot cabinet, CloseObject cabinet\n\nTask description: put the spoon and the plate into the door under the sink\nCompleted plans: Navigation sinkbasin, PickupObject ladle, Navigation bowl, PutObject ladle bowl, PickupObject bowl, Navigation cabinet\nVisible objects are cabinet, ladle, bowl\nNext Plans: OpenObject cabinet, PutObject bowl cabinet, CloseObject cabinet\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject vase, CloseObject cabinet, Navigation box, PutObject vase box, PickupObject box\nVisible objects are box, vase, diningtable\nNext Plans: Navigation diningtable, PutObject box diningtable\n\nTask description: Put a heated plate down in a corner cabinet. \nCompleted plans: Navigation fridge, OpenObject fridge, PickupObject plate, CloseObject fridge\nVisible objects are plate, cabinet, microwave\nNext Plans: Navigation microwave, OpenObject microwave, PutObject plate microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject plate, CloseObject microwave, Navigation cabinet, OpenObject cabinet, PutObject plate cabinet, CloseObject cabinet\n\nTask description: Put the chilled bowl on the counter\nCompleted plans: Navigation cabinet\nVisible objects are fridge, countertop, bowl\nNext Plans: OpenObject cabinet, PickupObject bowl, CloseObject cabinet, Navigation fridge, OpenObject fridge, PutObject bowl fridge, CloseObject fridge, OpenObject fridge, PickupObject bowl, CloseObject fridge, Navigation countertop, PutObject bowl countertop\n\nTask description: Wash the soap that you found in the cabinet and place it back in the cabinet\nCompleted plans: Navigation cabinet\nVisible objects are cabinet, sink, soapbar\nNext Plans: OpenObject cabinet, PickupObject soapbar, PutObject soapbar sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject soapbar, Navigation cabinet, PutObject soapbar cabinet, CloseObject cabinet\n\nTask description: Place a wet bar of soap under the sink.\nCompleted plans: \nVisible objects are cabinet, sink, soapbar\nNext Plans: Navigation cabinet, OpenObject cabinet, PickupObject soapbar, PutObject soapbar sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject soapbar, Navigation cabinet, OpenObject cabinet, PutObject soapbar cabinet, CloseObject cabinet\n\nTask description: If there is water in the mug, pour it out and put the mug in the cabinet.\nCompleted plans: Navigation mug\nVisible objects are bellpepper, bench, book, bookshelf, box, candybar, ceiling, ceilinglamp, cereal, chips, chocolatesyrup, clock, coffeemaker, crackers, creamybuns, cutleryfork, cutleryknife, dishbowl, dishwashingliquid, door, faucet, floor, fridge, fryingpan, garbagecan, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, lightswitch, microwave, mug, orchid, photoframe, pie, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tv, tvstand, wall, walllamp, wallphone, wallpictureframe, wallshelf, washingsponge, waterglass, whippedcream, wineglass\nNext Plans:",
  "raw_output": "OpenObject kitchencabinet, PutObject mug kitchencabinet, CloseObject kitchencabinet",
  "parsed_plan": [
    [
      "OpenObject",
      "kitchencabinet"
    ],
    [
      "PutObject",
      "mug",
      "kitchencabinet"
    ],
    [
      "CloseObject",
      "kitchencabinet"
    ]
  ],
  "replan_count": 5,
  "reason": "previous action failed: [grab] <mug> (194)"
}
```
## Step 11
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: G1_05=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 12
- **Action**: `[open] <kitchencabinet> (234)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_05=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 13
- **Action**: `[putin] <mug> (194) <kitchencabinet> (234)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_05=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 14
- **Action**: `[close] <kitchencabinet> (234)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_05=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

