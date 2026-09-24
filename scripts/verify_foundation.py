import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "AGENTS.md",
    "README.md",
    "PRODUCT.md",
    ".env.example",
    ".gitignore",
    ".editorconfig",
    "package.json",
    "package-lock.json",
    "pyproject.toml",
    "TANIM.bat",
    "STOP_TANIM.bat",
    "requirements/PRODUCT_REQUIREMENTS.md",
    "requirements/ARCHITECTURE.md",
    "requirements/DATA_SPECIFICATION.md",
    "requirements/PHASE_1_FOUNDATION.md",
    "requirements/PHASE_4_AUTH_DEMO.md",
    "data/migrations/001_foundation.sql",
    "data/migrations/002_data_foundation.sql",
    "data/migrations/003_auth_sessions.sql",
    "data/dataset_config.json",
    "data/registry/crops.csv",
    "data/registry/crop_scope_inventory.csv",
    "data/registry/geographies.csv",
    "data/seeds/demo_scenarios.json",
    "data/sources/SOURCES.md",
    "data/sources/DATA_FOUNDATION.md",
    "scripts/start-tanim.ps1",
    "scripts/stop-tanim.ps1",
    "scripts/check-health.ps1",
    "scripts/init_db.py",
    "scripts/__init__.py",
    "scripts/data_common.py",
    "scripts/generate_demo_data.py",
    "scripts/validate_data.py",
    "scripts/seed_data.py",
    "scripts/seed_demo_accounts.py",
    "scripts/cleanup_sessions.py",
    "scripts/smoke_api.py",
    "scripts/run-python.mjs",
    "scripts/run-frontends.ps1",
    "scripts/smoke_auth.py",
    "services/api/app.py",
    "services/engine/__init__.py",
    "tests/test_api_health.py",
    "tests/test_foundation.py",
    "tests/test_workspaces.py",
]

REQUIRED_DIRS = [
    "apps/landing",
    "apps/auth",
    "apps/platform",
    "apps/docs",
    "services/api",
    "services/engine",
    "packages/ui",
    "packages/i18n",
    "packages/types",
    "packages/config",
    "packages/api-client",
    "data/registry",
    "data/generated",
    "data/seeds",
    "data/sources",
    "data/migrations",
    "scripts",
    "tests",
]

missing = []

config_path = ROOT / "data" / "dataset_config.json"
if config_path.is_file():
    with config_path.open(encoding="utf-8") as config_file:
        dataset_version = json.load(config_file).get("dataset_version")
    if isinstance(dataset_version, str) and dataset_version:
        generated_dir = Path("data") / "generated" / dataset_version
        REQUIRED_FILES.extend(
            (generated_dir / name).as_posix()
            for name in [
                "crop_profiles.csv.gz",
                "price_history.csv.gz",
                "crop_references.csv.gz",
                "supply_snapshots.csv.gz",
                "soil_suitability.csv.gz",
                "metadata.json",
            ]
        )
    else:
        missing.append("data/dataset_config.json must define a dataset_version")

for item in REQUIRED_FILES:
    if not (ROOT / item).is_file():
        missing.append(f"missing file: {item}")

for item in REQUIRED_DIRS:
    if not (ROOT / item).is_dir():
        missing.append(f"missing directory: {item}")

for app_name in ["landing", "auth", "platform", "docs"]:
    app_root = ROOT / "apps" / app_name
    required_app_files = [
        "package.json",
        "index.html",
        "src/main.tsx",
        "vite.config.ts",
        "tsconfig.json",
    ]
    for relative in required_app_files:
        if not (app_root / relative).is_file():
            missing.append(f"missing file: apps/{app_name}/{relative}")

for package_name in ["ui", "i18n", "types", "config", "api-client"]:
    package_root = ROOT / "packages" / package_name
    if not (package_root / "package.json").is_file():
        missing.append(f"missing file: packages/{package_name}/package.json")

for forbidden in [".env", "node_modules", ".venv"]:
    if (ROOT / forbidden).exists():
        print(f"warning: local-only path exists: {forbidden}")

if missing:
    print("TANIM foundation verification failed.")
    for item in missing:
        print(f"- {item}")
    sys.exit(1)

tracked_result = subprocess.run(
    ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=False
)
if tracked_result.returncode == 0:
    forbidden_parts = {
        "node_modules",
        ".venv",
        "venv",
        "dist",
        "build",
        "coverage",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
    }
    for encoded_path in tracked_result.stdout.split(b"\0"):
        if not encoded_path:
            continue
        tracked_path = Path(encoded_path.decode("utf-8", errors="replace"))
        normalized_parts = {part.lower() for part in tracked_path.parts}
        if tracked_path.name == ".env" or normalized_parts.intersection(forbidden_parts):
            missing.append(f"forbidden tracked local file: {tracked_path.as_posix()}")

    if missing:
        print("TANIM foundation verification failed.")
        for item in missing:
            print(f"- {item}")
        sys.exit(1)

print("TANIM foundation verification passed.")
