"""Start the prototype interface with one command.

Installs and builds the frontend when needed, then serves the API and the app on
http://127.0.0.1:8765. With ``--dev`` the Vite dev server (http://127.0.0.1:5173,
reloads on every change) runs next to the API instead of the built app.

Example:
    .venv/bin/python scripts/ui.py
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
FRONTEND = ROOT / "frontend"
PORT = 8765


def _newest(folder: Path) -> float:
    return max((path.stat().st_mtime for path in folder.rglob("*") if path.is_file()), default=0.0)


def prepare_frontend(npm: str) -> None:
    if not (FRONTEND / "node_modules").exists():
        subprocess.run([npm, "ci"], cwd=FRONTEND, check=True)
    dist = FRONTEND / "dist"
    sources = max(_newest(FRONTEND / "src"), *(path.stat().st_mtime for path in FRONTEND.glob("*.*")))
    if not dist.exists() or _newest(dist) < sources:
        subprocess.run([npm, "run", "build"], cwd=FRONTEND, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dev", action="store_true", help="Vite dev server with reload, next to the API")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    import uvicorn

    npm = shutil.which("npm")
    vite = None
    if FRONTEND.exists() and npm is None:
        print("npm non trovato: parte solo l'API. Installa Node.js per l'interfaccia.", file=sys.stderr)
    elif FRONTEND.exists() and args.dev:
        if not (FRONTEND / "node_modules").exists():
            subprocess.run([npm, "ci"], cwd=FRONTEND, check=True)
        vite = subprocess.Popen([npm, "run", "dev"], cwd=FRONTEND)
        print("Interfaccia: http://127.0.0.1:5173", flush=True)
    elif FRONTEND.exists():
        prepare_frontend(npm)
        print(f"Interfaccia: http://127.0.0.1:{args.port}", flush=True)
    try:
        uvicorn.run("backend.ui.api:create_app", factory=True, host="127.0.0.1", port=args.port,
                    log_level="warning")
    finally:
        if vite is not None:
            vite.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
