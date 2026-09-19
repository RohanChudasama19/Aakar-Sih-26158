import re
from pathlib import Path

for script_name in ["convert_mars_lvig.py", "convert_usegeo.py", "convert_uavid.py", "convert_h3d.py"]:
    p = Path("scripts/datasets") / script_name
    if not p.exists():
        continue
    code = p.read_text(encoding="utf-8")

    if "import argparse" not in code:
        code = "import argparse\n" + code

    func_name = script_name.replace(".py", "")
    dataset_dir = func_name.replace("convert_", "")

    # 1. Replace function signature
    code = re.sub(
        f"def {func_name}\\(input_dir: Path, output_dir: Path\\):",
        f"def {func_name}(input_dir: Path, output_dir: Path, allow_synthetic: bool = False):",
        code,
    )

    # 2. Find ACCESS_BLOCKED check and modify to check allow_synthetic
    # Most adapters have something like:
    # if not input_dir.exists() or not any(input_dir.iterdir()):
    #     print("ACCESS_BLOCKED: ...")
    #     ...
    #     return
    #
    # We want:
    # if not ...:
    #     if not allow_synthetic:
    #         print("ERROR: STRICT_REAL_DATA is enforced.")
    #         sys.exit(1)

    if "ACCESS_BLOCKED" in code:

        def replace_block(m):
            indent = m.group(1)
            original = m.group(0)
            return f"""{indent}if not allow_synthetic:
{indent}    print("ERROR: STRICT_REAL_DATA is enforced.")
{indent}    import sys
{indent}    sys.exit(1)
{original}"""

        code = re.sub(r'([ \t]+)print\("ACCESS_BLOCKED.*?\n(?:.*?\n)*?.*return', replace_block, code, count=1)

    # 3. Replace __main__ block
    main_block = f"""if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="data_external/{dataset_dir}/raw")
    parser.add_argument("--output", type=str, default="data_external/{dataset_dir}")
    parser.add_argument("--allow-synthetic-test-fixture", action="store_true")
    args = parser.parse_args()
    {func_name}(Path(args.input), Path(args.output), args.allow_synthetic_test_fixture)
"""
    code = re.sub(r'if __name__ == [\'"]__main__[\'"]:.*', main_block, code, flags=re.DOTALL)

    p.write_text(code, encoding="utf-8")
    print(f"Patched {script_name}")
