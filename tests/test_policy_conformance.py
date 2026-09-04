import pytest
from pathlib import Path

from openfactory.contracts.manifest import Manifest, ComponentDocs, Component, DocRoles
from openfactory.policy.conformance import check, floor_reason, inherited_floor_roles
from openfactory.policy import presets

@pytest.fixture(autouse=True)
def reset_floor_cache():
    presets.org_default_validation.cache_clear()
    yield
    presets.org_default_validation.cache_clear()

def test_missing_test_gate_is_refused():
    manifest = Manifest()
    report = check(manifest, Path("."))

    assert not report.ok
    assert any(i.level == "error" and "floor requires a 'test' validation" in i.message for i in report.issues)

def test_inherited_floor_gate_emits_a_warning():
    manifest = Manifest(validate={"test": "pytest"})
    report = check(manifest, Path("."))

    assert report.ok
    assert any(i.level == "warning" and "the 'security' gate is the DEPLOYMENT's default" in i.message for i in report.issues)

def test_unknown_component_stack_is_refused():
    manifest = Manifest(
        validate={"test": "pytest"},
        components={"mycomp": Component(path="src", stack="nonexistent-stack")}
    )
    report = check(manifest, Path("."))

    assert not report.ok
    assert any(i.level == "error" and "unknown stack 'nonexistent-stack'" in i.message for i in report.issues)

def test_missing_doc_paths_are_warned_about(tmp_path):
    manifest = Manifest(
        validate={"test": "pytest"},
        docs=DocRoles(constraints="docs/adr/*.md", architecture="docs/arch.md")
    )
    report = check(manifest, tmp_path)

    assert report.ok
    assert any(i.level == "warning" and "docs.constraints glob 'docs/adr/*.md' matches no files" in i.message for i in report.issues)
    assert any(i.level == "warning" and "docs.architecture glob 'docs/arch.md' matches no files" in i.message for i in report.issues)

def test_unreadable_org_floor_is_refused(monkeypatch):
    monkeypatch.setattr(presets, "ORG_FLOOR_FILE", Path("/does/not/exist"))
    presets.org_default_validation.cache_clear()

    manifest = Manifest(validate={"test": "pytest", "security": "scanner"})
    report = check(manifest, Path("."))

    assert not report.ok
    assert any(i.level == "error" and "cannot read its own default gates" in i.message for i in report.issues)

def test_floor_reason_when_org_floor_is_unreadable(monkeypatch):
    monkeypatch.setattr(presets, "ORG_FLOOR_FILE", Path("/does/not/exist"))
    presets.org_default_validation.cache_clear()

    manifest = Manifest()
    reason = floor_reason(manifest)

    assert reason is not None
    assert "This deployment could not read its own default gates" in reason
    assert "OPENFACTORY_FLOOR_UNREADABLE" in reason

def test_floor_reason_when_gates_are_missing():
    manifest = Manifest()
    reason = floor_reason(manifest)

    assert reason is not None
    assert "this project declares no `test` validation" in reason
    assert "Declare a `test:` gate" in reason

def test_inherited_floor_roles():
    # If the user defines the exact same command as the floor, they are "inheriting" it.
    defaults = presets.org_default_validation()
    assert defaults

    # Take a gate from the defaults
    role = list(defaults.keys())[0]
    gate = defaults[role]

    manifest = Manifest(validate={role: gate})
    roles = inherited_floor_roles(manifest)

    assert role in roles

def test_overridden_floor_roles_are_not_inherited():
    defaults = presets.org_default_validation()
    assert defaults

    role = list(defaults.keys())[0]
    manifest = Manifest(validate={role: "echo 'overridden'"})
    roles = inherited_floor_roles(manifest)

    assert role not in roles

def test_generic_remedy_fallback():
    # Test that a missing role without a specific remedy gets the generic one.
    from openfactory.policy import floor
    original_roles = floor.REQUIRED_VALIDATION_ROLES
    try:
        # Temporarily add a weird role
        floor.REQUIRED_VALIDATION_ROLES = frozenset(list(original_roles) + ["weird_role"])

        manifest = Manifest()
        reason = floor_reason(manifest)

        assert reason is not None
        assert "Declare a `weird_role:` gate" in reason
    finally:
        floor.REQUIRED_VALIDATION_ROLES = original_roles

def test_global_deny_paths_exist():
    # A test asserts every path named in GLOBAL_DENY still exists, so this cannot rot into prose again.
    from openfactory.policy.floor import GLOBAL_DENY

    repo_root = Path(__file__).parent.parent

    for deny, description in GLOBAL_DENY.items():
        # parse the file path from the description
        # Usually it's the first word separated by :: or similar, or just spaces
        file_path_str = description.split(" ")[0].split("::")[0].strip(";")

        file_path = repo_root / file_path_str

        assert file_path.exists(), f"Path {file_path_str} mentioned in GLOBAL_DENY['{deny}'] does not exist"

        # if there is a ::, the next part is a function or variable name
        if "::" in description.split(" ")[0]:
            target_name = description.split(" ")[0].split("::")[1].strip(";")
            content = file_path.read_text()
            assert target_name in content, f"Target '{target_name}' mentioned in GLOBAL_DENY['{deny}'] not found in {file_path_str}"
