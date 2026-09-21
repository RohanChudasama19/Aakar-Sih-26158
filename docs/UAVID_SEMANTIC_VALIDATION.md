# UAVid Semantic Validation

Because the UAVid dataset requires manual registration and download from the official providers, no real data was used for model validation.

The `convert_uavid.py` script automatically halts and issues a `MANUAL_DOWNLOAD_REQUIRED` warning to strictly avoid train/test leakage or synthetic hallucinations of official benchmarks. 

Therefore, `REAL_MODEL_VALIDATION = NOT_AVAILABLE`. All architecture tests rely on controlled random dummy tensors to prove matrix operations, ONNX opset export, and end-to-end pipeline integrity.
