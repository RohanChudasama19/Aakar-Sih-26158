# Dynamic Object Masking

AeroRecon's semantic pipeline isolates `MovingCar` and `Human` as `SEMANTIC_DYNAMIC_CANDIDATE`. 

## Temporal Confirmation
To prevent false-positive masking of static objects (e.g. parked cars falsely identified as moving), dynamic candidates undergo multi-frame temporal confirmation using optical flow or epipolar constraints. Once confirmed, they are elevated to `TEMPORALLY_CONFIRMED_DYNAMIC` and their masks are explicitly withheld from geometric dense reconstruction and texturing.
