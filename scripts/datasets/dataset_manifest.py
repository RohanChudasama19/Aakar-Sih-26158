import hashlib
import json
from datetime import datetime
from pathlib import Path


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def create_manifest(
    dataset_name: str,
    source_url: str,
    source_sequence: str,
    local_files: list[Path],
    license_reference: str,
    original_format: str,
    output_dir: Path,
) -> None:
    """Generate a provenance manifest for a downloaded dataset sample."""
    manifest = {
        "dataset_name": dataset_name,
        "source_url": source_url,
        "source_sequence": source_sequence,
        "download_timestamp": datetime.utcnow().isoformat() + "Z",
        "license_reference": license_reference,
        "original_format": original_format,
        "conversion_status": "DOWNLOADED",
        "local_files": [],
    }

    for f in local_files:
        if f.is_file():
            manifest["local_files"].append({"path": str(f.name), "sha256": compute_sha256(f)})

    manifest_path = output_dir / "dataset_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=4)

    print(f"Created dataset manifest at {manifest_path}")
