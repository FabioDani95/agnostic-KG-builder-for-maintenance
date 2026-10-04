"""Run an immutable pre-change checkout, optionally with exact offline replay.

The adapter lives outside the baseline: no baseline prompt, parser or code is
rewritten. Archive misses raise and never reach a real client.
"""
from __future__ import annotations

import argparse
import importlib.util
import runpy
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-source', type=Path, required=True)
    parser.add_argument('--replay', type=Path)
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = args.baseline_source.resolve()
    if not (root / 'baseline_checkout_manifest.json').exists():
        parser.error('baseline must have a frozen checkout manifest')
    import hashlib
    import json
    manifest = json.loads((root / 'baseline_checkout_manifest.json').read_text())
    for name, sha in manifest['files'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != sha:
            parser.error(f'baseline source changed: {name}')
    sys.path.insert(0, str(root))
    if args.replay:
        spec = importlib.util.spec_from_file_location('isolated_exact_replay', Path(__file__).resolve().parents[1] / 'backend/kg_v3/replay.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        provider = module.ReplayProvider(args.replay)
        import backend.services.llm_gateway as gateway
        gateway.get_async_client = lambda **_kwargs: provider
    arguments = args.arguments[1:] if args.arguments[:1] == ['--'] else args.arguments
    sys.argv = [str(root / 'scripts/kg_v3.py'), *arguments]
    runpy.run_path(sys.argv[0], run_name='__main__')


if __name__ == '__main__':
    main()
