import pytest
from openfactory.util.causes import first_message, describe, scrubbed, _chain

def test_structured_cause_extraction_finds_deep_cause():
    """Test structured cause extraction."""
    err1 = ValueError("root cause")
    err2 = RuntimeError("middle")
    err3 = Exception("top")
    err2.__cause__ = err1
    err3.__cause__ = err2

    assert list(_chain(err3)) == [err3, err2, err1]
    assert first_message(err3) == "top"

def test_structured_cause_extraction_skips_placeholders():
    """Test structured cause extraction with placeholders."""
    err1 = ValueError("real reason")
    err2 = RuntimeError("activity task failed")
    err3 = Exception("workflow execution failed")
    err2.__cause__ = err1
    err3.__cause__ = err2

    # It should skip the placeholders and find the real reason
    assert first_message(err3) == "real reason"

def test_nested_error_chain_formatting():
    """Test nested error chain formatting."""
    err1 = ValueError("root cause")
    err2 = RuntimeError("middle")
    err3 = Exception("top")
    err2.__cause__ = err1
    err3.__cause__ = err2

    assert describe(err3) == "Exception: top"

def test_nested_error_chain_formatting_with_placeholders():
    """Test nested error chain formatting with placeholders."""
    err1 = ValueError("root cause")
    err2 = RuntimeError("activity task failed")
    err3 = Exception("workflow execution failed")
    err2.__cause__ = err1
    err3.__cause__ = err2

    # It should skip the placeholders and describe the real reason
    assert describe(err3) == "ValueError: root cause"

def test_diagnostic_context_attachment_chaining():
    """Test diagnostic context attachment chaining (__context__)."""
    err1 = ValueError("underlying context")
    err2 = RuntimeError("middle")
    err3 = Exception("top")
    err2.__context__ = err1
    err3.__context__ = err2

    assert list(_chain(err3)) == [err3, err2, err1]

def test_diagnostic_context_attachment_scrubbing():
    """Test diagnostic context attachment and scrubbing."""
    err = ValueError("Failed to clone https://x-access-token:live-token@github.com/repo")

    # Scrubbing secrets
    assert scrubbed(err, "live-token") == "Failed to clone https://x-access-token:***@github.com/repo"

    # Multiple secrets
    assert scrubbed(err, "live-token", "github.com") == "Failed to clone https://x-access-token:***@***/repo"

    # Truncation happens after scrubbing
    assert scrubbed(err, "live-token", limit=40) == "Failed to clone https://x-access-token:*"

def test_diagnostic_context_attachment_scrubbed_ignores_empty_secrets():
    """Test scrubbing with empty secrets."""
    err = ValueError("Something failed")
    assert scrubbed(err, "") == "Something failed"
