import pytest
import yaml
from pathlib import Path
from openfactory.registry import ProjectRegistry
from openfactory.contracts.project import Project, ProviderRef

def _p(name: str) -> Project:
    return Project(name=name, repo_path=f"/tmp/{name}",
                   tracker=ProviderRef(kind="github", repo=f"acme/{name}"))


def test_registry_loading_and_dictionary_access(tmp_path: Path):
    """Test loading project configs and dictionary-like access logic."""
    reg_path = tmp_path / "registry.yaml"
    reg_path.write_text(yaml.safe_dump({"projects": {
        "proj1": _p("proj1").model_dump(mode="json"),
        "proj2": _p("proj2").model_dump(mode="json"),
    }}))

    registry = ProjectRegistry(reg_path)
    projects = registry.list()
    assert len(projects) == 2
    assert {p.name for p in projects} == {"proj1", "proj2"}

    # Test get() method mapping to dictionary access
    proj1 = registry.get("proj1")
    assert proj1.name == "proj1"

    with pytest.raises(KeyError, match="proj3"):
        registry.get("proj3")


def test_duplicate_key_handling(tmp_path: Path):
    """Test that ProjectRegistry properly handles and prevents duplicate keys/projects."""
    reg_path = tmp_path / "registry.yaml"
    registry = ProjectRegistry(reg_path)

    # Add a project
    registry.add(_p("duplicate_test"))

    # Trying to add the same project again should raise a ValueError
    with pytest.raises(ValueError, match="project already registered: 'duplicate_test'"):
        registry.add(_p("duplicate_test"))
