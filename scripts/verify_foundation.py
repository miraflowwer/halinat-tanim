from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "AGENTS.md",
    "README.md",
    "PRODUCT.md",
    ".env.example",
    ".gitignore",
    ".editorconfig",
    "package.json",
    "pyproject.toml",
    "TANIM.bat",
    "STOP_TANIM.bat",
    "requirements/PRODUCT_REQUIREMENTS.md",
    "requirements/ARCHITECTURE.md",
    "requirements/DATA_SPECIFICATION.md",
    "requirements/PHASE_1_FOUNDATION.md",
    "data/migrations/001_foundation.sql",
    "scripts/start-tanim.ps1",
    "scripts/stop-tanim.ps1",
    "scripts/check-health.ps1",
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
    "data/registry",
    "data/generated",
    "data/seeds",
    "data/sources",
    "data/migrations",
    "scripts",
    "tests",
]

missing = []

for item in REQUIRED_FILES:
    if not (ROOT / item).is_file():
        missing.append(f"missing file: {item}")

for item in REQUIRED_DIRS:
    if not (ROOT / item).is_dir():
        missing.append(f"missing directory: {item}")

for forbidden in [".env", "node_modules", ".venv"]:
    if (ROOT / forbidden).exists():
        print(f"warning: local-only path exists: {forbidden}")

if missing:
    print("TANIM foundation verification failed.")
    for item in missing:
        print(f"- {item}")
    sys.exit(1)

print("TANIM foundation verification passed.")
