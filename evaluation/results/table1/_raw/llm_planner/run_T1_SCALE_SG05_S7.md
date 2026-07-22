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
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop, PickupObject winebottle, Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge\nVisible objects are fridge, cabinet, winebottle\nNext Plans: OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Put two candles in the drawer under the sink.\nCompleted plans: Navigation candle, PickupObject candle, Navigation drawer, OpenObject drawer, PutObject candle drawer, CloseObject drawer\nVisible objects are candle, drawer\nNext Plans: Navigation countertop, PickupObject candle, Navigation drawer, OpenObject drawer, PutObject candle drawer, CloseObject drawer\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: \nVisible objects are box, vase, diningtable\nNext Plans: Navigation cabinet, OpenObject cabinet, PickupObject vase, CloseObject cabinet, Navigation box, PutObject vase box, PickupObject box, Navigation diningtable, PutObject box diningtable\n\nTask description: Put watches on a shelf.\nCompleted plans: Navigation diningtable, PickupObject watch, Navigation shelf, PutObject watch shelf\nVisible objects are watch, shelf\nNext Plans: Navigation diningtable, PickupObject watch, Navigation shelf, PutObject watch shelf\n\nTask description: Place a box with the credit card on the blue sofa chair.\nCompleted plans: Navigation box, PickupObject box, Navigation armchair, PutObject box armchair, Navigation coffeetable, PickupObject creditcard, Navigation box, PutObject creditcard box\nVisible objects are box, creditcard, armchair\nNext Plans: CloseObject box\n\nTask description: To move the CD from the drawer to the safe.\nCompleted plans: Navigation drawer, OpenObject drawer, PickupObject cd, CloseObject drawer, Navigation safe, OpenObject safe, PutObject cd safe\nVisible objects are safe, cd\nNext Plans: CloseObject safe\n\nTask description: Move a laptop from a coffee table to an armchair.\nCompleted plans: Navigation coffeetable, CloseObject laptop, PickupObject laptop\nVisible objects are armchair, laptop\nNext Plans: Navigation armchair, PutObject laptop armchair\n\nTask description: Place the wine bottle in the fridge to put it in the trash can.\nCompleted plans: Navigation countertop, PickupObject winebottle, Navigation fridge, OpenObject fridge\nVisible objects are fridge, garbagecan, winebottle\nNext Plans: PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation garbagecan, PutObject winebottle garbagecan\n\nTask description: Wash the soap that you found in the cabinet and place it back in the cabinet\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject soapbar, PutObject soapbar sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject soapbar\nVisible objects are cabinet, sink, soapbar\nNext Plans: Navigation cabinet, PutObject soapbar cabinet, CloseObject cabinet\n\nTask description: 1. If there is water in the mug, pour it out and put the mug in the cabinet.\n2. If no one is watching the TV, turn it on.\n3. If you see a book somewhere unorganized, bring it to the sofa.\n4. If your computer stays off, turn it on.\n5. Put the folder in the closet.\n6. If the radio is off, turn it on\n7. If you have an apple somewhere, bring it to your desk.\nCompleted plans: \nVisible objects are apple, bellpepper, bench, book, bookshelf, box, candybar, ceiling, ceilinglamp, cereal, chips, chocolatesyrup, clock, coffeemaker, crackers, creamybuns, cutleryfork, cutleryknife, dishbowl, dishwashingliquid, door, faucet, floor, fridge, fryingpan, garbagecan, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, lightswitch, microwave, mug, orchid, photoframe, pie, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tv, tvstand, wall, walllamp, wallphone, wallpictureframe, wallshelf, washingsponge, waterglass, whippedcream, wineglass\nNext Plans:",
  "raw_output": "Navigation mug, OpenObject kitchencabinet, PickupObject mug, CloseObject kitchencabinet, Navigation tv, ToggleObjectOn tv, Navigation book, PickupObject book, Navigation sofa, PutObject book sofa, Navigation powersocket, ToggleObjectOn powersocket, Navigation folder, PickupObject folder, Navigation closet, PutObject folder closet, Navigation radio, ToggleObjectOn radio, Navigation apple, PickupObject apple, Navigation desk, PutObject apple desk",
  "parsed_plan": [
    [
      "Navigation",
      "mug"
    ],
    [
      "OpenObject",
      "kitchencabinet"
    ],
    [
      "PickupObject",
      "mug"
    ],
    [
      "CloseObject",
      "kitchencabinet"
    ],
    [
      "Navigation",
      "tv"
    ],
    [
      "ToggleObjectOn",
      "tv"
    ],
    [
      "Navigation",
      "book"
    ],
    [
      "PickupObject",
      "book"
    ],
    [
      "Navigation",
      "sofa"
    ],
    [
      "PutObject",
      "book",
      "sofa"
    ],
    [
      "Navigation",
      "powersocket"
    ],
    [
      "ToggleObjectOn",
      "powersocket"
    ],
    [
      "Navigation",
      "folder"
    ],
    [
      "PickupObject",
      "folder"
    ],
    [
      "Navigation",
      "closet"
    ],
    [
      "PutObject",
      "folder",
      "closet"
    ],
    [
      "Navigation",
      "radio"
    ],
    [
      "ToggleObjectOn",
      "radio"
    ],
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
      "desk"
    ],
    [
      "PutObject",
      "apple",
      "desk"
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
- **Task Progress**: G1_05=pending, E1_01=pending, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 1
- **Action**: `[walk] <mug> (194)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_05=pending, E1_01=pending, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 2
- **Action**: `[walk] <kitchencabinet> (234)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_05=pending, E1_01=pending, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 3
- **Action**: `[open] <kitchencabinet> (234)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_05=pending, E1_01=pending, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 4
- **Action**: `[walk] <mug> (194)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_05=pending, E1_01=pending, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 5
- **Action**: `[grab] <mug> (194)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_05=pending, E1_01=pending, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 6
- **Action**: `[walk] <kitchencabinet> (234)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_05=pending, E1_01=pending, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 7
- **Action**: `[close] <kitchencabinet> (234)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_05=pending, E1_01=pending, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 8
- **Action**: `[walk] <tv> (264)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_05=pending, E1_01=pending, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 9
- **Action**: `[switchon] <tv> (264)`
- **Action Success**: `True`
- **Action Message**: Faked switch operation in Python layer (bypassed Unity failure)
- **Task Progress**: G1_05=pending, E1_01=done, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 10
- **Action**: `[walk] <book> (268)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_05=pending, E1_01=done, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 11
- **Action**: `[grab] <book> (268)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_05=pending, E1_01=done, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
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
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop, PickupObject winebottle\nVisible objects are fridge, cabinet, winebottle\nNext Plans: Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Put two candles in the drawer under the sink.\nCompleted plans: Navigation candle, PickupObject candle, Navigation drawer, OpenObject drawer, PutObject candle drawer, CloseObject drawer, Navigation countertop, PickupObject candle, Navigation drawer\nVisible objects are candle, drawer\nNext Plans: OpenObject drawer, PutObject candle drawer, CloseObject drawer\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet\nVisible objects are box, vase, diningtable\nNext Plans: OpenObject cabinet, PickupObject vase, CloseObject cabinet, Navigation box, PutObject vase box, PickupObject box, Navigation diningtable, PutObject box diningtable\n\nTask description: Put watches on a shelf.\nCompleted plans: Navigation diningtable, PickupObject watch, Navigation shelf, PutObject watch shelf\nVisible objects are watch, shelf\nNext Plans: Navigation diningtable, PickupObject watch, Navigation shelf, PutObject watch shelf\n\nTask description: Place a box with the credit card on the blue sofa chair.\nCompleted plans: Navigation box\nVisible objects are box, creditcard, armchair\nNext Plans: PickupObject box, Navigation armchair, PutObject box armchair, Navigation coffeetable, PickupObject creditcard, Navigation box, PutObject creditcard box, CloseObject box\n\nTask description: To move the CD from the drawer to the safe.\nCompleted plans: Navigation drawer, OpenObject drawer, PickupObject cd, CloseObject drawer, Navigation safe, OpenObject safe, PutObject cd safe\nVisible objects are safe, cd\nNext Plans: CloseObject safe\n\nTask description: Move a laptop from a coffee table to an armchair.\nCompleted plans: Navigation coffeetable, CloseObject laptop, PickupObject laptop\nVisible objects are armchair, laptop\nNext Plans: Navigation armchair, PutObject laptop armchair\n\nTask description: Place the wine bottle in the fridge to put it in the trash can.\nCompleted plans: Navigation countertop, PickupObject winebottle, Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge\nVisible objects are fridge, garbagecan, winebottle\nNext Plans: PickupObject winebottle, CloseObject fridge, Navigation garbagecan, PutObject winebottle garbagecan\n\nTask description: Wash the soap that you found in the cabinet and place it back in the cabinet\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject soapbar, PutObject soapbar sink, ToggleObjectOn faucet, ToggleObjectOff faucet\nVisible objects are cabinet, sink, soapbar\nNext Plans: PickupObject soapbar, Navigation cabinet, PutObject soapbar cabinet, CloseObject cabinet\n\nTask description: 1. If there is water in the mug, pour it out and put the mug in the cabinet.\n2. If no one is watching the TV, turn it on.\n3. If you see a book somewhere unorganized, bring it to the sofa.\n4. If your computer stays off, turn it on.\n5. Put the folder in the closet.\n6. If the radio is off, turn it on\n7. If you have an apple somewhere, bring it to your desk.\nCompleted plans: \nVisible objects are apple, bellpepper, bench, book, bookshelf, box, candybar, ceiling, ceilinglamp, cereal, chips, chocolatesyrup, clock, coffeemaker, crackers, creamybuns, cutleryfork, cutleryknife, dishbowl, dishwashingliquid, door, faucet, floor, fridge, fryingpan, garbagecan, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, lightswitch, microwave, mug, orchid, photoframe, pie, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tv, tvstand, wall, walllamp, wallphone, wallpictureframe, wallshelf, washingsponge, waterglass, whippedcream, wineglass\nNext Plans:",
  "raw_output": "PickupObject mug, Navigation kitchencabinet, OpenObject kitchencabinet, PutObject mug kitchencabinet, CloseObject kitchencabinet, ToggleObjectOn tv, Navigation bookshelf, PickupObject book, Navigation sofa, PutObject book sofa, ToggleObjectOn computer, Navigation closet, OpenObject closet, PutObject folder closet, CloseObject closet, ToggleObjectOn radio, PickupObject apple, Navigation desk, PutObject apple desk",
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
    ],
    [
      "ToggleObjectOn",
      "tv"
    ],
    [
      "Navigation",
      "bookshelf"
    ],
    [
      "PickupObject",
      "book"
    ],
    [
      "Navigation",
      "sofa"
    ],
    [
      "PutObject",
      "book",
      "sofa"
    ],
    [
      "ToggleObjectOn",
      "computer"
    ],
    [
      "Navigation",
      "closet"
    ],
    [
      "OpenObject",
      "closet"
    ],
    [
      "PutObject",
      "folder",
      "closet"
    ],
    [
      "CloseObject",
      "closet"
    ],
    [
      "ToggleObjectOn",
      "radio"
    ],
    [
      "PickupObject",
      "apple"
    ],
    [
      "Navigation",
      "desk"
    ],
    [
      "PutObject",
      "apple",
      "desk"
    ]
  ],
  "replan_count": 2,
  "reason": "high-level skill failed: Navigation sofa; reason: Navigation target not found: sofa"
}
```
## Step 12
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: G1_05=pending, E1_01=done, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 13
- **Action**: `[grab] <mug> (194)`
- **Action Success**: `False`
- **Action Message**: {'0': {'message': 'ScriptExcutor 0: EXECUTION_GENERAL: Script is impossible to execute\n\n'}}
- **Task Progress**: G1_05=pending, E1_01=done, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
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
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: \nVisible objects are fridge, cabinet, winebottle\nNext Plans: Navigation countertop, PickupObject winebottle, Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Put two candles in the drawer under the sink.\nCompleted plans: Navigation candle\nVisible objects are candle, drawer\nNext Plans: PickupObject candle, Navigation drawer, OpenObject drawer, PutObject candle drawer, CloseObject drawer, Navigation countertop, PickupObject candle, Navigation drawer, OpenObject drawer, PutObject candle drawer, CloseObject drawer\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet\nVisible objects are box, vase, diningtable\nNext Plans: OpenObject cabinet, PickupObject vase, CloseObject cabinet, Navigation box, PutObject vase box, PickupObject box, Navigation diningtable, PutObject box diningtable\n\nTask description: Put watches on a shelf.\nCompleted plans: Navigation diningtable, PickupObject watch, Navigation shelf, PutObject watch shelf, Navigation diningtable\nVisible objects are watch, shelf\nNext Plans: PickupObject watch, Navigation shelf, PutObject watch shelf\n\nTask description: Place a box with the credit card on the blue sofa chair.\nCompleted plans: Navigation box, PickupObject box\nVisible objects are box, creditcard, armchair\nNext Plans: Navigation armchair, PutObject box armchair, Navigation coffeetable, PickupObject creditcard, Navigation box, PutObject creditcard box, CloseObject box\n\nTask description: To move the CD from the drawer to the safe.\nCompleted plans: Navigation drawer, OpenObject drawer, PickupObject cd, CloseObject drawer\nVisible objects are safe, cd\nNext Plans: Navigation safe, OpenObject safe, PutObject cd safe, CloseObject safe\n\nTask description: Move a laptop from a coffee table to an armchair.\nCompleted plans: Navigation coffeetable, CloseObject laptop\nVisible objects are armchair, laptop\nNext Plans: PickupObject laptop, Navigation armchair, PutObject laptop armchair\n\nTask description: Place the wine bottle in the fridge to put it in the trash can.\nCompleted plans: Navigation countertop, PickupObject winebottle, Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge\nVisible objects are fridge, garbagecan, winebottle\nNext Plans: Navigation garbagecan, PutObject winebottle garbagecan\n\nTask description: Wash the soap that you found in the cabinet and place it back in the cabinet\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject soapbar\nVisible objects are cabinet, sink, soapbar\nNext Plans: PutObject soapbar sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject soapbar, Navigation cabinet, PutObject soapbar cabinet, CloseObject cabinet\n\nTask description: 1. If there is water in the mug, pour it out and put the mug in the cabinet.\n2. If no one is watching the TV, turn it on.\n3. If you see a book somewhere unorganized, bring it to the sofa.\n4. If your computer stays off, turn it on.\n5. Put the folder in the closet.\n6. If the radio is off, turn it on\n7. If you have an apple somewhere, bring it to your desk.\nCompleted plans: \nVisible objects are apple, bellpepper, bench, book, bookshelf, box, candybar, ceiling, ceilinglamp, cereal, chips, chocolatesyrup, clock, coffeemaker, crackers, creamybuns, cutleryfork, cutleryknife, dishbowl, dishwashingliquid, door, faucet, floor, fridge, fryingpan, garbagecan, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, lightswitch, microwave, mug, orchid, photoframe, pie, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tv, tvstand, wall, walllamp, wallphone, wallpictureframe, wallshelf, washingsponge, waterglass, whippedcream, wineglass\nNext Plans:",
  "raw_output": "PickupObject mug, Navigation sink, PutObject mug sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject mug, Navigation kitchencabinet, PutObject mug kitchencabinet, Navigation tv, ToggleObjectOn tv, PickupObject book, Navigation sofa, PutObject book sofa, Navigation laptop, ToggleObjectOn laptop, Navigation folder, PickupObject folder, Navigation closet, PutObject folder closet, Navigation radio, ToggleObjectOn radio, Navigation apple, PickupObject apple, Navigation desk, PutObject apple desk",
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
      "PutObject",
      "mug",
      "kitchencabinet"
    ],
    [
      "Navigation",
      "tv"
    ],
    [
      "ToggleObjectOn",
      "tv"
    ],
    [
      "PickupObject",
      "book"
    ],
    [
      "Navigation",
      "sofa"
    ],
    [
      "PutObject",
      "book",
      "sofa"
    ],
    [
      "Navigation",
      "laptop"
    ],
    [
      "ToggleObjectOn",
      "laptop"
    ],
    [
      "Navigation",
      "folder"
    ],
    [
      "PickupObject",
      "folder"
    ],
    [
      "Navigation",
      "closet"
    ],
    [
      "PutObject",
      "folder",
      "closet"
    ],
    [
      "Navigation",
      "radio"
    ],
    [
      "ToggleObjectOn",
      "radio"
    ],
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
      "desk"
    ],
    [
      "PutObject",
      "apple",
      "desk"
    ]
  ],
  "replan_count": 3,
  "reason": "previous action failed: [grab] <mug> (194)"
}
```
## Step 14
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: G1_05=pending, E1_01=done, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 15
- **Action**: `[grab] <mug> (194)`
- **Action Success**: `False`
- **Action Message**: {'0': {'message': 'ScriptExcutor 0: EXECUTION_GENERAL: Script is impossible to execute\n\n'}}
- **Task Progress**: G1_05=pending, E1_01=done, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
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
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop, PickupObject winebottle, Navigation fridge\nVisible objects are fridge, cabinet, winebottle\nNext Plans: OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Put two candles in the drawer under the sink.\nCompleted plans: Navigation candle, PickupObject candle, Navigation drawer, OpenObject drawer, PutObject candle drawer, CloseObject drawer, Navigation countertop, PickupObject candle, Navigation drawer\nVisible objects are candle, drawer\nNext Plans: OpenObject drawer, PutObject candle drawer, CloseObject drawer\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject vase, CloseObject cabinet, Navigation box, PutObject vase box, PickupObject box, Navigation diningtable\nVisible objects are box, vase, diningtable\nNext Plans: PutObject box diningtable\n\nTask description: Put watches on a shelf.\nCompleted plans: Navigation diningtable, PickupObject watch\nVisible objects are watch, shelf\nNext Plans: Navigation shelf, PutObject watch shelf, Navigation diningtable, PickupObject watch, Navigation shelf, PutObject watch shelf\n\nTask description: Place a box with the credit card on the blue sofa chair.\nCompleted plans: Navigation box, PickupObject box, Navigation armchair, PutObject box armchair, Navigation coffeetable\nVisible objects are box, creditcard, armchair\nNext Plans: PickupObject creditcard, Navigation box, PutObject creditcard box, CloseObject box\n\nTask description: To move the CD from the drawer to the safe.\nCompleted plans: Navigation drawer, OpenObject drawer, PickupObject cd, CloseObject drawer, Navigation safe, OpenObject safe, PutObject cd safe\nVisible objects are safe, cd\nNext Plans: CloseObject safe\n\nTask description: Move a laptop from a coffee table to an armchair.\nCompleted plans: Navigation coffeetable, CloseObject laptop, PickupObject laptop, Navigation armchair\nVisible objects are armchair, laptop\nNext Plans: PutObject laptop armchair\n\nTask description: Place the wine bottle in the fridge to put it in the trash can.\nCompleted plans: Navigation countertop\nVisible objects are fridge, garbagecan, winebottle\nNext Plans: PickupObject winebottle, Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation garbagecan, PutObject winebottle garbagecan\n\nTask description: Wash the soap that you found in the cabinet and place it back in the cabinet\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject soapbar, PutObject soapbar sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject soapbar, Navigation cabinet, PutObject soapbar cabinet\nVisible objects are cabinet, sink, soapbar\nNext Plans: CloseObject cabinet\n\nTask description: 1. If there is water in the mug, pour it out and put the mug in the cabinet.\n2. If no one is watching the TV, turn it on.\n3. If you see a book somewhere unorganized, bring it to the sofa.\n4. If your computer stays off, turn it on.\n5. Put the folder in the closet.\n6. If the radio is off, turn it on\n7. If you have an apple somewhere, bring it to your desk.\nCompleted plans: \nVisible objects are apple, bellpepper, bench, book, bookshelf, box, candybar, ceiling, ceilinglamp, cereal, chips, chocolatesyrup, clock, coffeemaker, crackers, creamybuns, cutleryfork, cutleryknife, dishbowl, dishwashingliquid, door, faucet, floor, fridge, fryingpan, garbagecan, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, lightswitch, microwave, mug, orchid, photoframe, pie, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tv, tvstand, wall, walllamp, wallphone, wallpictureframe, wallshelf, washingsponge, waterglass, whippedcream, wineglass\nNext Plans:",
  "raw_output": "Navigation mug, PickupObject mug, Navigation sink, OpenObject kitchencabinet, PutObject mug kitchencabinet, CloseObject kitchencabinet, ToggleObjectOn tv, Navigation book, PickupObject book, Navigation sofa, PutObject book sofa, Navigation computer, ToggleObjectOn computer, Navigation folder, PickupObject folder, Navigation closet, PutObject folder closet, Navigation radio, ToggleObjectOn radio, Navigation apple, PickupObject apple, Navigation desk, PutObject apple desk",
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
    ],
    [
      "ToggleObjectOn",
      "tv"
    ],
    [
      "Navigation",
      "book"
    ],
    [
      "PickupObject",
      "book"
    ],
    [
      "Navigation",
      "sofa"
    ],
    [
      "PutObject",
      "book",
      "sofa"
    ],
    [
      "Navigation",
      "computer"
    ],
    [
      "ToggleObjectOn",
      "computer"
    ],
    [
      "Navigation",
      "folder"
    ],
    [
      "PickupObject",
      "folder"
    ],
    [
      "Navigation",
      "closet"
    ],
    [
      "PutObject",
      "folder",
      "closet"
    ],
    [
      "Navigation",
      "radio"
    ],
    [
      "ToggleObjectOn",
      "radio"
    ],
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
      "desk"
    ],
    [
      "PutObject",
      "apple",
      "desk"
    ]
  ],
  "replan_count": 4,
  "reason": "previous action failed: [grab] <mug> (194)"
}
```
## Step 16
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: G1_05=pending, E1_01=done, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 17
- **Action**: `[grab] <mug> (194)`
- **Action Success**: `False`
- **Action Message**: {'0': {'message': 'ScriptExcutor 0: EXECUTION_GENERAL: Script is impossible to execute\n\n'}}
- **Task Progress**: G1_05=pending, E1_01=done, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
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
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop, PickupObject winebottle, Navigation fridge\nVisible objects are fridge, cabinet, winebottle\nNext Plans: OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Put two candles in the drawer under the sink.\nCompleted plans: Navigation candle, PickupObject candle, Navigation drawer, OpenObject drawer\nVisible objects are candle, drawer\nNext Plans: PutObject candle drawer, CloseObject drawer, Navigation countertop, PickupObject candle, Navigation drawer, OpenObject drawer, PutObject candle drawer, CloseObject drawer\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet\nVisible objects are box, vase, diningtable\nNext Plans: OpenObject cabinet, PickupObject vase, CloseObject cabinet, Navigation box, PutObject vase box, PickupObject box, Navigation diningtable, PutObject box diningtable\n\nTask description: Put watches on a shelf.\nCompleted plans: Navigation diningtable, PickupObject watch, Navigation shelf, PutObject watch shelf, Navigation diningtable, PickupObject watch\nVisible objects are watch, shelf\nNext Plans: Navigation shelf, PutObject watch shelf\n\nTask description: Place a box with the credit card on the blue sofa chair.\nCompleted plans: Navigation box, PickupObject box, Navigation armchair, PutObject box armchair, Navigation coffeetable, PickupObject creditcard, Navigation box\nVisible objects are box, creditcard, armchair\nNext Plans: PutObject creditcard box, CloseObject box\n\nTask description: To move the CD from the drawer to the safe.\nCompleted plans: Navigation drawer, OpenObject drawer\nVisible objects are safe, cd\nNext Plans: PickupObject cd, CloseObject drawer, Navigation safe, OpenObject safe, PutObject cd safe, CloseObject safe\n\nTask description: Move a laptop from a coffee table to an armchair.\nCompleted plans: \nVisible objects are armchair, laptop\nNext Plans: Navigation coffeetable, CloseObject laptop, PickupObject laptop, Navigation armchair, PutObject laptop armchair\n\nTask description: Place the wine bottle in the fridge to put it in the trash can.\nCompleted plans: Navigation countertop\nVisible objects are fridge, garbagecan, winebottle\nNext Plans: PickupObject winebottle, Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation garbagecan, PutObject winebottle garbagecan\n\nTask description: Wash the soap that you found in the cabinet and place it back in the cabinet\nCompleted plans: \nVisible objects are cabinet, sink, soapbar\nNext Plans: Navigation cabinet, OpenObject cabinet, PickupObject soapbar, PutObject soapbar sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject soapbar, Navigation cabinet, PutObject soapbar cabinet, CloseObject cabinet\n\nTask description: 1. If there is water in the mug, pour it out and put the mug in the cabinet.\n2. If no one is watching the TV, turn it on.\n3. If you see a book somewhere unorganized, bring it to the sofa.\n4. If your computer stays off, turn it on.\n5. Put the folder in the closet.\n6. If the radio is off, turn it on\n7. If you have an apple somewhere, bring it to your desk.\nCompleted plans: Navigation mug\nVisible objects are apple, bellpepper, bench, book, bookshelf, box, candybar, ceiling, ceilinglamp, cereal, chips, chocolatesyrup, clock, coffeemaker, crackers, creamybuns, cutleryfork, cutleryknife, dishbowl, dishwashingliquid, door, faucet, floor, fridge, fryingpan, garbagecan, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, lightswitch, microwave, mug, orchid, photoframe, pie, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tv, tvstand, wall, walllamp, wallphone, wallpictureframe, wallshelf, washingsponge, waterglass, whippedcream, wineglass\nNext Plans:",
  "raw_output": "PickupObject mug, Navigation sink, PutObject mug sink, ToggleObjectOn faucet, ToggleObjectOff faucet, Navigation kitchencabinet, OpenObject kitchencabinet, PutObject mug kitchencabinet, CloseObject kitchencabinet, ToggleObjectOn tv, Navigation bookshelf, PickupObject book, Navigation sofa, PutObject book sofa, ToggleObjectOn computer, Navigation closet, OpenObject closet, PickupObject folder, PutObject folder closet, CloseObject closet, ToggleObjectOn radio, PickupObject apple, Navigation desk, PutObject apple desk",
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
    ],
    [
      "ToggleObjectOn",
      "tv"
    ],
    [
      "Navigation",
      "bookshelf"
    ],
    [
      "PickupObject",
      "book"
    ],
    [
      "Navigation",
      "sofa"
    ],
    [
      "PutObject",
      "book",
      "sofa"
    ],
    [
      "ToggleObjectOn",
      "computer"
    ],
    [
      "Navigation",
      "closet"
    ],
    [
      "OpenObject",
      "closet"
    ],
    [
      "PickupObject",
      "folder"
    ],
    [
      "PutObject",
      "folder",
      "closet"
    ],
    [
      "CloseObject",
      "closet"
    ],
    [
      "ToggleObjectOn",
      "radio"
    ],
    [
      "PickupObject",
      "apple"
    ],
    [
      "Navigation",
      "desk"
    ],
    [
      "PutObject",
      "apple",
      "desk"
    ]
  ],
  "replan_count": 5,
  "reason": "previous action failed: [grab] <mug> (194)"
}
```
## Step 18
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: G1_05=pending, E1_01=done, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 19
- **Action**: `[grab] <mug> (194)`
- **Action Success**: `False`
- **Action Message**: {'0': {'message': 'ScriptExcutor 0: EXECUTION_GENERAL: Script is impossible to execute\n\n'}}
- **Task Progress**: G1_05=pending, E1_01=done, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
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
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop, PickupObject winebottle, Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge\nVisible objects are fridge, cabinet, winebottle\nNext Plans: Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet\n\nTask description: Put two candles in the drawer under the sink.\nCompleted plans: Navigation candle, PickupObject candle, Navigation drawer, OpenObject drawer\nVisible objects are candle, drawer\nNext Plans: PutObject candle drawer, CloseObject drawer, Navigation countertop, PickupObject candle, Navigation drawer, OpenObject drawer, PutObject candle drawer, CloseObject drawer\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject vase, CloseObject cabinet, Navigation box\nVisible objects are box, vase, diningtable\nNext Plans: PutObject vase box, PickupObject box, Navigation diningtable, PutObject box diningtable\n\nTask description: Put watches on a shelf.\nCompleted plans: \nVisible objects are watch, shelf\nNext Plans: Navigation diningtable, PickupObject watch, Navigation shelf, PutObject watch shelf, Navigation diningtable, PickupObject watch, Navigation shelf, PutObject watch shelf\n\nTask description: Place a box with the credit card on the blue sofa chair.\nCompleted plans: Navigation box, PickupObject box, Navigation armchair, PutObject box armchair, Navigation coffeetable, PickupObject creditcard, Navigation box\nVisible objects are box, creditcard, armchair\nNext Plans: PutObject creditcard box, CloseObject box\n\nTask description: To move the CD from the drawer to the safe.\nCompleted plans: Navigation drawer, OpenObject drawer, PickupObject cd\nVisible objects are safe, cd\nNext Plans: CloseObject drawer, Navigation safe, OpenObject safe, PutObject cd safe, CloseObject safe\n\nTask description: Move a laptop from a coffee table to an armchair.\nCompleted plans: \nVisible objects are armchair, laptop\nNext Plans: Navigation coffeetable, CloseObject laptop, PickupObject laptop, Navigation armchair, PutObject laptop armchair\n\nTask description: Place the wine bottle in the fridge to put it in the trash can.\nCompleted plans: Navigation countertop, PickupObject winebottle\nVisible objects are fridge, garbagecan, winebottle\nNext Plans: Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation garbagecan, PutObject winebottle garbagecan\n\nTask description: Wash the soap that you found in the cabinet and place it back in the cabinet\nCompleted plans: Navigation cabinet\nVisible objects are cabinet, sink, soapbar\nNext Plans: OpenObject cabinet, PickupObject soapbar, PutObject soapbar sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject soapbar, Navigation cabinet, PutObject soapbar cabinet, CloseObject cabinet\n\nTask description: 1. If there is water in the mug, pour it out and put the mug in the cabinet.\n2. If no one is watching the TV, turn it on.\n3. If you see a book somewhere unorganized, bring it to the sofa.\n4. If your computer stays off, turn it on.\n5. Put the folder in the closet.\n6. If the radio is off, turn it on\n7. If you have an apple somewhere, bring it to your desk.\nCompleted plans: Navigation mug\nVisible objects are apple, bellpepper, bench, book, bookshelf, box, candybar, ceiling, ceilinglamp, cereal, chips, chocolatesyrup, clock, coffeemaker, crackers, creamybuns, cutleryfork, cutleryknife, dishbowl, dishwashingliquid, door, faucet, floor, fridge, fryingpan, garbagecan, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, lightswitch, microwave, mug, orchid, photoframe, pie, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tv, tvstand, wall, walllamp, wallphone, wallpictureframe, wallshelf, washingsponge, waterglass, whippedcream, wineglass\nNext Plans:",
  "raw_output": "Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet, CloseObject cabinet",
  "parsed_plan": [
    [
      "Navigation",
      "cabinet"
    ],
    [
      "OpenObject",
      "cabinet"
    ],
    [
      "PutObject",
      "winebottle",
      "cabinet"
    ],
    [
      "CloseObject",
      "cabinet"
    ]
  ],
  "replan_count": 6,
  "reason": "previous action failed: [grab] <mug> (194)"
}
```
## Step 20
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: G1_05=pending, E1_01=done, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 21
- **Action**: `[walk] <kitchencabinet> (234)`
- **Action Success**: `True`
- **Action Message**: {'0': {'message': 'Success'}}
- **Task Progress**: G1_05=pending, E1_01=done, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 22
- **Action**: `[open] <kitchencabinet> (234)`
- **Action Success**: `False`
- **Action Message**: {'0': {'message': 'ScriptExcutor 0: EXECUTION_GENERAL: Script is impossible to execute\n\n'}}
- **Task Progress**: G1_05=pending, E1_01=done, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
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
  "prompt": "Create a high-level plan for completing a household task using the allowed actions and visible objects.\n\n\nAllowed actions: OpenObject, CloseObject, PickupObject, PutObject, ToggleObjectOn, ToggleObjectOff, SliceObject, Navigation\n\nTask description: Put a chilled bottle of wine in the cabinet.\nCompleted plans: Navigation countertop, PickupObject winebottle, Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation cabinet, OpenObject cabinet, PutObject winebottle cabinet\nVisible objects are fridge, cabinet, winebottle\nNext Plans: CloseObject cabinet\n\nTask description: Put two candles in the drawer under the sink.\nCompleted plans: Navigation candle, PickupObject candle, Navigation drawer, OpenObject drawer, PutObject candle drawer, CloseObject drawer, Navigation countertop, PickupObject candle, Navigation drawer\nVisible objects are candle, drawer\nNext Plans: OpenObject drawer, PutObject candle drawer, CloseObject drawer\n\nTask description: Place a box with a bottle on a table.\nCompleted plans: Navigation cabinet\nVisible objects are box, vase, diningtable\nNext Plans: OpenObject cabinet, PickupObject vase, CloseObject cabinet, Navigation box, PutObject vase box, PickupObject box, Navigation diningtable, PutObject box diningtable\n\nTask description: Put watches on a shelf.\nCompleted plans: Navigation diningtable, PickupObject watch, Navigation shelf, PutObject watch shelf, Navigation diningtable, PickupObject watch, Navigation shelf\nVisible objects are watch, shelf\nNext Plans: PutObject watch shelf\n\nTask description: Place a box with the credit card on the blue sofa chair.\nCompleted plans: Navigation box, PickupObject box, Navigation armchair, PutObject box armchair\nVisible objects are box, creditcard, armchair\nNext Plans: Navigation coffeetable, PickupObject creditcard, Navigation box, PutObject creditcard box, CloseObject box\n\nTask description: To move the CD from the drawer to the safe.\nCompleted plans: \nVisible objects are safe, cd\nNext Plans: Navigation drawer, OpenObject drawer, PickupObject cd, CloseObject drawer, Navigation safe, OpenObject safe, PutObject cd safe, CloseObject safe\n\nTask description: Move a laptop from a coffee table to an armchair.\nCompleted plans: \nVisible objects are armchair, laptop\nNext Plans: Navigation coffeetable, CloseObject laptop, PickupObject laptop, Navigation armchair, PutObject laptop armchair\n\nTask description: Place the wine bottle in the fridge to put it in the trash can.\nCompleted plans: Navigation countertop, PickupObject winebottle\nVisible objects are fridge, garbagecan, winebottle\nNext Plans: Navigation fridge, OpenObject fridge, PutObject winebottle fridge, CloseObject fridge, OpenObject fridge, PickupObject winebottle, CloseObject fridge, Navigation garbagecan, PutObject winebottle garbagecan\n\nTask description: Wash the soap that you found in the cabinet and place it back in the cabinet\nCompleted plans: Navigation cabinet, OpenObject cabinet, PickupObject soapbar, PutObject soapbar sink, ToggleObjectOn faucet, ToggleObjectOff faucet, PickupObject soapbar, Navigation cabinet, PutObject soapbar cabinet\nVisible objects are cabinet, sink, soapbar\nNext Plans: CloseObject cabinet\n\nTask description: 1. If there is water in the mug, pour it out and put the mug in the cabinet.\n2. If no one is watching the TV, turn it on.\n3. If you see a book somewhere unorganized, bring it to the sofa.\n4. If your computer stays off, turn it on.\n5. Put the folder in the closet.\n6. If the radio is off, turn it on\n7. If you have an apple somewhere, bring it to your desk.\nCompleted plans: Navigation mug\nVisible objects are apple, bellpepper, bench, book, bookshelf, box, candybar, ceiling, ceilinglamp, cereal, chips, chocolatesyrup, clock, coffeemaker, crackers, creamybuns, cutleryfork, cutleryknife, dishbowl, dishwashingliquid, door, faucet, floor, fridge, fryingpan, garbagecan, kitchencabinet, kitchencounter, kitchencounterdrawer, kitchentable, lightswitch, microwave, mug, orchid, photoframe, pie, plate, powersocket, rug, salmon, sink, stove, stovefan, toaster, tv, tvstand, wall, walllamp, wallphone, wallpictureframe, wallshelf, washingsponge, waterglass, whippedcream, wineglass\nNext Plans:",
  "raw_output": "OpenObject mug, PickupObject mug, Navigation sink, PutObject mug sink, Navigation tv, ToggleObjectOn tv, Navigation book, PickupObject book, Navigation sofa, PutObject book sofa, Navigation computer, ToggleObjectOn computer, Navigation folder, PickupObject folder, Navigation closet, PutObject folder closet, Navigation radio, ToggleObjectOn radio, Navigation apple, PickupObject apple, Navigation desk, PutObject apple desk",
  "parsed_plan": [
    [
      "OpenObject",
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
      "Navigation",
      "tv"
    ],
    [
      "ToggleObjectOn",
      "tv"
    ],
    [
      "Navigation",
      "book"
    ],
    [
      "PickupObject",
      "book"
    ],
    [
      "Navigation",
      "sofa"
    ],
    [
      "PutObject",
      "book",
      "sofa"
    ],
    [
      "Navigation",
      "computer"
    ],
    [
      "ToggleObjectOn",
      "computer"
    ],
    [
      "Navigation",
      "folder"
    ],
    [
      "PickupObject",
      "folder"
    ],
    [
      "Navigation",
      "closet"
    ],
    [
      "PutObject",
      "folder",
      "closet"
    ],
    [
      "Navigation",
      "radio"
    ],
    [
      "ToggleObjectOn",
      "radio"
    ],
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
      "desk"
    ],
    [
      "PutObject",
      "apple",
      "desk"
    ]
  ],
  "replan_count": 7,
  "reason": "previous action failed: [open] <kitchencabinet> (234)"
}
```
## Step 23
- **Action**: `[wait]`
- **Action Success**: `True`
- **Action Message**: Time passes. You waited for a while.
- **Task Progress**: G1_05=pending, E1_01=done, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

## Step 24
- **Action**: `[open] <mug> (194)`
- **Action Success**: `False`
- **Action Message**: {'0': {'message': 'ScriptExcutor 0: EXECUTION_GENERAL: Script is impossible to execute\n\n'}}
- **Task Progress**: G1_05=pending, E1_01=done, E1_03=pending, E1_11=pending, E1_15=pending, E1_17=pending, E1_02=pending
- **SDG Status**:
No SDG active.
- **Observed Items (0)**: 

