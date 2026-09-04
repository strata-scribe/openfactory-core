import pytest
from openfactory.semver import parse, bump, suggest, Version, _cmp_prerelease

def test_parse_valid():
    assert tuple(parse("1.2.3")) == (1, 2, 3)
    assert tuple(parse("v1.2.3")) == (1, 2, 3)
    assert tuple(parse("0.0.0")) == (0, 0, 0)
    assert tuple(parse("v0.0.0")) == (0, 0, 0)

    # Prerelease tags
    v = parse("1.2.3-alpha")
    assert (v.major, v.minor, v.patch, v.prerelease, v.build) == (1, 2, 3, "alpha", "")

    v = parse("v1.2.3-alpha.1")
    assert (v.major, v.minor, v.patch, v.prerelease, v.build) == (1, 2, 3, "alpha.1", "")

    # Build metadata
    v = parse("1.2.3+build.123")
    assert (v.major, v.minor, v.patch, v.prerelease, v.build) == (1, 2, 3, "", "build.123")

    # Prerelease + Build metadata
    v = parse("v1.0.0-beta+exp.sha.5114f85")
    assert (v.major, v.minor, v.patch, v.prerelease, v.build) == (1, 0, 0, "beta", "exp.sha.5114f85")

def test_parse_invalid():
    # Not a version
    assert tuple(parse("not a version")) == (0, 0, 0)
    assert tuple(parse("1.2")) == (0, 0, 0)
    assert tuple(parse("1.2.3.4")) == (0, 0, 0)
    assert tuple(parse(None)) == (0, 0, 0)
    assert tuple(parse("")) == (0, 0, 0)

    # Invalid prerelease (leading zeros for numeric) or invalid characters
    # Note: the regex in _V might capture it or not depending on strictness.
    # We at least want to ensure it falls back gracefully or ignores it.
    assert tuple(parse("1.0.0-0123")) == (0, 0, 0)

def test_comparison_operations():
    v1 = parse("1.0.0")
    v2 = parse("2.0.0")
    v1_1 = parse("1.1.0")
    v1_0_1 = parse("1.0.1")

    # Basic numeric comparison
    assert v1 < v2
    assert v2 > v1
    assert v1 <= v1
    assert v2 >= v1
    assert v1 == parse("1.0.0")
    assert v1 != v2

    assert v1 < v1_0_1 < v1_1 < v2

    # Prerelease comparison
    alpha = parse("1.0.0-alpha")
    alpha_1 = parse("1.0.0-alpha.1")
    alpha_beta = parse("1.0.0-alpha.beta")
    beta = parse("1.0.0-beta")
    beta_2 = parse("1.0.0-beta.2")
    beta_11 = parse("1.0.0-beta.11")
    rc_1 = parse("1.0.0-rc.1")
    release = parse("1.0.0")

    # 1.0.0-alpha < 1.0.0-alpha.1 < 1.0.0-alpha.beta < 1.0.0-beta < 1.0.0-beta.2 < 1.0.0-beta.11 < 1.0.0-rc.1 < 1.0.0
    sequence = [alpha, alpha_1, alpha_beta, beta, beta_2, beta_11, rc_1, release]
    for i in range(len(sequence) - 1):
        assert sequence[i] < sequence[i + 1]
        assert sequence[i] <= sequence[i + 1]
        assert sequence[i + 1] > sequence[i]
        assert sequence[i + 1] >= sequence[i]
        assert sequence[i] != sequence[i + 1]

    # Build metadata should be ignored in precedence
    v1_build1 = parse("1.0.0+build.1")
    v1_build2 = parse("1.0.0+build.2")
    assert v1 == v1_build1
    assert v1 == v1_build2
    assert v1_build1 == v1_build2
    assert not (v1_build1 < v1_build2)
    assert not (v1_build1 > v1_build2)

def test_sort_ordering():
    versions_str = [
        "1.0.0",
        "1.0.0-rc.1",
        "1.0.0-beta.11",
        "1.0.0-beta.2",
        "1.0.0-beta",
        "1.0.0-alpha.beta",
        "1.0.0-alpha.1",
        "1.0.0-alpha",
        "0.9.0",
        "2.0.0",
        "1.1.0"
    ]
    parsed_versions = [parse(v) for v in versions_str]
    sorted_versions = sorted(parsed_versions)

    expected_order = [
        "0.9.0",
        "1.0.0-alpha",
        "1.0.0-alpha.1",
        "1.0.0-alpha.beta",
        "1.0.0-beta",
        "1.0.0-beta.2",
        "1.0.0-beta.11",
        "1.0.0-rc.1",
        "1.0.0",
        "1.1.0",
        "2.0.0"
    ]

    assert [str(v) for v in sorted_versions] == expected_order

def test_bump():
    assert bump("1.2.3", "patch") == "1.2.4"
    assert bump("1.2.3", "minor") == "1.3.0"
    assert bump("1.2.3", "major") == "2.0.0"

    assert bump("v1.2.3", "patch") == "1.2.4"
    assert bump("v1.2.3-alpha", "patch") == "1.2.4" # Prerelease info is wiped on bump in existing logic
    assert bump("v1.2.3+build", "patch") == "1.2.4"

def test_suggest():
    res = suggest("1.2.3")
    assert res == {
        "current": "1.2.3",
        "patch": "1.2.4",
        "minor": "1.3.0",
        "major": "2.0.0"
    }

    res_none = suggest(None)
    assert res_none == {
        "current": "0.0.0",
        "patch": "0.0.1",
        "minor": "0.1.0",
        "major": "1.0.0"
    }

def test_cmp_prerelease():
    # Helper direct test
    assert _cmp_prerelease("", "") == 0
    assert _cmp_prerelease("alpha", "") == -1
    assert _cmp_prerelease("", "alpha") == 1
    assert _cmp_prerelease("alpha", "alpha") == 0
    assert _cmp_prerelease("alpha", "beta") == -1
    assert _cmp_prerelease("beta", "alpha") == 1
    assert _cmp_prerelease("alpha.1", "alpha.2") == -1
    assert _cmp_prerelease("alpha.2", "alpha.1") == 1
    assert _cmp_prerelease("alpha.10", "alpha.2") == 1  # 10 > 2 numerically
