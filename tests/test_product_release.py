from openfactory.product.release import (
    detect_version_bump,
    compile_release_notes,
    generate_changelog_markdown,
)

def test_detect_version_bump_major():
    assert detect_version_bump("1.2.3", "2.0.0") == "major"

def test_detect_version_bump_minor():
    assert detect_version_bump("1.2.3", "1.3.0") == "minor"

def test_detect_version_bump_patch():
    assert detect_version_bump("1.2.3", "1.2.4") == "patch"

def test_detect_version_bump_none():
    assert detect_version_bump("1.2.3", "1.2.3") == "none"

def test_detect_version_bump_prerelease_ignored():
    assert detect_version_bump("1.2.3", "1.2.4-alpha") == "patch"

def test_compile_release_notes_empty():
    assert compile_release_notes([]) == []

def test_compile_release_notes_ignores_empty_strings():
    assert compile_release_notes(["", " ", "\n"]) == []

def test_compile_release_notes_extracts_first_line():
    commits = [
        "feat: add feature\n\nMore details here.",
        "fix: resolve bug",
        "  chore: cleanup  "
    ]
    expected = [
        "feat: add feature",
        "fix: resolve bug",
        "chore: cleanup"
    ]
    assert compile_release_notes(commits) == expected

def test_generate_changelog_markdown_no_notes():
    expected = "## 1.0.0\n\n- No changes\n"
    assert generate_changelog_markdown("1.0.0", []) == expected

def test_generate_changelog_markdown_with_notes():
    notes = ["feat: add feature", "fix: resolve bug"]
    expected = "## 1.0.0\n\n- feat: add feature\n- fix: resolve bug\n"
    assert generate_changelog_markdown("1.0.0", notes) == expected
