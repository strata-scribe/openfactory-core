import pytest
from openfactory.policy.floor import FloorPolicy

def test_floor_policy_verification():
    valid_policy = FloorPolicy({"coverage": 85, "security_enabled": True})
    assert valid_policy.verify() is True

    invalid_policy = FloorPolicy({"coverage": 70, "security_enabled": True})
    assert invalid_policy.verify() is False

    invalid_policy_sec = FloorPolicy({"coverage": 90, "security_enabled": False})
    assert invalid_policy_sec.verify() is False

def test_minimum_coverage_requirements():
    policy_high = FloorPolicy({"coverage": 90})
    assert policy_high.check_minimum_coverage() is True

    policy_exact = FloorPolicy({"coverage": 80})
    assert policy_exact.check_minimum_coverage() is True

    policy_low = FloorPolicy({"coverage": 79})
    assert policy_low.check_minimum_coverage() is False

    policy_none = FloorPolicy({})
    assert policy_none.check_minimum_coverage() is False

def test_security_floor_enforcement():
    policy_secure = FloorPolicy({"security_enabled": True})
    assert policy_secure.enforce_security_floor() is True

    policy_insecure = FloorPolicy({"security_enabled": False})
    assert policy_insecure.enforce_security_floor() is False

    policy_none = FloorPolicy({})
    assert policy_none.enforce_security_floor() is False
