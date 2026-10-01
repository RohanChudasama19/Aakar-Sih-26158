
import os
import shutil
import glob

# Create target directory
archive_dir = "scripts/archive"
os.makedirs(archive_dir, exist_ok=True)

# Files to keep in root
keep_files = {
    "README.md", "CONTRIBUTORS.md", "requirements.txt", "requirements-dev.txt", 
    "requirements-models.txt", "requirements-semantic.txt", "pyproject.toml", 
    ".gitignore", ".env.example", "publication_audit_report.md"
}

# Directories to keep in root
keep_dirs = {
    "app", "frontend", "web", "docs", "scripts", "tests", "models", 
    "samples", "demo", "screenshots", "colorado_dataset", "data", "weights", ".git"
}

for item in os.listdir("."):
    if item in keep_files or item in keep_dirs or item.startswith("."):
        continue
    
    if os.path.isfile(item):
        if item.endswith(".py") or item.endswith(".txt") or item.endswith(".log") or item.endswith(".json") or item.endswith(".csv") or item.endswith(".md") or item.endswith(".mjs") or item.endswith(".js"):
            # Move to archive
            try:
                shutil.move(item, os.path.join(archive_dir, item))
            except Exception as e:
                print(f"Failed to move {item}: {e}")
        elif item.endswith(".png") or item.endswith(".jpg"):
            # Move images to docs/assets
            os.makedirs("docs/assets", exist_ok=True)
            try:
                shutil.move(item, os.path.join("docs/assets", item))
            except Exception as e:
                print(f"Failed to move {item}: {e}")

