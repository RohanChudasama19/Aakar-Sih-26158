import argparse
from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch
from torchvision.models.segmentation import lraspp_mobilenet_v3_large
from torchvision.models.segmentation.lraspp import LRASPPHead


def build_model(num_classes=8):
    model = lraspp_mobilenet_v3_large(weights=None)
    model.classifier.low_classifier = torch.nn.Conv2d(40, num_classes, 1)
    model.classifier.high_classifier = torch.nn.Conv2d(128, num_classes, 1)
    return model


def main():
    parser = argparse.ArgumentParser(description="Export PyTorch Segmentation Model to ONNX")
    parser.add_argument("--weights", type=str, default="best_model.pth")
    parser.add_argument("--output", type=str, default="semantic_model.onnx")
    parser.add_argument("--opset", type=int, default=14)
    args = parser.parse_args()

    print(f"Exporting model to ONNX (opset {args.opset})...")

    if not Path(args.weights).exists():
        raise FileNotFoundError(f"Weights file not found: {args.weights}")

    model = build_model(num_classes=8)
    checkpoint = torch.load(args.weights, map_location="cpu")
    model.load_state_dict(checkpoint["model_state"])
    model.eval()

    dummy_input = torch.randn(1, 3, 512, 1024)

    torch.onnx.export(
        model,
        dummy_input,
        args.output,
        opset_version=args.opset,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size", 2: "height", 3: "width"},
            "output": {0: "batch_size", 2: "height", 3: "width"},
        },
    )

    print(f"Exported to {args.output}")

    # Verify
    ort_session = ort.InferenceSession(args.output)
    ort_inputs = {ort_session.get_inputs()[0].name: dummy_input.numpy()}
    ort_outs = ort_session.run(None, ort_inputs)

    with torch.no_grad():
        torch_out = model(dummy_input)["out"]

    np.testing.assert_allclose(torch_out.numpy(), ort_outs[0], rtol=1e-03, atol=1e-04)
    print("Numerical Agreement: VERIFIED")

    diff = np.abs(torch_out.numpy() - ort_outs[0])
    print(f"Max absolute difference: {np.max(diff)}")


if __name__ == "__main__":
    main()
