from app.agents.claim_analyzer import ClaimAnalyzer
from app.models.schemas import (
    Claim,
    ClaimElementMapping,
)


def test_claim_analyzer():

    claim = Claim(
        claim_number="1",
        text="A device comprising a processor."
    )

    mapping = ClaimElementMapping(
        claim_element_id="1.1",
        supported=True,
        confidence=0.95,
        evidence=[],
        reasoning="The evidence supports the claim element."
    )

    analyzer = ClaimAnalyzer()

    result = analyzer.analyze(
        claim,
        [mapping]
    )

    assert result.claim_number == "1"
    assert result.coverage_status == "NOT_SUPPORTED"
    assert result.confidence == 0.0
    assert result.element_mappings == []
    assert result.reasoning == (
        "Claim analysis not yet implemented."
    )
