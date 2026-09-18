import json
import sys
from pathlib import Path

# Ensure scripts can be imported
sys.path.append(str(Path(__file__).parent.parent / "scripts" / "datasets"))
from dataset_manifest import create_manifest


def test_dataset_manifest_creation(tmp_path):
    # Create a dummy file
    dummy_file = tmp_path / "dummy.txt"
    dummy_file.write_text("dummy content")

    create_manifest(
        dataset_name="TestDataset",
        source_url="http://test.com/data.zip",
        source_sequence="seq01",
        local_files=[dummy_file],
        license_reference="MIT",
        original_format="ZIP",
        output_dir=tmp_path,
    )

    manifest_path = tmp_path / "dataset_manifest.json"
    assert manifest_path.exists()

    with open(manifest_path) as f:
        data = json.load(f)

    assert data["dataset_name"] == "TestDataset"
    assert data["source_url"] == "http://test.com/data.zip"
    assert data["license_reference"] == "MIT"
    assert len(data["local_files"]) == 1
    assert data["local_files"][0]["path"] == "dummy.txt"
    assert "sha256" in data["local_files"][0]
