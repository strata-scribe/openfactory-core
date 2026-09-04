import pytest
from openfactory.credentials import redact

def test_redact_url_credentials():
    assert redact("https://user:password@github.com/repo") == "https://***@github.com/repo"
    assert redact("http://token@example.com") == "http://***@example.com"
    assert redact("https://github.com") == "https://github.com"

def test_redact_private_keys():
    key = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----"
    expected = "-----BEGIN PRIVATE KEY-----\n***\n-----END PRIVATE KEY-----"
    assert redact(key) == expected

def test_redact_tokens_and_secrets():
    assert redact("Authorization: Bearer abcdef1234567890abcdef1234567890") == "Authorization: Bearer: ***"
    assert redact('my_token="abcdef1234567890abcdef1234567890"') == 'my_token: ***'
    assert redact("AWS_SECRET_ACCESS_KEY=abcdef1234567890abcdef1234567890") == "AWS_SECRET_ACCESS_KEY: ***"
    assert redact("ghp_1234567890abcdef1234567890abcdef12") == "***"

def test_no_false_positives():
    assert redact("This is a normal sentence.") == "This is a normal sentence."
    assert redact("{" + '"key": "value"' + "}") == "{" + '"key": "value"' + "}"

def test_zero_network_calls(monkeypatch):
    import socket
    def block_network(*args, **kwargs):
        raise RuntimeError("Network call blocked")
    monkeypatch.setattr(socket, "socket", block_network)

    redact("https://user:password@example.com")

def test_redact_base64_credentials():
    assert redact("Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=") == "Authorization: Basic: ***"
    assert redact("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c") == "***"
    assert redact("abc/def/ghi/jkl/mno/pqr/stu/vwx/yzA=B+C") == "***"
