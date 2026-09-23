"""Start the local API and smoke-test health behavior without a PostgreSQL server."""

import json
import os
import socket
import subprocess
import sys
from http.client import HTTPResponse
from pathlib import Path
from time import monotonic, sleep
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
SMOKE_DATABASE_URL = "postgresql://tanim@127.0.0.1:65432/tanim"


def get_free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def get_json_response(url: str, timeout: float = 2) -> tuple[int, dict[str, object]]:
    try:
        response: HTTPResponse
        with urlopen(url, timeout=timeout) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def main() -> int:
    port = get_free_port()
    environment = os.environ.copy()
    environment["DATABASE_URL"] = SMOKE_DATABASE_URL
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "services.api.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"

    try:
        deadline = monotonic() + 15
        while monotonic() < deadline:
            if process.poll() is not None:
                print(f"API smoke failed: the API process exited with status {process.returncode}.")
                return 1
            try:
                health_status, health_body = get_json_response(f"{base_url}/health")
                if health_status == 200:
                    break
            except (TimeoutError, URLError, OSError):
                sleep(0.2)
        else:
            print("API smoke failed: the API did not become ready within 15 seconds.")
            return 1

        if health_body != {"status": "healthy"}:
            print("API smoke failed: /health returned an unexpected response.")
            return 1

        database_status, database_body = get_json_response(f"{base_url}/health/db", timeout=5)
        detail = database_body.get("detail", {})
        if (
            database_status != 503
            or not isinstance(detail, dict)
            or detail.get("status") != "unhealthy"
            or detail.get("database") != "unavailable"
        ):
            print("API smoke failed: /health/db did not report the unavailable database clearly.")
            return 1

        serialized = json.dumps(database_body)
        if SMOKE_DATABASE_URL in serialized or "tanim@" in serialized:
            print("API smoke failed: /health/db exposed connection details.")
            return 1

        print(
            "API smoke passed: /health succeeds; /health/db safely reports no database."
        )
        return 0
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)


if __name__ == "__main__":
    sys.exit(main())
