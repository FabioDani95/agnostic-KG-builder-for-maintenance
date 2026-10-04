# Contributing

Start with the [documentation index](docs/README.md), then follow
[development and checks](docs/development.md). This is a local research application;
read [LICENSE](LICENSE) for the repository's existing terms.

## Change workflow

1. Inspect `git status` before editing. Preserve work already present in the checkout.
2. Use a focused branch, such as `codex/documentation-cleanup`, and keep unrelated
   changes out of your commit. Review the complete diff before staging files.
3. Update the relevant canonical guide in `docs/` when commands, configuration,
   behaviour or limitations change. Keep the root README short and link to guides.
4. Run the checks below. Include the problem, resulting behaviour, verification
   and remaining limitations in the pull request description.
5. Stage specific paths, inspect `git diff --cached`, and commit only the intended
   files. Push the reviewed branch and open a pull request.

Do not retain superseded implementation plans or assistant handoff prompts as
onboarding documentation. Completed decisions belong in the architecture or
development guide; Git history retains earlier tracked versions. Use issues for
new work. Keep reusable scripts under `scripts/` and their tests under `tests/`.

## Required checks

From the repository root, with development dependencies installed:

```sh
python scripts/check_repository.py
ruff check backend scripts tests
python scripts/test_offline.py
git diff --check
```

For the interface, from `frontend/`:

```sh
npm ci
npm test
npm run build
```

CI runs the repository check, Python lint, offline Python tests, frontend tests
and production build. Node 22 is selected by `.nvmrc`; Python 3.12 is used in CI.
The offline runner blocks outgoing socket connections while allowing loopback
for local API tests. Tests requiring privately stored manuals or run state may
skip in a fresh clone; the synthetic fixtures remain mandatory.

## Source, local data and scientific evidence

Commit source, tests, dependency declarations/lockfiles, canonical documentation
and deliberately reviewed research artifacts. `.gitignore` excludes credentials,
local runs, uploaded PDFs, provider response caches and generated preview files.
Ignored files already tracked remain tracked: changing ignore rules does not
remove historical evidence from Git.

Do not stage `.env`, API keys, local databases, `node_modules/`, frontend build
output, the private `paper/` folder, the local `workspace/`, ad hoc `runs/`,
`experiments/` or `review/` folders. Never force-add manuscript materials;
the repository check rejects files under `paper/` even if they are staged.
The repository check catches selected secret formats, private filenames,
oversized files and broken local links in the application guides. It is a
lightweight check of the working tree, not a complete audit of Git history.

Frozen evidence under `campaign/` is retained separately from active application
documentation. Do not edit gold to match predictions, rewrite historic manifests
or move results between code/model versions. The private manuscript workspace has
a separate lifecycle and is not a prerequisite for installing or testing the app.
When working on a local copy of it, follow its own instructions and evidence records.

Paid extraction and evaluation require an explicit spending decision, a bounded
budget and the correct ledger. Tests, replay and preflight do not authorize paid
runs. Update existing IT/EN interface text together, preserving guide section IDs.

## Before sharing

Confirm a fresh clone can follow the setup guide with `.env.example`, and review
the exact staged file list. Keep runtime and dependency upgrades separate from
documentation cleanup when they can affect parser IDs, frozen runs or model
behaviour. Report technical test results separately from extraction quality.
