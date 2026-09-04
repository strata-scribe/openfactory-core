from openfactory.contracts import Component, Manifest, RunResult
from openfactory.contracts.state import RiskLevel
from openfactory.orchestrator.risk import RiskAssessment, assess, of_attempt


def test_assess_with_no_components():
    manifest = Manifest(components={})
    assessment = assess(["src/main.py"], manifest)
    assert assessment.declares_nothing is True
    assert assessment.undeclared is False
    assert assessment.needs_a_human is False
    assert assessment.level is None
    assert assessment.undeclared_paths == ("src/main.py",)
    assert assessment.undeclared_count == 1
    assert assessment.note == "risk: not expressed — this manifest declares no components"


def test_assess_with_no_diff():
    manifest = Manifest(components={"app": Component(path="src/", stack="python")})
    assessment = assess([], manifest)
    assert assessment.declares_nothing is False
    assert assessment.undeclared is False
    assert assessment.needs_a_human is False
    assert assessment.level is None
    assert assessment.undeclared_paths == ()
    assert assessment.undeclared_count == 0
    assert assessment.note == "risk: UNDECLARED — nothing the manifest describes covers this change"


def test_assess_with_undeclared_paths():
    manifest = Manifest(components={"app": Component(path="src/", stack="python")})
    assessment = assess(["src/main.py", "docs/README.md"], manifest)
    assert assessment.declares_nothing is False
    assert assessment.undeclared is True
    assert assessment.needs_a_human is True
    assert assessment.level == RiskLevel.NORMAL
    assert assessment.undeclared_paths == ("docs/README.md",)
    assert assessment.undeclared_count == 1
    assert assessment.touched == ("app",)


def test_assess_levels():
    manifest = Manifest(components={
        "low_risk": Component(path="docs/", stack="python", risk="low"),
        "normal_risk": Component(path="src/", stack="python", risk="normal"),
        "high_risk": Component(path="infra/", stack="terraform", risk="high"),
    })

    # Touch normal and low
    assessment = assess(["docs/api.md", "src/main.py"], manifest)
    assert assessment.level == RiskLevel.NORMAL
    assert assessment.driven_by == ("normal_risk",)
    assert assessment.touched == ("low_risk", "normal_risk")
    assert assessment.needs_a_human is False

    # Touch high and normal
    assessment = assess(["src/main.py", "infra/main.tf"], manifest)
    assert assessment.level == RiskLevel.HIGH
    assert assessment.driven_by == ("high_risk",)
    assert assessment.touched == ("high_risk", "normal_risk")
    assert assessment.needs_a_human is True

    # Touch low only
    assessment = assess(["docs/api.md"], manifest)
    assert assessment.level == RiskLevel.LOW
    assert assessment.driven_by == ("low_risk",)
    assert assessment.needs_a_human is False


def test_of_attempt_legacy_result():
    manifest = Manifest(components={"app": Component(path="src/", stack="python")})
    # Older RunResult might not have undeclared_paths or undeclared_count
    result = RunResult(
        ticket_id="#1",
        state="pr_open",
        touched_components=["app"]
    )
    # The fields should be mapped back to default values
    assessment = of_attempt(manifest, result)
    assert assessment.touched == ("app",)
    assert assessment.undeclared_paths == ()
    assert assessment.undeclared_count == 0
    assert assessment.undeclared is False

def test_of_attempt_with_undeclared():
    manifest = Manifest(components={"app": Component(path="src/", stack="python")})
    result = RunResult(
        ticket_id="#1",
        state="pr_open",
        touched_components=["app"],
        undeclared_paths=["docs/README.md"],
        undeclared_count=1
    )
    assessment = of_attempt(manifest, result)
    assert assessment.touched == ("app",)
    assert assessment.undeclared_paths == ("docs/README.md",)
    assert assessment.undeclared_count == 1
    assert assessment.undeclared is True
    assert assessment.needs_a_human is True

def test_risk_assessment_note_formatting():
    # 1. Declares nothing
    assessment = RiskAssessment(declares_nothing=True)
    assert assessment.note == "risk: not expressed — this manifest declares no components"

    # 2. Level none, with undeclared paths
    assessment = RiskAssessment(level=None, undeclared_paths=("docs/README.md",), undeclared_count=1)
    assert assessment.note == "risk: UNDECLARED — nothing the manifest describes covers this change · 1 path(s) no component declares: `docs/README.md`"

    # 3. Level normal, with no undeclared
    assessment = RiskAssessment(level=RiskLevel.NORMAL, driven_by=("app",))
    assert assessment.note == "risk: normal (app)"

    # 4. Level high, with multiple driven by and undeclared paths but truncated
    assessment = RiskAssessment(
        level=RiskLevel.HIGH,
        driven_by=("infra", "db"),
        undeclared_paths=("docs/README.md",),
        undeclared_count=3
    )
    assert assessment.note == "risk: high (infra, db) · 3 path(s) no component declares: `docs/README.md` and 2 more"

def test_risk_assessment_needs_a_human():
    # Only HIGH level or undeclared paths true requires a human.
    assert RiskAssessment(level=RiskLevel.LOW).needs_a_human is False
    assert RiskAssessment(level=RiskLevel.NORMAL).needs_a_human is False
    assert RiskAssessment(level=RiskLevel.HIGH).needs_a_human is True
    assert RiskAssessment(level=RiskLevel.LOW, undeclared_paths=("docs/",), declares_nothing=False).needs_a_human is True
    # If declares nothing, undeclared is false, so no human needed.
    assert RiskAssessment(level=None, undeclared_paths=("docs/",), declares_nothing=True).needs_a_human is False
