import subprocess
import sys
from pathlib import Path


def test_adapter_cli_strict_real_data(tmp_path):
    """Ensure adapter CLI fails without --allow-synthetic-test-fixture when real data is missing."""

    python_exe = sys.executable

    adapter = Path("scripts/datasets/convert_zurich_mav.py")

    # Run without flag
    result = subprocess.run(
        [python_exe, str(adapter), "--input", str(tmp_path), "--output", str(tmp_path)], capture_output=True, text=True
    )
    assert result.returncode == 1
    assert "STRICT_REAL_DATA is enforced" in result.stdout

    # Run with flag
    result2 = subprocess.run(
        [
            python_exe,
            str(adapter),
            "--input",
            str(tmp_path),
            "--output",
            str(tmp_path),
            "--allow-synthetic-test-fixture",
        ],
        capture_output=True,
        text=True,
    )
    assert result2.returncode == 0
    assert "falling back to synthetic" in result2.stdout.lower() or "creating synthetic" in result2.stdout.lower()
