"""Checks for sharing a clean clone, independent of local manuals and secrets."""

import subprocess
from pathlib import Path

from scripts.check_repository import check, file_issues, link_issues


def test_repository_check_respects_ignores_and_deleted_tracked_files(tmp_path):
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text(".env\n")
    (tmp_path / ".env").write_text("private local settings")
    removed = tmp_path / "old.md"
    removed.write_text("obsolete")
    subprocess.run(["git", "add", "old.md"], cwd=tmp_path, check=True)
    removed.unlink()
    (tmp_path / "README.md").write_text("[Missing](missing.md)")
    count, issues = check(tmp_path)
    assert count == 2
    assert issues == ["README.md: broken local link: missing.md"]


def test_credential_findings_do_not_print_values(tmp_path):
    secret = "sk-" + "proj-" + "a" * 40
    source = tmp_path / "settings.json"
    source.write_text(secret)
    issues = file_issues(source)
    assert issues and all(secret not in issue for issue in issues)
    source.write_text("sk-test-0123456789abcdefWXYZ")
    assert not file_issues(source)


def test_links_support_fragments_encoded_paths_and_ignore_code(tmp_path):
    (tmp_path / "a b.md").write_text("# Heading")
    source = tmp_path / "README.md"
    source.write_text(
        '[Local](a%20b.md#heading) [Same](#here) [Web](https://example.com)\n'
        '```md\n[Example](missing.md)\n```\n'
    )
    assert not link_issues(source, tmp_path)
    source.write_text("[Outside](../outside.md)")
    assert "outside the repository" in link_issues(source, tmp_path)[0]


def test_environment_example_loads_in_the_application(monkeypatch):
    from backend.config import Settings

    monkeypatch.delenv("KG_GENERATION_MODEL", raising=False)
    monkeypatch.delenv("MODEL_NAME", raising=False)
    example = Path(__file__).resolve().parents[1] / ".env.example"
    settings = Settings(_env_file=example)
    assert settings.MODEL_NAME == "gpt-6-luna"


def test_private_paper_is_rejected_even_if_force_added(tmp_path):
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text("/paper/\n")
    (tmp_path / "paper").mkdir()
    manuscript = tmp_path / "paper/manuscript.md"
    manuscript.write_text("Private draft")
    assert check(tmp_path)[1] == []
    subprocess.run(["git", "add", "-f", "paper/manuscript.md"], cwd=tmp_path, check=True)
    assert check(tmp_path)[1] == ["paper/manuscript.md: private paper workspace must not be shared"]


def test_public_documentation_cannot_link_to_local_paper(tmp_path):
    (tmp_path / "paper").mkdir()
    (tmp_path / "paper/STATUS.md").write_text("Private status")
    guide = tmp_path / "README.md"
    guide.write_text("[Status](paper/STATUS.md)")
    assert link_issues(guide, tmp_path) == ["link targets the private paper workspace: paper/STATUS.md"]
