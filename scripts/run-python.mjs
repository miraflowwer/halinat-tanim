import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const python =
  process.platform === "win32"
    ? join(root, ".venv", "Scripts", "python.exe")
    : join(root, ".venv", "bin", "python");
const pythonArguments = process.argv.slice(2);

if (!existsSync(python)) {
  console.error("The TANIM Python environment is missing. Create .venv and install the project packages first.");
  process.exit(1);
}

if (pythonArguments.length === 0) {
  console.error("Provide a Python script or module command to run.");
  process.exit(2);
}

const result = spawnSync(python, pythonArguments, {
  cwd: root,
  stdio: "inherit",
});

if (result.error) {
  console.error(`Could not start the TANIM Python environment: ${result.error.message}`);
  process.exit(1);
}

process.exit(result.status ?? 1);
