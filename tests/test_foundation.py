import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_foundation_verifier_passes():
    result = subprocess.run(
        [sys.executable, "scripts/verify_foundation.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "TANIM foundation verification passed." in result.stdout


def test_baseline_migration_has_no_destructive_statements():
    migration = (ROOT / "data/migrations/001_foundation.sql").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS" in migration
    assert "DROP TABLE" not in migration.upper()
    assert "TRUNCATE" not in migration.upper()


def test_stop_script_does_not_use_broad_process_termination():
    stop_script = (ROOT / "scripts/stop-tanim.ps1").read_text(encoding="utf-8").lower()

    assert "taskkill.exe /pid" in stop_script
    assert "taskkill /im node.exe" not in stop_script
    assert "taskkill /im python.exe" not in stop_script
    assert "taskkill /im postgres.exe" not in stop_script
