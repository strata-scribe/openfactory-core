import pytest
import logging
from openfactory.policy.authz import may, is_admin, FACTORY, PRODUCT
from openfactory.identity.base import Subject, UNKNOWN

class MockProductConfig:
    def __init__(self, admins=None, enabled=True):
        self.admins = admins or []
        self.enabled = enabled

class MockProject:
    def __init__(self, admins=None, product=None):
        self.admins = admins or []
        self.product = product

def test_may_with_subject_id_in_allowlist():
    subject = Subject(id="user1", via="test")
    project = MockProject(admins=["user1", "user2"])

    decision = may(subject, project=project, scope=FACTORY)
    assert decision.allowed is True
    assert bool(decision) is True

def test_may_with_subject_group_in_allowlist():
    subject = Subject(id="user3", groups=("admin-group",), via="test")
    project = MockProject(admins=["user1", "admin-group"])

    decision = may(subject, project=project, scope=FACTORY)
    assert decision.allowed is True

def test_may_with_empty_allowlist_rejects():
    subject = Subject(id="user1", groups=("admin-group",), via="test")
    project = MockProject(admins=[])

    decision = may(subject, project=project, scope=FACTORY)
    assert decision.allowed is False
    assert "not on this project's factory allowlist" in decision.why

def test_may_with_neither_id_nor_group_in_allowlist():
    subject = Subject(id="user3", groups=("other-group",), via="test")
    project = MockProject(admins=["user1", "admin-group"])

    decision = may(subject, project=project, scope=FACTORY)
    assert decision.allowed is False

def test_may_unknown_subject_rejected():
    project = MockProject(admins=["user1"])
    decision = may(UNKNOWN, project=project, scope=FACTORY)
    assert decision.allowed is False
    assert "could not tell who is asking" in decision.why

def test_may_none_subject_rejected():
    project = MockProject(admins=["user1"])
    decision = may(None, project=project, scope=FACTORY)
    assert decision.allowed is False
    assert "could not tell who is asking" in decision.why

def test_may_unknown_scope_rejected(caplog):
    subject = Subject(id="user1", via="test")
    project = MockProject(admins=["user1"])

    with caplog.at_level(logging.ERROR):
        decision = may(subject, project=project, scope="invalid-scope")

    assert decision.allowed is False
    assert "unknown authorization scope" in decision.why
    assert "OPENFACTORY_AUTHZ_UNKNOWN_SCOPE" in caplog.text

def test_may_product_scope_enabled():
    subject = Subject(id="prod-user", via="test")
    project = MockProject(product=MockProductConfig(admins=["prod-user"]))

    decision = may(subject, project=project, scope=PRODUCT)
    assert decision.allowed is True

def test_may_product_scope_disabled():
    subject = Subject(id="prod-user", via="test")
    project = MockProject(product=MockProductConfig(admins=["prod-user"], enabled=False))

    decision = may(subject, project=project, scope=PRODUCT)
    assert decision.allowed is False
    assert "not enabled" in decision.why

def test_may_product_scope_no_product_config():
    subject = Subject(id="prod-user", via="test")
    project = MockProject(product=None)

    decision = may(subject, project=project, scope=PRODUCT)
    assert decision.allowed is False
    assert "not enabled" in decision.why

def test_is_admin_helper():
    subject1 = Subject(id="user1", via="test")
    subject2 = Subject(id="user2", via="test")
    project = MockProject(admins=["user1"])

    assert is_admin(subject1, project) is True
    assert is_admin(subject2, project) is False
