import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_APPS = {
    "landing": ("@tanim/landing", 3000),
    "auth": ("@tanim/auth", 3001),
    "platform": ("@tanim/platform", 3002),
    "docs": ("@tanim/docs", 3003),
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_root_declares_expected_npm_workspaces():
    root = read_json(ROOT / "package.json")
    assert root["private"] is True
    assert root["workspaces"] == ["apps/*", "packages/*"]

    for app, (expected_name, _) in EXPECTED_APPS.items():
        manifest = read_json(ROOT / "apps" / app / "package.json")
        assert manifest["name"] == expected_name
        assert {"dev", "build", "lint"}.issubset(manifest["scripts"])

    for package in ["ui", "i18n", "types", "config"]:
        manifest = read_json(ROOT / "packages" / package / "package.json")
        assert manifest["name"] == f"@tanim/{package}"


def test_frontend_commands_and_ports_match_the_foundation():
    root = read_json(ROOT / "package.json")
    config = (ROOT / "packages/config/src/index.ts").read_text(encoding="utf-8")

    for app, (workspace_name, port) in EXPECTED_APPS.items():
        assert f"{workspace_name}" in root["scripts"][f"dev:{app}"]
        assert str(port) in config
