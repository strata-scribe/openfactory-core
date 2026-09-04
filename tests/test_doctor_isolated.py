import pytest
from unittest.mock import MagicMock, patch

from openfactory import namespace
from openfactory.doctor import Probes, Finding, _agent_cred, _manifest, _harness, _docker

def test_agent_cred_environment_variables():
    # Test when agent credential check returns False (environment variables missing)
    probes_mock = MagicMock(spec=Probes)
    probes_mock.agent_credential = MagicMock(return_value=(False, "no agent credential in this environment"))

    finding = _agent_cred(probes_mock)

    assert finding.ok is False
    assert finding.check == "agent_credential"
    assert "no agent credential" in finding.message
    assert "CLAUDE_CODE_OAUTH_TOKEN" in finding.remedy

    # Test when agent credential check returns True (environment variables present)
    probes_mock.agent_credential = MagicMock(return_value=(True, ""))

    finding = _agent_cred(probes_mock)
    assert finding.ok is True
    assert finding.check == "agent_credential"


def test_manifest_directory_existence_retired_namespace():
    probes_mock = MagicMock(spec=Probes)

    # Simulate directory existence failure when using retired namespace
    def mock_manifest_retired():
        raise namespace.RetiredNamespace(f"directory {namespace.RETIRED_DIR} found instead of {namespace.DIR}")

    probes_mock.manifest = mock_manifest_retired

    finding = _manifest(probes_mock)
    assert finding.ok is False
    assert finding.check == "manifest"
    assert "rename the directory" in finding.remedy
    assert namespace.RETIRED_DIR in finding.remedy


def test_manifest_directory_existence_file_not_found():
    probes_mock = MagicMock(spec=Probes)

    # Simulate directory/file existence failure when manifest is completely missing
    def mock_manifest_missing():
        raise FileNotFoundError("No manifest found")

    probes_mock.manifest = mock_manifest_missing
    probes_mock.open_proposal = MagicMock(return_value="")

    finding = _manifest(probes_mock)
    assert finding.ok is False
    assert finding.check == "manifest"
    assert "missing" in finding.message


def test_harness_file_permissions():
    probes_mock = MagicMock(spec=Probes)
    probes_mock.harness_kind = MagicMock(return_value="dummy_harness")

    # Simulate file permissions / executable check where harness is NOT on path
    probes_mock.harness_on_path = MagicMock(return_value=False)

    finding = _harness(probes_mock)
    assert finding.ok is False
    assert finding.check == "harness"
    assert "is not on PATH" in finding.message

    # Simulate file permissions / executable check where harness IS on path
    probes_mock.harness_on_path = MagicMock(return_value=True)

    finding = _harness(probes_mock)
    assert finding.ok is True
    assert finding.check == "harness"
    assert "is on PATH" in finding.message


def test_docker_file_permissions_and_executable():
    probes_mock = MagicMock(spec=Probes)

    # Simulate docker CLI file permissions / missing binary
    probes_mock.docker_running = MagicMock(return_value=(False, "the docker CLI is not installed in this environment"))

    finding = _docker(probes_mock)
    assert finding.ok is False
    assert finding.check == "docker"
    assert "docker CLI is not installed" in finding.message
    assert "install the docker CLI" in finding.remedy

    # Simulate docker running correctly
    probes_mock.docker_running = MagicMock(return_value=(True, ""))

    finding = _docker(probes_mock)
    assert finding.ok is True
    assert finding.check == "docker"
    assert "running" in finding.message

def test_forge_git_hygiene():
    from openfactory.doctor import _forge

    probes_mock = MagicMock(spec=Probes)

    # Simulate git hygiene failure / unreachability
    probes_mock.forge_reachable = MagicMock(return_value=(False, "no forge credential"))

    finding = _forge(probes_mock)
    assert finding.ok is False
    assert finding.check == "forge_access"
    assert "no forge credential" in finding.message

    # Simulate git hygiene success
    probes_mock.forge_reachable = MagicMock(return_value=(True, ""))

    finding = _forge(probes_mock)
    assert finding.ok is True
    assert finding.check == "forge_access"
