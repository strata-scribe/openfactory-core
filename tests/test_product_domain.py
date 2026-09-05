import pytest
from datetime import date
from openfactory.product.domain import (
    Domain, Fact, load_domain, parse_facts, render_file, render_fact,
    LEARNED, CONFIRMED, RETIRED
)

def test_domain_metadata_persistence(tmp_path):
    facts = [
        Fact(
            term="Invoice",
            status=CONFIRMED,
            source="Accountant",
            where="Email",
            learned_on="2023-01-01",
            body="An invoice is a bill."
        ),
        Fact(
            term="Receipt",
            status=LEARNED,
            source="Clerk",
            where="Chat",
            learned_on="2023-01-02",
            body="A receipt is proof of payment."
        )
    ]

    file_content = render_file(facts, title="Financial Terms", intro="Intro text")

    f = tmp_path / "domain_facts.md"
    f.write_text(file_content, encoding="utf-8")

    parsed_facts, findings = parse_facts(f.read_text(encoding="utf-8"))
    assert len(findings) == 0
    assert len(parsed_facts) == 2

    invoice = next(f for f in parsed_facts if f.term == "Invoice")
    assert invoice.status == CONFIRMED
    assert invoice.source == "Accountant"
    assert invoice.where == "Email"
    assert invoice.learned_on == "2023-01-01"
    assert invoice.body == "An invoice is a bill."

    receipt = next(f for f in parsed_facts if f.term == "Receipt")
    assert receipt.status == LEARNED
    assert receipt.source == "Clerk"
    assert receipt.where == "Chat"
    assert receipt.learned_on == "2023-01-02"
    assert receipt.body == "A receipt is proof of payment."


def test_cross_domain_access_checks(tmp_path):
    # A non-existent directory results in an empty domain, no failure
    missing_dir = tmp_path / "does_not_exist"
    empty_domain = load_domain(missing_dir)
    assert not empty_domain.facts
    assert not empty_domain.findings

    # Two distinct directories should not contaminate each other
    dir_a = tmp_path / "domain_a"
    dir_a.mkdir()
    (dir_a / "fact_a.md").write_text("""### Term A\n- Fonte: A\n- Data: 2023-01-01\nBody A""", encoding="utf-8")

    dir_b = tmp_path / "domain_b"
    dir_b.mkdir()
    (dir_b / "fact_b.md").write_text("""### Term B\n- Fonte: B\n- Data: 2023-01-02\nBody B""", encoding="utf-8")

    domain_a = load_domain(dir_a)
    assert len(domain_a.facts) == 1
    assert domain_a.facts[0].term == "Term A"

    domain_b = load_domain(dir_b)
    assert len(domain_b.facts) == 1
    assert domain_b.facts[0].term == "Term B"


def test_domain_scoping_duplicate_terms(tmp_path):
    dir_c = tmp_path / "domain_c"
    dir_c.mkdir()

    # Same term in different files inside the same domain
    (dir_c / "file1.md").write_text("""### Duplicated\n- Fonte: C1\n- Data: 2023-01-01\nBody 1""", encoding="utf-8")
    (dir_c / "file2.md").write_text("""### duplicated\n- Fonte: C2\n- Data: 2023-01-02\nBody 2""", encoding="utf-8")

    domain_c = load_domain(dir_c)
    # The first one is kept
    assert len(domain_c.facts) == 1
    assert domain_c.facts[0].source == "C1"

    # But a finding is emitted
    assert len(domain_c.findings) == 1
    assert domain_c.findings[0].code == "duplicate-term"


def test_domain_scoping_missing_metadata(tmp_path):
    # Tests that missing metadata emits appropriate findings
    content = """### No Metadata
Body without metadata
"""
    facts, findings = parse_facts(content)
    assert len(facts) == 1
    assert len(findings) == 2
    codes = [f.code for f in findings]
    assert "no-source" in codes
    assert "no-date" in codes

    assert facts[0].status == LEARNED
