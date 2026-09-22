# UAVid Semantic Validation

## Dataset Status
- **Real UAVid Data**: NOT_AVAILABLE locally. The `data_external/uavid/raw` directory was inspected and found empty.
- **Model Training**: Safely aborted. The pipeline is implemented but suspended pending data availability.
- **Validation**: Mapped classes verified synthetically via pytest. 
- **GPU Availability**: Local `torch.cuda.is_available()` reported FALSE on the current testbed.

## Validation Protocol
If data were available, the protocol strictly enforces:
- Zero data leakage between Train/Validation/Test splits.
- Checkpointing isolated to Validation.
- No dummy/fabricated ONNX weights exported.

## Metrics tracked
- **Native**: UAVid mIoU, per-class IoU (Pending data).
- **AeroRecon**: Mapped mIoU (Pending data).
