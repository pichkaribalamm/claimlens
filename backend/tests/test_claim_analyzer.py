from app.agents.claim_analyzer import ClaimAnalyzer
from app.models.schemas import (
    Claim,
    ClaimElementMapping,
)


def test_claim_analyzer_fully_supported():

    claim = Claim(
        claim_number="1",
        text="A device comprising a processor."
    )

    mappings = [
        ClaimElementMapping(
            claim_element_id="1.1",
            supported=True,
            confidence=0.95,
            evidence=[],
            reasoning="The evidence supports the claim element."
        ),
        ClaimElementMapping(
            claim_element_id="1.2",
            supported=True,
            confidence=0.90,
            evidence=[],
            reasoning="The evidence supports the claim element."
        ),
    ]

    analyzer = ClaimAnalyzer()

    result = analyzer.analyze(
        claim,
        mappings
    )

    assert result.claim_number == "1"
    assert result.coverage_status == "FULLY_SUPPORTED"
    assert result.confidence == 0.90
    assert result.element_mappings == mappings
    assert result.reasoning == (
        "All claim elements are supported by the available "
        "technical evidence."
    )


def test_claim_analyzer_partially_supported():

    claim = Claim(
        claim_number="1",
        text="A device comprising a processor."
    )

    mappings = [
        ClaimElementMapping(
            claim_element_id="1.1",
            supported=True,
            confidence=0.95,
            evidence=[],
            reasoning="The evidence supports the claim element."
        ),
        ClaimElementMapping(
            claim_element_id="1.2",
            supported=False,
            confidence=0.80,
            evidence=[],
            reasoning="No evidence supports this element."
        ),
    ]

    analyzer = ClaimAnalyzer()

    result = analyzer.analyze(
        claim,
        mappings
    )

    assert result.claim_number == "1"
    assert result.coverage_status == "PARTIALLY_SUPPORTED"
    assert result.confidence == 0.5
    assert result.element_mappings == mappings
    assert result.reasoning == (
        "1 of 2 claim elements are supported by the available "
        "technical evidence."
    )


def test_claim_analyzer_not_supported():

    claim = Claim(
        claim_number="1",
        text="A device comprising a processor."
    )

    mappings = [
        ClaimElementMapping(
            claim_element_id="1.1",
            supported=False,
            confidence=0.90,
            evidence=[],
            reasoning="No evidence supports this element."
        ),
        ClaimElementMapping(
            claim_element_id="1.2",
            supported=False,
            confidence=0.85,
            evidence=[],
            reasoning="No evidence supports this element."
        ),
    ]

    analyzer = ClaimAnalyzer()

    result = analyzer.analyze(
        claim,
        mappings
    )

    assert result.claim_number == "1"
    assert result.coverage_status == "NOT_SUPPORTED"
    assert result.confidence == 0.0
    assert result.element_mappings == mappings
    assert result.reasoning == (
        "None of the claim elements are supported by the "
        "available technical evidence."
    )


def test_claim_analyzer_without_mappings():

    claim = Claim(
        claim_number="1",
        text="A device comprising a processor."
    )

    analyzer = ClaimAnalyzer()

    result = analyzer.analyze(
        claim,
        []
    )

    assert result.claim_number == "1"
    assert result.coverage_status == "NOT_SUPPORTED"
    assert result.confidence == 0.0
    assert result.element_mappings == []
    assert result.reasoning == (
        "No claim-element mappings were provided."
    )
