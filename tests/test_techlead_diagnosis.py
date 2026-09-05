from __future__ import annotations

import pytest

from openfactory.contracts.decision import parse_handoff, HandOff

def test_parse_handoff_basic():
    text = """
    Some context here.
    ```json
    {
        "headline": "A test headline",
        "what_happened": "Something failed",
        "why": "Because of reasons",
        "correction": "This is a correction",
        "recommendation": "Do this",
        "alternatives": "Or do that",
        "suggested_command": "skip #123"
    }
    ```
    """
    ho = parse_handoff(text)
    assert ho is not None
    assert ho.headline == "A test headline"
    assert ho.what_happened == "Something failed"
    assert ho.why == "Because of reasons"
    assert ho.correction == "This is a correction"
    assert ho.recommendation == "Do this"
    assert ho.alternatives == "Or do that"
    assert ho.suggested_command == "skip #123"

def test_parse_handoff_no_json():
    text = "Just some text without any JSON blocks."
    ho = parse_handoff(text)
    assert ho is None

def test_parse_handoff_invalid_json():
    text = """
    ```json
    {
        "headline": "A test headline",
        "what_happened": "Something failed",
    ```
    """
    ho = parse_handoff(text)
    assert ho is None

def test_parse_handoff_multiple_json():
    text = """
    ```json
    {
        "headline": "First block"
    }
    ```
    Some text in between.
    ```json
    {
        "headline": "Second block",
        "what_happened": "Last one wins"
    }
    ```
    """
    ho = parse_handoff(text)
    assert ho is not None
    assert ho.headline == "Second block"
    assert ho.what_happened == "Last one wins"

def test_parse_handoff_unfenced_json():
    text = """
    Here is a block without markdown fences:
    {
        "headline": "Unfenced headline",
        "what_happened": "It works without fences"
    }
    """
    ho = parse_handoff(text)
    assert ho is not None
    assert ho.headline == "Unfenced headline"

def test_parse_handoff_missing_required_fields():
    text = """
    ```json
    {
        "why": "No headline or what_happened here"
    }
    ```
    """
    ho = parse_handoff(text)
    assert ho is None

def test_parse_handoff_with_issue():
    text = """
    ```json
    {
        "headline": "Issue test",
        "suggested_command": "skip #456"
    }
    ```
    """
    # Test valid suggested_command
    ho = parse_handoff(text, issue="456")
    assert ho is not None
    assert ho.suggested_command == "skip #456"

    # Test invalid suggested_command targeting wrong ticket
    ho_wrong = parse_handoff(text, issue="123")
    assert ho_wrong is not None
    assert ho_wrong.suggested_command == ""


def test_python_stack_trace_parsing():
    text = """
    We crashed with:
    ```json
    {
        "headline": "Python exception in job",
        "what_happened": "Traceback (most recent call last):\\n  File \\"main.py\\", line 10, in <module>\\n    main()\\nValueError: Invalid configuration",
        "why": "The root cause is a bad config",
        "recommendation": "Fix the config file"
    }
    ```
    """
    ho = parse_handoff(text)
    assert ho is not None
    assert "ValueError: Invalid configuration" in ho.what_happened
    assert ho.why == "The root cause is a bad config"

def test_go_stack_trace_parsing():
    text = """
    ```json
    {
        "headline": "Go panic",
        "what_happened": "panic: runtime error: index out of range [1] with length 1\\n\\ngoroutine 1 [running]:\\nmain.main()\\n\\t/app/main.go:5 +0x18",
        "why": "Array bounds exceeded",
        "recommendation": "Check array length before access"
    }
    ```
    """
    ho = parse_handoff(text)
    assert ho is not None
    assert "panic: runtime error: index out of range" in ho.what_happened
    assert "main.main()" in ho.what_happened
    assert ho.why == "Array bounds exceeded"

def test_error_root_cause_isolation():
    text = """
    ```json
    {
        "headline": "Build failed",
        "what_happened": "Error: ENOSPC: no space left on device, write",
        "why": "Disk is full, this is the root cause. Not a code issue.",
        "correction": "Previous assumption that it was a permission issue is wrong.",
        "recommendation": "Increase disk size or clear cache"
    }
    ```
    """
    ho = parse_handoff(text)
    assert ho is not None
    assert ho.headline == "Build failed"
    assert ho.what_happened == "Error: ENOSPC: no space left on device, write"
    assert "Disk is full" in ho.why
    assert "permission issue is wrong" in ho.correction

def test_automated_patch_suggestion_formatting():
    text = """
    ```json
    {
        "headline": "Typo in variable name",
        "what_happened": "NameError: name 'my_var' is not defined",
        "why": "The variable is actually named 'my_variable'",
        "recommendation": "Apply this patch:\\n```diff\\n- print(my_var)\\n+ print(my_variable)\\n```",
        "suggested_command": "resume #999"
    }
    ```
    """
    ho = parse_handoff(text, issue="999")
    assert ho is not None
    assert "```diff" in ho.recommendation
    assert "- print(my_var)" in ho.recommendation
    assert "+ print(my_variable)" in ho.recommendation
    assert ho.suggested_command == "resume #999"
