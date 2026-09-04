import pytest
from openfactory.review.verdict import ReviewVerdict

def test_review_verdict_aggregation():
    verdicts = [
        ReviewVerdict(decision="approved", confidence=0.8),
        ReviewVerdict(decision="approved", confidence=0.9)
    ]

    result = ReviewVerdict.aggregate(verdicts)
    assert result.decision == "approved"
    assert pytest.approx(result.confidence) == 0.85

def test_review_verdict_aggregation_empty():
    with pytest.raises(ValueError):
        ReviewVerdict.aggregate([])

def test_review_verdict_conflicting_vote_resolution():
    verdicts = [
        ReviewVerdict(decision="approved", confidence=0.8),
        ReviewVerdict(decision="rejected", confidence=0.9)
    ]

    result = ReviewVerdict.resolve_conflicts(verdicts)
    assert result.decision == "rejected"
    assert result.confidence == 0.9

def test_review_verdict_conflicting_vote_resolution_empty():
    with pytest.raises(ValueError):
        ReviewVerdict.resolve_conflicts([])

def test_review_verdict_confidence_weighted_consensus():
    verdicts = [
        ReviewVerdict(decision="approved", confidence=0.4),
        ReviewVerdict(decision="approved", confidence=0.4),
        ReviewVerdict(decision="rejected", confidence=0.9)
    ]

    result = ReviewVerdict.confidence_weighted_consensus(verdicts)
    assert result.decision == "rejected"
    assert pytest.approx(result.confidence) == 0.9 / 1.7

def test_review_verdict_confidence_weighted_consensus_empty():
    with pytest.raises(ValueError):
        ReviewVerdict.confidence_weighted_consensus([])
