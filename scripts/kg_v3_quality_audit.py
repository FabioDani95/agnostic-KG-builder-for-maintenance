"""Offline preservation audit. Never rewrites frozen inputs or concurrent files."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=False)
    sources = sorted({p for folder in ('backend/kg_v3', 'backend/adapters', 'backend/services', 'scripts', 'tests')
                      for p in (ROOT / folder).glob('*.py')} | {ROOT / 'ontology_schema.JSON', ROOT / 'config.yaml'})
    protected = sorted({p for folder in ('campaign', 'paper/experiments', 'paper/evaluation')
                        for p in (ROOT / folder).rglob('*') if p.is_file() and p.suffix in {'.json', '.md', '.yaml'}})
    concurrent = subprocess.check_output(['git', 'status', '--porcelain', '-uall'], cwd=ROOT, text=True)
    graphs = json.loads((ROOT / 'campaign/results/quality_F.json').read_text())
    checks = []
    for manual, data in graphs['manuals'].items():
        for run, expected in data['runs'].items():
            p = ROOT / 'campaign' / manual / 'runs' / run / 'graph.json'
            checks.append({'path': str(p.relative_to(ROOT)), 'expected': expected['graph_sha256'],
                           'actual': sha(p) if p.exists() else None,
                           'matches': p.exists() and sha(p) == expected['graph_sha256']})
    manifest = {'version': 'kg-quality-baseline-1',
                'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'working_tree': concurrent, 'sources': {str(p.relative_to(ROOT)): sha(p) for p in sources},
                'protected': {str(p.relative_to(ROOT)): sha(p) for p in protected}, 'historical_F': checks,
                'dependencies': {name: importlib.metadata.version(name)
                                 for name in ('pydantic', 'PyMuPDF', 'openai', 'pytest')},
                'quality_measured': False, 'provider_calls': 0}
    (out / 'baseline_manifest.json').write_text(json.dumps(manifest, indent=2))
    with tarfile.open(out / 'baseline_source.tar.gz', 'w:gz') as archive:
        for p in sources:
            archive.add(p, arcname=str(p.relative_to(ROOT)))
    return manifest


def verify(path: Path) -> dict:
    data = json.loads(path.read_text())
    changed = [name for name, digest in data['protected'].items()
               if not (ROOT / name).exists() or sha(ROOT / name) != digest]
    return {'protected_files': len(data['protected']), 'changed': changed,
            'historical_F_matches': sum(c['matches'] for c in data['historical_F']),
            'historical_F_expected': len(data['historical_F'])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--snapshot', type=Path)
    group.add_argument('--verify', type=Path)
    args = parser.parse_args()
    result = snapshot(args.snapshot) if args.snapshot else verify(args.verify)
    print(json.dumps({k: v for k, v in result.items() if k not in {'sources', 'protected', 'working_tree'}}, indent=2))


if __name__ == '__main__':
    main()
