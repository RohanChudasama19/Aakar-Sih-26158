# Semantic Segmentation Model License Audit

## Architecture and Code License
- **Model**: LRASPP MobileNetV3-Large (DeepLabV3 variant)
- **Source**: `torchvision.models.segmentation.lraspp_mobilenet_v3_large`
- **Code License**: BSD 3-Clause License (PyTorch/Torchvision)
- **Redistribution Rights**: Fully permissive for commercial, academic, and private use, provided the copyright notice is retained.

## Pretrained Foundation Weights
- **Source**: Torchvision pre-trained on COCO / Cityscapes.
- **License**: BSD 3-Clause / CC-BY (depending on underlying dataset specifics). For AeroRecon, foundation weights are fine-tuned on UAVid.

## UAVid Dataset License (Fine-tuning Target)
- **Source**: UAVid dataset (https://uavid.nl/)
- **License**: Custom academic/research-only license. 
- **Redistribution Rights**: Non-commercial. Weights fine-tuned *solely* on UAVid may inherit these restrictions. AeroRecon supports dynamic loading of `.onnx` files so users can provide their own proprietary or academic weights without polluting the open-source AeroRecon distribution.
- **Attribution**: "UAVid: A Semantic Segmentation Dataset for UAV Imagery" (Lyu et al., ISPRS 2020).

## AeroRecon Implementation
- The AeroRecon segmentation pipeline (`app/pipeline/semantic_model.py`) and training scripts are licensed under the overarching AeroRecon project license (e.g., Apache 2.0).
