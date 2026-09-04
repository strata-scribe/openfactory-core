import pytest
from pathlib import Path
from openfactory.paths import workspace_path

def test_workspace_path_resolves_valid_subpath(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "dir").mkdir()
    (root / "dir" / "file.txt").touch()

    # Relative to workspace string
    res = workspace_path(str(root), "dir/file.txt")
    assert res == root / "dir" / "file.txt"

    # Relative to workspace Path
    res2 = workspace_path(root, "dir/file.txt")
    assert res2 == root / "dir" / "file.txt"

def test_workspace_path_rejects_path_traversal(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    with pytest.raises(ValueError, match="escapes workspace"):
        workspace_path(root, "../outside.txt")

def test_workspace_path_rejects_path_traversal_deep(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    with pytest.raises(ValueError, match="escapes workspace"):
        workspace_path(root, "dir/../../outside.txt")

def test_workspace_path_rejects_absolute_paths(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    # Absolute paths will be treated as starting from root in Path, meaning `Path(root) / "/etc/passwd"` becomes `/etc/passwd`.
    # Let's ensure this is caught and rejected.
    with pytest.raises(ValueError, match="escapes workspace"):
        workspace_path(root, "/etc/passwd")

def test_workspace_path_allows_internal_symlink(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    target = root / "actual.txt"
    target.touch()

    link = root / "link.txt"
    link.symlink_to(target)

    res = workspace_path(root, "link.txt")
    assert res == target

def test_workspace_path_rejects_external_symlink(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    outside = tmp_path / "outside.txt"
    outside.touch()

    link = root / "link.txt"
    link.symlink_to(outside)

    with pytest.raises(ValueError, match="escapes workspace"):
        workspace_path(root, "link.txt")

def test_workspace_path_allows_redundant_current_dir(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()

    res = workspace_path(root, "././file.txt")
    assert res == root / "file.txt"
