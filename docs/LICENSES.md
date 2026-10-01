# Software and Model License Inventory

This document tracks the licenses of third-party dependencies, binaries, and ML models used in AAKAR.

## Python Dependencies (Backend)
- **FastAPI, Uvicorn, Starlette, Pydantic**: MIT License
- **SQLAlchemy, Alembic**: MIT License
- **OpenCV-Python**: Apache 2.0 / MIT
- **NumPy, SciPy**: BSD 3-Clause
- **Open3D**: MIT License
- **Trimesh**: MIT License
- **Rasterio**: BSD 3-Clause
- **Laspy**: BSD 2-Clause
- **Structlog**: MIT License / Apache 2.0
- **Pytest**: MIT License

## JavaScript Dependencies (Frontend)
- **Three.js**: MIT License (included in `web/vendor/three.min.js` and addons)
- **Viewer logic**: Custom / Apache 2.0 (assumed repository license)

## External Binaries & Systems
- **COLMAP**: New BSD License (used for GPU SfM / MVS path)
- **Redis**: BSD 3-Clause (used for job queuing in production)
- **PostgreSQL**: PostgreSQL License (production database)

## Machine Learning Models
*No models are bundled directly by default.* When using custom ONNX or PyTorch checkpoints:
- **Custom Depth (ONNX)**: The `depth.onnx` provided by the user must adhere to its origin license.
- **Custom Segmentation (YOLO/PT)**: YOLOv8 (Ultralytics) is licensed under **AGPL-3.0**. Commercial use requires an Enterprise License from Ultralytics. The repository integration (`ALLOW_TRUSTED_PT=1`) does not bypass this license requirement.

## Sample Datasets
- **Zurich Urban MAV Dataset (subset)**: Used for tests and baseline benchmarking. See original dataset license for redistribution constraints.
