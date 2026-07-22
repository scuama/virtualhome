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
    "apple",
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
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put cold apple on a table. \nCompleted plans: Navigation diningtable, PickupObject knife, Navigation apple, OpenObject microwave, SliceObject apple, CloseObject microwave, Navigation diningtable, PutObject knife diningtable, Navigation microwave, OpenObject microwave, PickupObject applesliced, CloseObject microwave\nVisible objects are fridge, knife, diningtable, applesliced\nNext Plans: Navigation fridge, OpenObject fridge, PutObject applesliced fridge, CloseObject fridge, OpenObject fridge, PickupObject applesliced, CloseObject fridge, Navigation diningtable, PutObject applesliced diningtable\n\nTask description: Put the apple slice in the trash.\nCompleted plans: Navigation countertop, PickupObject apple, Navigation countertop, PutObject apple countertop, PickupObject butterknife, SliceObject apple, PutObject butterknife countertop, PickupObject applesliced, Navigation fridge, OpenObject fridge, PutObject applesliced fridge, CloseObject fridge, OpenObject fridge\nVisible objects are applesliced, fridge, garbagecan, apple, butterknife, countertop\nNext Plans: PickupObject applesliced, CloseObject fridge, Navigation garbagecan, PutObject applesliced garbagecan\n\nTask description: Put cooked apple on a counter.\nCompleted plans: Navigation garbagecan\nVisible objects are applesliced, countertop, microwave, butterknife, apple\nNext Plans: PickupObject apple, Navigation countertop, PutObject apple countertop, PickupObject butterknife, SliceObject apple, PutObject butterknife countertop, PickupObject applesliced, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject applesliced, CloseObject microwave, Navigation countertop, PutObject applesliced countertop\n\nTask description: Place an apple slice on the table.\nCompleted plans: Navigation diningtable, PickupObject knife, Navigation apple, SliceObject apple\nVisible objects are plate, applesliced, knife, diningtable\nNext Plans: Navigation diningtable, PutObject knife diningtable, Navigation diningtable, PickupObject applesliced, Navigation plate, PutObject applesliced plate, PickupObject plate, Navigation diningtable, PutObject plate diningtable\n\nTask description: To heat a piece of apple and place it on the edge of the white table.\nCompleted plans: Navigation diningtable, PickupObject butterknife, Navigation apple, OpenObject fridge, SliceObject apple, PutObject butterknife fridge, PickupObject applesliced, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject applesliced\nVisible objects are applesliced, fridge, microwave, butterknife, diningtable\nNext Plans: CloseObject microwave, Navigation diningtable, PutObject applesliced diningtable\n\nTask description: Put a pot with a piece of apple in it on a table.\nCompleted plans: Navigation countertop, PickupObject knife, Navigation apple, OpenObject fridge, SliceObject apple, CloseObject fridge, Navigation diningtable, PutObject knife diningtable, Navigation fridge, OpenObject fridge, PickupObject applesliced, CloseObject fridge, Navigation pot, PutObject applesliced pot, PickupObject pot\nVisible objects are pot, knife, diningtable, applesliced\nNext Plans: Navigation diningtable, PutObject pot diningtable\n\nTask description: Carry a knife to cut the yellow apple in the fridge\nCompleted plans: Navigation countertop, PickupObject knife, Navigation apple\nVisible objects are \nNext Plans: OpenObject fridge, SliceObject apple, CloseObject fridge\n\nTask description: Place two apple slices and a knife in the microwave\nCompleted plans: Navigation countertop, PickupObject butterknife, Navigation apple, SliceObject apple, Navigation microwave, OpenObject microwave, PutObject butterknife microwave, CloseObject microwave, Navigation diningtable, PickupObject applesliced, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, PickupObject butterknife, CloseObject microwave, Navigation apple, SliceObject apple, Navigation microwave, OpenObject microwave, PutObject butterknife microwave, CloseObject microwave, Navigation sidetable, PickupObject applesliced, Navigation microwave, OpenObject microwave\nVisible objects are applesliced, microwave, butterknife\nNext Plans: PutObject applesliced microwave, CloseObject microwave\n\nTask description: Put washed apple piece inside the microwave next to the gray knife.\nCompleted plans: Navigation countertop, PickupObject butterknife, Navigation apple, OpenObject fridge, SliceObject apple, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject butterknife microwave\nVisible objects are applesliced, microwave, butterknife, sink\nNext Plans: CloseObject microwave, Navigation fridge, OpenObject fridge, PickupObject applesliced, CloseObject fridge, Navigation sinkbasin, PutObject applesliced sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject applesliced, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, CloseObject microwave\n\nTask description: If there are apples on the table, wash them clean and bring them over.\nCompleted plans: \nVisible objects are apple, bellpepper, bench, book, bookshelf, box, candybar, ceiling, ceilinglamp, cereal, chips, chocolatesyrup, clock, coffeemaker, crackers, creamybuns, cutleryfork, cutleryknife, dishbowl, dishwashingliquid, door, faucet, floor, fridge, fryingpan, garbagecan, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, lightswitch, microwave, orchid, photoframe, pie, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tv, tvstand, wall, walllamp, wallphone, wallpictureframe, wallshelf, washingsponge, waterglass, whippedcream, wineglass\nNext Plans:",
  "raw_output": "Navigation kitchentable, PickupObject apple, Navigation sink, OpenObject sink, ToggleObjectOn faucet, ToggleObjectOff faucet, CloseObject sink, Navigation kitchentable, PutObject apple kitchentable",
  "parsed_plan": [
    [
      "Navigation",
      "kitchentable"
    ],
    [
      "PickupObject",
      "apple"
    ],
    [
      "Navigation",
      "sink"
    ],
    [
      "OpenObject",
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
      "CloseObject",
      "sink"
    ],
    [
      "Navigation",
      "kitchentable"
    ],
    [
      "PutObject",
      "apple",
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
- **Task Progress**: G1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 1
- **Action**: `[walk] <apple> (437)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 2
- **Action**: `[grab] <apple> (437)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 3
- **Action**: `[walk] <sink> (247)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 4
- **Action**: `[open] <sink> (247)`
- **Action Success**: `False`
- **Action Message**: {'0': {'message': 'ScriptExcutor 0: EXECUTION_GENERAL: Script is impossible to execute\n\n'}}
- **Task Progress**: G1_02=pending
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
    "apple",
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
      "kitchentable"
    ]
  ],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put cold apple on a table. \nCompleted plans: Navigation diningtable, PickupObject knife, Navigation apple, OpenObject microwave\nVisible objects are fridge, knife, diningtable, applesliced\nNext Plans: SliceObject apple, CloseObject microwave, Navigation diningtable, PutObject knife diningtable, Navigation microwave, OpenObject microwave, PickupObject applesliced, CloseObject microwave, Navigation fridge, OpenObject fridge, PutObject applesliced fridge, CloseObject fridge, OpenObject fridge, PickupObject applesliced, CloseObject fridge, Navigation diningtable, PutObject applesliced diningtable\n\nTask description: Put the apple slice in the trash.\nCompleted plans: Navigation countertop, PickupObject apple\nVisible objects are applesliced, fridge, garbagecan, apple, butterknife, countertop\nNext Plans: Navigation countertop, PutObject apple countertop, PickupObject butterknife, SliceObject apple, PutObject butterknife countertop, PickupObject applesliced, Navigation fridge, OpenObject fridge, PutObject applesliced fridge, CloseObject fridge, OpenObject fridge, PickupObject applesliced, CloseObject fridge, Navigation garbagecan, PutObject applesliced garbagecan\n\nTask description: Put cooked apple on a counter.\nCompleted plans: Navigation garbagecan, PickupObject apple, Navigation countertop, PutObject apple countertop, PickupObject butterknife, SliceObject apple, PutObject butterknife countertop, PickupObject applesliced\nVisible objects are applesliced, countertop, microwave, butterknife, apple\nNext Plans: Navigation microwave, OpenObject microwave, PutObject applesliced microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject applesliced, CloseObject microwave, Navigation countertop, PutObject applesliced countertop\n\nTask description: Place an apple slice on the table.\nCompleted plans: Navigation diningtable\nVisible objects are plate, applesliced, knife, diningtable\nNext Plans: PickupObject knife, Navigation apple, SliceObject apple, Navigation diningtable, PutObject knife diningtable, Navigation diningtable, PickupObject applesliced, Navigation plate, PutObject applesliced plate, PickupObject plate, Navigation diningtable, PutObject plate diningtable\n\nTask description: To heat a piece of apple and place it on the edge of the white table.\nCompleted plans: Navigation diningtable, PickupObject butterknife, Navigation apple, OpenObject fridge, SliceObject apple, PutObject butterknife fridge, PickupObject applesliced, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave\nVisible objects are applesliced, fridge, microwave, butterknife, diningtable\nNext Plans: PickupObject applesliced, CloseObject microwave, Navigation diningtable, PutObject applesliced diningtable\n\nTask description: Put a pot with a piece of apple in it on a table.\nCompleted plans: Navigation countertop, PickupObject knife, Navigation apple, OpenObject fridge, SliceObject apple, CloseObject fridge, Navigation diningtable, PutObject knife diningtable, Navigation fridge, OpenObject fridge, PickupObject applesliced, CloseObject fridge, Navigation pot, PutObject applesliced pot\nVisible objects are pot, knife, diningtable, applesliced\nNext Plans: PickupObject pot, Navigation diningtable, PutObject pot diningtable\n\nTask description: Carry a knife to cut the yellow apple in the fridge\nCompleted plans: Navigation countertop, PickupObject knife, Navigation apple\nVisible objects are \nNext Plans: OpenObject fridge, SliceObject apple, CloseObject fridge\n\nTask description: Place two apple slices and a knife in the microwave\nCompleted plans: Navigation countertop, PickupObject butterknife, Navigation apple, SliceObject apple, Navigation microwave, OpenObject microwave, PutObject butterknife microwave, CloseObject microwave, Navigation diningtable, PickupObject applesliced, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, PickupObject butterknife, CloseObject microwave, Navigation apple, SliceObject apple, Navigation microwave, OpenObject microwave, PutObject butterknife microwave\nVisible objects are applesliced, microwave, butterknife\nNext Plans: CloseObject microwave, Navigation sidetable, PickupObject applesliced, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, CloseObject microwave\n\nTask description: Put washed apple piece inside the microwave next to the gray knife.\nCompleted plans: Navigation countertop, PickupObject butterknife, Navigation apple, OpenObject fridge, SliceObject apple, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject butterknife microwave, CloseObject microwave, Navigation fridge, OpenObject fridge\nVisible objects are applesliced, microwave, butterknife, sink\nNext Plans: PickupObject applesliced, CloseObject fridge, Navigation sinkbasin, PutObject applesliced sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject applesliced, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, CloseObject microwave\n\nTask description: If there are apples on the table, wash them clean and bring them over.\nCompleted plans: Navigation kitchentable\nVisible objects are apple, bellpepper, bench, book, bookshelf, box, candybar, ceiling, ceilinglamp, cereal, chips, chocolatesyrup, clock, coffeemaker, crackers, creamybuns, cutleryfork, cutleryknife, dishbowl, dishwashingliquid, door, faucet, floor, fridge, fryingpan, garbagecan, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, lightswitch, microwave, orchid, photoframe, pie, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tv, tvstand, wall, walllamp, wallphone, wallpictureframe, wallshelf, washingsponge, waterglass, whippedcream, wineglass\nNext Plans:",
  "raw_output": "Navigation apple, PickupObject apple, Navigation sink, OpenObject fridge, CloseObject fridge",
  "parsed_plan": [
    [
      "Navigation",
      "apple"
    ],
    [
      "PickupObject",
      "apple"
    ],
    [
      "Navigation",
      "sink"
    ],
    [
      "OpenObject",
      "fridge"
    ],
    [
      "CloseObject",
      "fridge"
    ]
  ],
  "replan_count": 2,
  "reason": "previous action failed: [open] <sink> (247)"
}
```
## Step 5
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: G1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 6
- **Action**: `[grab] <apple> (437)`
- **Action Success**: `False`
- **Action Message**: {'0': {'message': 'ScriptExcutor 0: EXECUTION_GENERAL: Script is impossible to execute\n\n'}}
- **Task Progress**: G1_02=pending
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
    "apple",
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
      "kitchentable"
    ],
    [
      "Navigation",
      "apple"
    ]
  ],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put cold apple on a table. \nCompleted plans: Navigation diningtable\nVisible objects are fridge, knife, diningtable, applesliced\nNext Plans: PickupObject knife, Navigation apple, OpenObject microwave, SliceObject apple, CloseObject microwave, Navigation diningtable, PutObject knife diningtable, Navigation microwave, OpenObject microwave, PickupObject applesliced, CloseObject microwave, Navigation fridge, OpenObject fridge, PutObject applesliced fridge, CloseObject fridge, OpenObject fridge, PickupObject applesliced, CloseObject fridge, Navigation diningtable, PutObject applesliced diningtable\n\nTask description: Put the apple slice in the trash.\nCompleted plans: Navigation countertop, PickupObject apple\nVisible objects are applesliced, fridge, garbagecan, apple, butterknife, countertop\nNext Plans: Navigation countertop, PutObject apple countertop, PickupObject butterknife, SliceObject apple, PutObject butterknife countertop, PickupObject applesliced, Navigation fridge, OpenObject fridge, PutObject applesliced fridge, CloseObject fridge, OpenObject fridge, PickupObject applesliced, CloseObject fridge, Navigation garbagecan, PutObject applesliced garbagecan\n\nTask description: Put cooked apple on a counter.\nCompleted plans: Navigation garbagecan, PickupObject apple\nVisible objects are applesliced, countertop, microwave, butterknife, apple\nNext Plans: Navigation countertop, PutObject apple countertop, PickupObject butterknife, SliceObject apple, PutObject butterknife countertop, PickupObject applesliced, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject applesliced, CloseObject microwave, Navigation countertop, PutObject applesliced countertop\n\nTask description: Place an apple slice on the table.\nCompleted plans: Navigation diningtable, PickupObject knife, Navigation apple, SliceObject apple, Navigation diningtable\nVisible objects are plate, applesliced, knife, diningtable\nNext Plans: PutObject knife diningtable, Navigation diningtable, PickupObject applesliced, Navigation plate, PutObject applesliced plate, PickupObject plate, Navigation diningtable, PutObject plate diningtable\n\nTask description: To heat a piece of apple and place it on the edge of the white table.\nCompleted plans: Navigation diningtable, PickupObject butterknife, Navigation apple, OpenObject fridge, SliceObject apple\nVisible objects are applesliced, fridge, microwave, butterknife, diningtable\nNext Plans: PutObject butterknife fridge, PickupObject applesliced, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject applesliced, CloseObject microwave, Navigation diningtable, PutObject applesliced diningtable\n\nTask description: Put a pot with a piece of apple in it on a table.\nCompleted plans: Navigation countertop, PickupObject knife, Navigation apple, OpenObject fridge, SliceObject apple, CloseObject fridge, Navigation diningtable, PutObject knife diningtable, Navigation fridge\nVisible objects are pot, knife, diningtable, applesliced\nNext Plans: OpenObject fridge, PickupObject applesliced, CloseObject fridge, Navigation pot, PutObject applesliced pot, PickupObject pot, Navigation diningtable, PutObject pot diningtable\n\nTask description: Carry a knife to cut the yellow apple in the fridge\nCompleted plans: Navigation countertop, PickupObject knife\nVisible objects are \nNext Plans: Navigation apple, OpenObject fridge, SliceObject apple, CloseObject fridge\n\nTask description: Place two apple slices and a knife in the microwave\nCompleted plans: Navigation countertop, PickupObject butterknife, Navigation apple, SliceObject apple, Navigation microwave, OpenObject microwave, PutObject butterknife microwave, CloseObject microwave, Navigation diningtable, PickupObject applesliced, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, PickupObject butterknife, CloseObject microwave, Navigation apple, SliceObject apple, Navigation microwave, OpenObject microwave\nVisible objects are applesliced, microwave, butterknife\nNext Plans: PutObject butterknife microwave, CloseObject microwave, Navigation sidetable, PickupObject applesliced, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, CloseObject microwave\n\nTask description: Put washed apple piece inside the microwave next to the gray knife.\nCompleted plans: Navigation countertop, PickupObject butterknife, Navigation apple, OpenObject fridge, SliceObject apple, CloseObject fridge\nVisible objects are applesliced, microwave, butterknife, sink\nNext Plans: Navigation microwave, OpenObject microwave, PutObject butterknife microwave, CloseObject microwave, Navigation fridge, OpenObject fridge, PickupObject applesliced, CloseObject fridge, Navigation sinkbasin, PutObject applesliced sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject applesliced, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, CloseObject microwave\n\nTask description: If there are apples on the table, wash them clean and bring them over.\nCompleted plans: Navigation kitchentable, Navigation apple\nVisible objects are apple, bellpepper, bench, book, bookshelf, box, candybar, ceiling, ceilinglamp, cereal, chips, chocolatesyrup, clock, coffeemaker, crackers, creamybuns, cutleryfork, cutleryknife, dishbowl, dishwashingliquid, door, faucet, floor, fridge, fryingpan, garbagecan, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, lightswitch, microwave, orchid, photoframe, pie, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tv, tvstand, wall, walllamp, wallphone, wallpictureframe, wallshelf, washingsponge, waterglass, whippedcream, wineglass\nNext Plans:",
  "raw_output": "PickupObject apple, Navigation sink, PutObject apple sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject apple, Navigation kitchentable, PutObject apple kitchentable",
  "parsed_plan": [
    [
      "PickupObject",
      "apple"
    ],
    [
      "Navigation",
      "sink"
    ],
    [
      "PutObject",
      "apple",
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
      "apple"
    ],
    [
      "Navigation",
      "kitchentable"
    ],
    [
      "PutObject",
      "apple",
      "kitchentable"
    ]
  ],
  "replan_count": 3,
  "reason": "previous action failed: [grab] <apple> (437)"
}
```
## Step 7
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: G1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 8
- **Action**: `[grab] <apple> (437)`
- **Action Success**: `False`
- **Action Message**: {'0': {'message': 'ScriptExcutor 0: EXECUTION_GENERAL: Script is impossible to execute\n\n'}}
- **Task Progress**: G1_02=pending
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
    "apple",
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
      "kitchentable"
    ],
    [
      "Navigation",
      "apple"
    ]
  ],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put cold apple on a table. \nCompleted plans: Navigation diningtable, PickupObject knife, Navigation apple, OpenObject microwave, SliceObject apple, CloseObject microwave, Navigation diningtable\nVisible objects are fridge, knife, diningtable, applesliced\nNext Plans: PutObject knife diningtable, Navigation microwave, OpenObject microwave, PickupObject applesliced, CloseObject microwave, Navigation fridge, OpenObject fridge, PutObject applesliced fridge, CloseObject fridge, OpenObject fridge, PickupObject applesliced, CloseObject fridge, Navigation diningtable, PutObject applesliced diningtable\n\nTask description: Put the apple slice in the trash.\nCompleted plans: Navigation countertop, PickupObject apple, Navigation countertop, PutObject apple countertop\nVisible objects are applesliced, fridge, garbagecan, apple, butterknife, countertop\nNext Plans: PickupObject butterknife, SliceObject apple, PutObject butterknife countertop, PickupObject applesliced, Navigation fridge, OpenObject fridge, PutObject applesliced fridge, CloseObject fridge, OpenObject fridge, PickupObject applesliced, CloseObject fridge, Navigation garbagecan, PutObject applesliced garbagecan\n\nTask description: Put cooked apple on a counter.\nCompleted plans: Navigation garbagecan, PickupObject apple, Navigation countertop, PutObject apple countertop, PickupObject butterknife, SliceObject apple, PutObject butterknife countertop, PickupObject applesliced, Navigation microwave, OpenObject microwave, PutObject applesliced microwave\nVisible objects are applesliced, countertop, microwave, butterknife, apple\nNext Plans: CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject applesliced, CloseObject microwave, Navigation countertop, PutObject applesliced countertop\n\nTask description: Place an apple slice on the table.\nCompleted plans: Navigation diningtable, PickupObject knife, Navigation apple, SliceObject apple, Navigation diningtable, PutObject knife diningtable, Navigation diningtable, PickupObject applesliced, Navigation plate\nVisible objects are plate, applesliced, knife, diningtable\nNext Plans: PutObject applesliced plate, PickupObject plate, Navigation diningtable, PutObject plate diningtable\n\nTask description: To heat a piece of apple and place it on the edge of the white table.\nCompleted plans: Navigation diningtable, PickupObject butterknife, Navigation apple, OpenObject fridge, SliceObject apple, PutObject butterknife fridge, PickupObject applesliced, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave\nVisible objects are applesliced, fridge, microwave, butterknife, diningtable\nNext Plans: PickupObject applesliced, CloseObject microwave, Navigation diningtable, PutObject applesliced diningtable\n\nTask description: Put a pot with a piece of apple in it on a table.\nCompleted plans: Navigation countertop, PickupObject knife\nVisible objects are pot, knife, diningtable, applesliced\nNext Plans: Navigation apple, OpenObject fridge, SliceObject apple, CloseObject fridge, Navigation diningtable, PutObject knife diningtable, Navigation fridge, OpenObject fridge, PickupObject applesliced, CloseObject fridge, Navigation pot, PutObject applesliced pot, PickupObject pot, Navigation diningtable, PutObject pot diningtable\n\nTask description: Carry a knife to cut the yellow apple in the fridge\nCompleted plans: Navigation countertop, PickupObject knife, Navigation apple, OpenObject fridge\nVisible objects are \nNext Plans: SliceObject apple, CloseObject fridge\n\nTask description: Place two apple slices and a knife in the microwave\nCompleted plans: \nVisible objects are applesliced, microwave, butterknife\nNext Plans: Navigation countertop, PickupObject butterknife, Navigation apple, SliceObject apple, Navigation microwave, OpenObject microwave, PutObject butterknife microwave, CloseObject microwave, Navigation diningtable, PickupObject applesliced, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, PickupObject butterknife, CloseObject microwave, Navigation apple, SliceObject apple, Navigation microwave, OpenObject microwave, PutObject butterknife microwave, CloseObject microwave, Navigation sidetable, PickupObject applesliced, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, CloseObject microwave\n\nTask description: Put washed apple piece inside the microwave next to the gray knife.\nCompleted plans: Navigation countertop, PickupObject butterknife, Navigation apple, OpenObject fridge, SliceObject apple, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject butterknife microwave, CloseObject microwave, Navigation fridge, OpenObject fridge, PickupObject applesliced, CloseObject fridge, Navigation sinkbasin\nVisible objects are applesliced, microwave, butterknife, sink\nNext Plans: PutObject applesliced sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject applesliced, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, CloseObject microwave\n\nTask description: If there are apples on the table, wash them clean and bring them over.\nCompleted plans: Navigation kitchentable, Navigation apple\nVisible objects are apple, bellpepper, bench, book, bookshelf, box, candybar, ceiling, ceilinglamp, cereal, chips, chocolatesyrup, clock, coffeemaker, crackers, creamybuns, cutleryfork, cutleryknife, dishbowl, dishwashingliquid, door, faucet, floor, fridge, fryingpan, garbagecan, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, lightswitch, microwave, orchid, photoframe, pie, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tv, tvstand, wall, walllamp, wallphone, wallpictureframe, wallshelf, washingsponge, waterglass, whippedcream, wineglass\nNext Plans:",
  "raw_output": "OpenObject fridge, PickupObject apple, CloseObject fridge, Navigation diningtable, PutObject apple diningtable",
  "parsed_plan": [
    [
      "OpenObject",
      "fridge"
    ],
    [
      "PickupObject",
      "apple"
    ],
    [
      "CloseObject",
      "fridge"
    ],
    [
      "Navigation",
      "diningtable"
    ],
    [
      "PutObject",
      "apple",
      "diningtable"
    ]
  ],
  "replan_count": 4,
  "reason": "previous action failed: [grab] <apple> (437)"
}
```
## Step 9
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: G1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 10
- **Action**: `[walk] <fridge> (305)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 11
- **Action**: `[open] <fridge> (305)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 12
- **Action**: `[grab] <apple> (437)`
- **Action Success**: `False`
- **Action Message**: {'0': {'message': 'ScriptExcutor 0: EXECUTION_GENERAL: Script is impossible to execute\n\n'}}
- **Task Progress**: G1_02=pending
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
    "apple",
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
      "kitchentable"
    ],
    [
      "Navigation",
      "apple"
    ]
  ],
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put cold apple on a table. \nCompleted plans: Navigation diningtable, PickupObject knife, Navigation apple, OpenObject microwave, SliceObject apple, CloseObject microwave, Navigation diningtable\nVisible objects are fridge, knife, diningtable, applesliced\nNext Plans: PutObject knife diningtable, Navigation microwave, OpenObject microwave, PickupObject applesliced, CloseObject microwave, Navigation fridge, OpenObject fridge, PutObject applesliced fridge, CloseObject fridge, OpenObject fridge, PickupObject applesliced, CloseObject fridge, Navigation diningtable, PutObject applesliced diningtable\n\nTask description: Put the apple slice in the trash.\nCompleted plans: Navigation countertop, PickupObject apple, Navigation countertop, PutObject apple countertop, PickupObject butterknife, SliceObject apple, PutObject butterknife countertop, PickupObject applesliced, Navigation fridge\nVisible objects are applesliced, fridge, garbagecan, apple, butterknife, countertop\nNext Plans: OpenObject fridge, PutObject applesliced fridge, CloseObject fridge, OpenObject fridge, PickupObject applesliced, CloseObject fridge, Navigation garbagecan, PutObject applesliced garbagecan\n\nTask description: Put cooked apple on a counter.\nCompleted plans: Navigation garbagecan, PickupObject apple, Navigation countertop\nVisible objects are applesliced, countertop, microwave, butterknife, apple\nNext Plans: PutObject apple countertop, PickupObject butterknife, SliceObject apple, PutObject butterknife countertop, PickupObject applesliced, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, CloseObject microwave, ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject applesliced, CloseObject microwave, Navigation countertop, PutObject applesliced countertop\n\nTask description: Place an apple slice on the table.\nCompleted plans: Navigation diningtable, PickupObject knife, Navigation apple, SliceObject apple, Navigation diningtable, PutObject knife diningtable, Navigation diningtable, PickupObject applesliced, Navigation plate, PutObject applesliced plate, PickupObject plate\nVisible objects are plate, applesliced, knife, diningtable\nNext Plans: Navigation diningtable, PutObject plate diningtable\n\nTask description: To heat a piece of apple and place it on the edge of the white table.\nCompleted plans: Navigation diningtable, PickupObject butterknife, Navigation apple, OpenObject fridge, SliceObject apple, PutObject butterknife fridge, PickupObject applesliced, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, CloseObject microwave\nVisible objects are applesliced, fridge, microwave, butterknife, diningtable\nNext Plans: ToggleObjectOn microwave, ToggleObjectOff microwave, OpenObject microwave, PickupObject applesliced, CloseObject microwave, Navigation diningtable, PutObject applesliced diningtable\n\nTask description: Put a pot with a piece of apple in it on a table.\nCompleted plans: Navigation countertop, PickupObject knife, Navigation apple, OpenObject fridge, SliceObject apple, CloseObject fridge, Navigation diningtable, PutObject knife diningtable, Navigation fridge, OpenObject fridge, PickupObject applesliced, CloseObject fridge, Navigation pot, PutObject applesliced pot, PickupObject pot\nVisible objects are pot, knife, diningtable, applesliced\nNext Plans: Navigation diningtable, PutObject pot diningtable\n\nTask description: Carry a knife to cut the yellow apple in the fridge\nCompleted plans: Navigation countertop\nVisible objects are \nNext Plans: PickupObject knife, Navigation apple, OpenObject fridge, SliceObject apple, CloseObject fridge\n\nTask description: Place two apple slices and a knife in the microwave\nCompleted plans: Navigation countertop, PickupObject butterknife\nVisible objects are applesliced, microwave, butterknife\nNext Plans: Navigation apple, SliceObject apple, Navigation microwave, OpenObject microwave, PutObject butterknife microwave, CloseObject microwave, Navigation diningtable, PickupObject applesliced, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, PickupObject butterknife, CloseObject microwave, Navigation apple, SliceObject apple, Navigation microwave, OpenObject microwave, PutObject butterknife microwave, CloseObject microwave, Navigation sidetable, PickupObject applesliced, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, CloseObject microwave\n\nTask description: Put washed apple piece inside the microwave next to the gray knife.\nCompleted plans: Navigation countertop, PickupObject butterknife\nVisible objects are applesliced, microwave, butterknife, sink\nNext Plans: Navigation apple, OpenObject fridge, SliceObject apple, CloseObject fridge, Navigation microwave, OpenObject microwave, PutObject butterknife microwave, CloseObject microwave, Navigation fridge, OpenObject fridge, PickupObject applesliced, CloseObject fridge, Navigation sinkbasin, PutObject applesliced sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject applesliced, Navigation microwave, OpenObject microwave, PutObject applesliced microwave, CloseObject microwave\n\nTask description: If there are apples on the table, wash them clean and bring them over.\nCompleted plans: Navigation kitchentable, Navigation apple\nVisible objects are apple, bellpepper, bench, book, bookshelf, box, candybar, ceiling, ceilinglamp, cereal, chips, chocolatesyrup, clock, coffeemaker, crackers, creamybuns, cutleryfork, cutleryknife, dishbowl, dishwashingliquid, door, faucet, floor, fridge, fryingpan, garbagecan, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, lightswitch, microwave, orchid, photoframe, pie, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tv, tvstand, wall, walllamp, wallphone, wallpictureframe, wallshelf, washingsponge, waterglass, whippedcream, wineglass\nNext Plans:",
  "raw_output": "PickupObject apple, Navigation sink, PutObject apple sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject apple, Navigation diningtable, PutObject apple diningtable",
  "parsed_plan": [
    [
      "PickupObject",
      "apple"
    ],
    [
      "Navigation",
      "sink"
    ],
    [
      "PutObject",
      "apple",
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
      "apple"
    ],
    [
      "Navigation",
      "diningtable"
    ],
    [
      "PutObject",
      "apple",
      "diningtable"
    ]
  ],
  "replan_count": 5,
  "reason": "previous action failed: [grab] <apple> (437)"
}
```
## Step 13
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: G1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 14
- **Action**: `[grab] <apple> (437)`
- **Action Success**: `False`
- **Action Message**: {'0': {'message': 'ScriptExcutor 0: EXECUTION_GENERAL: Script is impossible to execute\n\n'}}
- **Task Progress**: G1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

