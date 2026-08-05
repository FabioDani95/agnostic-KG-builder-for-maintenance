#!/usr/bin/env node

import { spawn, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const isWindows = process.platform === "win32";
const port = String(process.env.PORT || "8000");
const host = String(process.env.HOST || "127.0.0.1");
const killOnly = process.argv.includes("--kill-only");
const reload = process.env.KG_RELOAD === "1";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function runChecked(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: repoRoot,
    stdio: options.stdio || "inherit",
    encoding: "utf8",
    env: process.env,
  });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(" ")} exited with ${result.status}`);
  }
  return result;
}

function runCapture(command, args) {
  const result = spawnSync(command, args, {
    cwd: repoRoot,
    stdio: ["ignore", "pipe", "pipe"],
    encoding: "utf8",
    env: process.env,
  });
  if (result.error || result.status !== 0) return "";
  return result.stdout || "";
}

function pythonBin() {
  if (process.env.PYTHON_BIN) return process.env.PYTHON_BIN;
  return path.join(repoRoot, ".venv", isWindows ? "Scripts/python.exe" : "bin/python");
}

function createVenv() {
  if (existsSync(pythonBin())) return;
  if (isWindows) {
    const result = spawnSync("py", ["-3", "-m", "venv", ".venv"], {
      cwd: repoRoot,
      stdio: "inherit",
      env: process.env,
    });
    if (!result.error && result.status === 0) return;
  }
  runChecked("python3", ["-m", "venv", ".venv"]);
}

function ensurePythonDeps() {
  createVenv();
  const py = pythonBin();
  const runtimeImports = [
    "fastapi",
    "fitz",
    "json_repair",
    "jsonschema",
    "langgraph",
    "multipart",
    "networkx",
    "openai",
    "openpyxl",
    "pydantic_settings",
    "uvicorn",
    "yaml",
  ];
  const check = spawnSync(py, ["-c", `import ${runtimeImports.join(", ")}`], {
    cwd: repoRoot,
    stdio: "ignore",
    env: process.env,
  });
  if (check.status !== 0) {
    runChecked(py, ["-m", "pip", "install", "-r", "requirements.txt"]);
  }
  return py;
}

function findListeningPids() {
  if (isWindows) {
    const output = runCapture("netstat", ["-ano", "-p", "tcp"]);
    const pids = new Set();
    for (const line of output.split(/\r?\n/)) {
      if (!line.includes("LISTENING")) continue;
      const parts = line.trim().split(/\s+/);
      const localAddress = parts[1] || "";
      const pid = parts[parts.length - 1] || "";
      if (localAddress.endsWith(`:${port}`) && /^\d+$/.test(pid)) pids.add(pid);
    }
    return [...pids];
  }

  const output = runCapture("lsof", ["-ti", `tcp:${port}`, "-sTCP:LISTEN"]);
  return output
    .split(/\s+/)
    .map((pid) => pid.trim())
    .filter((pid) => /^\d+$/.test(pid) && Number(pid) !== process.pid);
}

function killPids(pids, force = false) {
  for (const pid of pids) {
    if (isWindows) {
      const args = ["/PID", pid, "/T"];
      if (force) args.push("/F");
      spawnSync("taskkill", args, { stdio: "ignore" });
      continue;
    }
    try {
      process.kill(Number(pid), force ? "SIGKILL" : "SIGTERM");
    } catch (err) {
      if (err.code !== "ESRCH") throw err;
    }
  }
}

async function cleanupPort() {
  const pids = findListeningPids();
  if (!pids.length) return;
  console.error(`[dev-server] Freeing ${host}:${port}; stopping PID(s): ${pids.join(", ")}`);
  killPids(pids, false);
  await sleep(800);
  const remaining = findListeningPids();
  if (remaining.length) {
    console.error(`[dev-server] Force-stopping PID(s): ${remaining.join(", ")}`);
    killPids(remaining, true);
    await sleep(300);
  }
}

async function main() {
  await cleanupPort();
  if (killOnly) return;

  const py = ensurePythonDeps();
  const args = ["-m", "uvicorn", "backend.main:app", "--host", host, "--port", port];
  if (reload) {
    args.push(
      "--reload",
      "--reload-exclude",
      "tests/*",
      "--reload-exclude",
      "test-results/*",
      "--reload-exclude",
      "playwright-report/*",
    );
  }

  const child = spawn(py, args, {
    cwd: repoRoot,
    stdio: "inherit",
    env: process.env,
  });

  const forward = (signal) => {
    if (!child.killed) child.kill(signal);
    setTimeout(() => {
      if (!child.killed) child.kill("SIGKILL");
    }, 1000).unref();
  };
  process.on("SIGINT", () => forward("SIGINT"));
  process.on("SIGTERM", () => forward("SIGTERM"));

  child.on("exit", (code, signal) => {
    if (signal) process.exit(0);
    process.exit(code ?? 0);
  });
}

main().catch((err) => {
  console.error(`[dev-server] ${err.message}`);
  process.exit(1);
});
