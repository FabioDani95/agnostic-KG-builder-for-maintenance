"""Check shareable files and local documentation links without network access.

Examines tracked files plus non-ignored untracked files, so it works before a
commit as well as in CI. Historical research documents are not onboarding guides
and are excluded from link checks. Secret findings never print matching values.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 95 * 1024 * 1024
TEXT_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".json", ".jsonl", ".md", ".txt", ".yml", ".yaml", ".toml", ".cff"}
SECRET_PATTERNS = (
    re.compile(r"sk-(?:proj-|svcacct-)[A-Za-z0-9_-]{32,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
MARKDOWN_LINK = re.compile(r"\[[^\]\n]*\]\(<?([^\s)>]+)>?(?:\s+\"[^\"]*\")?\)")


def repository_files(root: Path) -> list[Path]:
    result = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root,
    )
    return sorted({root / name.decode() for name in result.split(b"\0") if name and (root / name.decode()).is_file()})


def file_issues(path: Path) -> list[str]:
    issues = []
    if path.name.startswith(".env") and path.name != ".env.example":
        issues.append("private environment file")
    if path.suffix.lower() in {".key", ".pem", ".p12", ".pfx"} or path.name in {"id_rsa", "id_ed25519"}:
        issues.append("credential/private-key filename")
    if path.stat().st_size > MAX_FILE_BYTES:
        issues.append("file exceeds the 95 MiB repository limit")
        return issues
    if path.suffix.lower() in TEXT_SUFFIXES or path.name == ".env.example":
        content = path.read_text(encoding="utf-8", errors="replace")
        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            issues.append("possible credential content; inspect locally (value redacted)")
    return issues


def link_issues(path: Path, root: Path) -> list[str]:
    issues = []
    # Ignore code samples; Markdown links inside examples are not navigation.
    content = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
    for match in MARKDOWN_LINK.finditer(content):
        target = match.group(1)
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        target_path = unquote(parsed.path)
        resolved = (root / target_path.lstrip("/") if target_path.startswith("/") else path.parent / target_path).resolve()
        if not resolved.is_relative_to(root.resolve()):
            issues.append(f"link points outside the repository: {target}")
        elif resolved.is_relative_to(root.resolve() / "paper"):
            issues.append(f"link targets the private paper workspace: {target}")
        elif not resolved.exists():
            issues.append(f"broken local link: {target}")
    return issues


def check(root: Path) -> tuple[int, list[str]]:
    files = repository_files(root)
    issues = []
    for path in files:
        relative = path.relative_to(root)
        if relative.parts[0] == "paper":
            issues.append(f"{relative}: private paper workspace must not be shared")
            continue
        issues.extend(f"{relative}: {issue}" for issue in file_issues(path))
        if relative.as_posix() in {"README.md", "CONTRIBUTING.md", "campaign/README.md"} or (
            relative.parts[0] == "docs" and path.suffix == ".md"
        ):
            issues.extend(f"{relative}: {issue}" for issue in link_issues(path, root))
    return len(files), issues


def main() -> int:
    count, issues = check(ROOT)
    if issues:
        print("Repository checks failed:")
        print("\n".join(f"- {issue}" for issue in issues))
        return 1
    print(f"Repository checks passed ({count} shareable files; active guide links checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
