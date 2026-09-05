import pytest
import os
import subprocess
from pydantic import BaseModel, Field

from openfactory.contracts.project import Project, ProviderRef
from openfactory.runtime.card_repo import _ref_repo, _is_default_repo, _checkout_key, _runner_view, RuntimeCardRepo


def test_ref_repo_no_ref_repo():
    project = Project(name="test", repo_path="https://github.com/owner/default", tracker=ProviderRef(kind="github", repo="owner/default"))
    assert _ref_repo(project, "123") == ("owner/default", "123")
    assert _ref_repo(project, "#123") == ("owner/default", "123")


def test_ref_repo_with_ref_repo():
    project = Project(name="test", repo_path="https://github.com/owner/default", tracker=ProviderRef(kind="github", repo="owner/default"))
    assert _ref_repo(project, "owner/other#123") == ("owner/other", "123")
    assert _ref_repo(project, "#owner/other#123") == ("owner/other", "123")


def test_is_default_repo():
    project = Project(name="test", repo_path="https://github.com/owner/default", tracker=ProviderRef(kind="github", repo="owner/default"))
    assert _is_default_repo(project, "owner/default") is True
    assert _is_default_repo(project, "owner/other") is False
    assert _is_default_repo(project, "") is True


def test_is_default_repo_with_forge():
    project = Project(name="test", repo_path="https://github.com/owner/forge_default", forge=ProviderRef(kind="github", repo="owner/forge_default"), tracker=ProviderRef(kind="github", repo="owner/default"))
    assert _is_default_repo(project, "owner/forge_default") is True
    assert _is_default_repo(project, "owner/default") is False
    assert _is_default_repo(project, "") is True


def test_checkout_key():
    project = Project(name="test", repo_path="https://github.com/owner/default", tracker=ProviderRef(kind="github", repo="owner/default"))
    assert _checkout_key(project, "owner/default") == "test"
    assert _checkout_key(project, "owner/other") == "test--owner--other"


def test_runner_view_default():
    project = Project(name="test", tracker=ProviderRef(kind="github", repo="owner/default"), repo_path="https://github.com/owner/default.git")
    view, key = _runner_view(project, "123")
    assert key == "test"
    assert view.repo_path == "https://github.com/owner/default.git"
    assert view.tracker.repo == "owner/default"


def test_runner_view_other(monkeypatch):
    from openfactory.adapters.forge import registry
    monkeypatch.setattr(registry, "clone_url_for", lambda p, r, token: f"https://github.com/{r}.git")

    project = Project(name="test", tracker=ProviderRef(kind="github", repo="owner/default"), forge=ProviderRef(kind="github", repo="owner/default"), repo_path="https://github.com/owner/default.git")
    view, key = _runner_view(project, "owner/other#123")
    assert key == "test--owner--other"
    assert view.repo_path == "https://github.com/owner/other.git"
    assert view.forge.repo == "owner/other"
    assert view.tracker.repo == "owner/default"


@pytest.fixture
def temp_git_repo(tmp_path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    subprocess.run(["git", "init"], cwd=repo_path, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
    return str(repo_path)


def test_runtime_card_repo_write_read_blob(temp_git_repo):
    repo = RuntimeCardRepo(temp_git_repo)
    data = b"card metadata content"
    blob_sha = repo.write_blob(data)
    assert len(blob_sha) == 40
    read_data = repo.read_blob(blob_sha)
    assert read_data == data


def test_runtime_card_repo_commit_creation(temp_git_repo):
    repo = RuntimeCardRepo(temp_git_repo)
    # create an empty tree
    tree_sha = subprocess.run(["git", "write-tree"], cwd=temp_git_repo, check=True, stdout=subprocess.PIPE).stdout.decode().strip()

    commit_sha = repo.create_commit(tree_sha, None, "test commit")
    assert len(commit_sha) == 40

    # check that we can read the commit back
    commit_output = subprocess.run(["git", "cat-file", "-p", commit_sha], cwd=temp_git_repo, check=True, stdout=subprocess.PIPE).stdout.decode()
    assert "test commit" in commit_output
    assert f"tree {tree_sha}" in commit_output


def test_runtime_card_repo_branch_isolation(temp_git_repo):
    repo = RuntimeCardRepo(temp_git_repo)
    tree_sha = subprocess.run(["git", "write-tree"], cwd=temp_git_repo, check=True, stdout=subprocess.PIPE).stdout.decode().strip()
    commit_sha = repo.create_commit(tree_sha, None, "test commit")

    repo.isolate_branch("test-branch", commit_sha)

    branch_sha = subprocess.run(["git", "rev-parse", "test-branch"], cwd=temp_git_repo, check=True, stdout=subprocess.PIPE).stdout.decode().strip()
    assert branch_sha == commit_sha
