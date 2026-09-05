from __future__ import annotations

import os
import subprocess
import pytest
from unittest import mock

from openfactory.runtime import boxed_job as ep
from openfactory.contracts.state import JobState
from openfactory.contracts import RunResult

# Tests for exception handling (timeout and memory limits) and exit code captures.

def test_main_catches_timeout_and_returns_1(monkeypatch, capsys):
    monkeypatch.setenv("OPENFACTORY_PROJECT", "p")
    monkeypatch.setenv("OPENFACTORY_ISSUE", "5")
    monkeypatch.setenv("OPENFACTORY_REPO", "o/r")
    monkeypatch.setattr(ep, "materialize_app_key", lambda env, dest_dir: None)

    def raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="git", timeout=300)

    monkeypatch.setattr(ep, "run_boxed", raise_timeout)

    rc = ep.main()
    assert rc == 1

    out = capsys.readouterr().out
    assert ep.RESULT_PREFIX in out
    assert '"state":"failed"' in out.replace(" ", "")
    assert "box failed: Command 'git' timed out after 300 seconds" in out

def test_main_catches_memory_error_and_returns_1(monkeypatch, capsys):
    monkeypatch.setenv("OPENFACTORY_PROJECT", "p")
    monkeypatch.setenv("OPENFACTORY_ISSUE", "5")
    monkeypatch.setenv("OPENFACTORY_REPO", "o/r")
    monkeypatch.setattr(ep, "materialize_app_key", lambda env, dest_dir: None)

    def raise_memory_error(*args, **kwargs):
        raise MemoryError("out of memory")

    monkeypatch.setattr(ep, "run_boxed", raise_memory_error)

    rc = ep.main()
    assert rc == 1

    out = capsys.readouterr().out
    assert ep.RESULT_PREFIX in out
    assert '"state":"failed"' in out.replace(" ", "")
    assert "box failed: out of memory" in out

def test_main_returns_0_when_state_is_done(monkeypatch):
    monkeypatch.setenv("OPENFACTORY_PROJECT", "p")
    monkeypatch.setenv("OPENFACTORY_ISSUE", "5")
    monkeypatch.setenv("OPENFACTORY_REPO", "o/r")
    monkeypatch.setattr(ep, "materialize_app_key", lambda env, dest_dir: None)

    def mock_run_boxed(*args, **kwargs):
        class MockState:
            value = "merged"

        class MockResult:
            state = MockState()

            def model_dump_json(self):
                return '{"state":"merged"}'

        return MockResult()

    monkeypatch.setattr(ep, "run_boxed", mock_run_boxed)

    rc = ep.main()
    assert rc == 0

def test_main_returns_1_when_state_is_not_done(monkeypatch):
    monkeypatch.setenv("OPENFACTORY_PROJECT", "p")
    monkeypatch.setenv("OPENFACTORY_ISSUE", "5")
    monkeypatch.setenv("OPENFACTORY_REPO", "o/r")
    monkeypatch.setattr(ep, "materialize_app_key", lambda env, dest_dir: None)

    def mock_run_boxed(*args, **kwargs):
        class MockState:
            value = "on_hold"

        class MockResult:
            state = MockState()

            def model_dump_json(self):
                return '{"state":"on_hold"}'

        return MockResult()

    monkeypatch.setattr(ep, "run_boxed", mock_run_boxed)

    rc = ep.main()
    assert rc == 1
