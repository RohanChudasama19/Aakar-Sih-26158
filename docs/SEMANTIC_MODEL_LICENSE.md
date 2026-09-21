# Semantic Model Licenses

The semantic segmentation architecture relies on:
- **PyTorch / torchvision:** BSD 3-Clause License
- **Architecture:** DeepLabV3 (LRASPP) with MobileNetV3-Large backbone
- **Pre-trained Weights:** ImageNet/COCO weights (BSD 3-Clause). 

No proprietary datasets were bundled in the repository. The UAVid dataset requires a manual download and agreement to their official usage terms. Therefore, the inference script checks for locally generated weights and safely falls back if they are unavailable.

## Redistribution Rights
The architecture code and MobileNet backbone are fully permissive for commercial and demo use under the BSD 3-Clause license. 
If trained on UAVid, the resulting weights inherit any limitations specified by the UAVid dataset license regarding commercial application.
