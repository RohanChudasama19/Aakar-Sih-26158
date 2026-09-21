import argparse
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import torch

from scripts.semantic.train import SemanticModel


def export_onnx(model_path: Path, output_path: Path):
    if not model_path.exists():
        print(f"Model {model_path} not found.")
        return

    model = SemanticModel(num_classes=8)
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()

    dummy_input = torch.randn(1, 3, 512, 512, requires_grad=True)

    print("Exporting ONNX...")
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size", 2: "height", 3: "width"},
            "output": {0: "batch_size", 2: "height", 3: "width"},
        },
    )

    print("Verifying ONNX model...")
    onnx_model = onnx.load(output_path)
    onnx.checker.check_model(onnx_model)

    # Check numerical agreement
    ort_session = ort.InferenceSession(str(output_path), providers=["CPUExecutionProvider"])

    def to_numpy(tensor):
        return tensor.detach().cpu().numpy() if tensor.requires_grad else tensor.cpu().numpy()

    ort_inputs = {ort_session.get_inputs()[0].name: to_numpy(dummy_input)}
    ort_outs = ort_session.run(None, ort_inputs)

    torch_out = model(dummy_input)

    np.testing.assert_allclose(to_numpy(torch_out), ort_outs[0], rtol=1e-03, atol=1e-05)
    print("ONNX numerical agreement verified successfully!")
    print(f"Exported to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="models/semantic/best_model.pt")
    parser.add_argument("--output", type=str, default="models/semantic/model.onnx")
    args = parser.parse_args()
    export_onnx(Path(args.model), Path(args.output))
