from unittest.mock import patch

from app.agents.claim_mapper import ClaimMapper
from app.models.schemas import (
    ClaimElement,
    Evidence,
    EvidenceVerificationResult,
    VerifiedEvidence,
)


def test_claim_mapper():

    element = ClaimElement(
        id="1.2",
        claim_number="1",
        text="an AI image signal processor (ISP) associated with the front camera"
    )

    evidence = Evidence(
        claim_element_id="1.2",
        source_title="Samsung Galaxy S26 Ultra",
        url="https://www.samsung.com/in/smartphones/galaxy-s26-ultra/",
        excerpt=(
            "Galaxy S26 Ultra's front camera now features "
            "an AI image signal processor (ISP)"
        ),
        evidence_type="direct",
        relevance=(
            "The source explicitly confirms that the front camera "
            "features an AI image signal processor (ISP)."
        )
    )

    verification = EvidenceVerificationResult(
        claim_element_id="1.2",
        evidence_supported=True,
        confidence=0.98,
        reasoning=(
            "The evidence excerpt explicitly states that the front "
            "camera features an AI image signal processor (ISP)."
        )
    )

    verified_evidence = VerifiedEvidence(
        evidence=evidence,
        verification=verification,
    )

    fake_gemini_response = """
    {
        "claim_element_id": "1.2",
        "supported": true,
        "confidence": 0.98,
        "evidence": [
            {
                "claim_element_id": "1.2",
                "source_title": "Samsung Galaxy S26 Ultra",
                "url": "https://www.samsung.com/in/smartphones/galaxy-s26-ultra/",
                "excerpt": "Galaxy S26 Ultra's front camera now features an AI image signal processor (ISP)",
                "evidence_type": "direct",
                "relevance": "The source explicitly confirms that the front camera features an AI image signal processor (ISP)."
            }
        ],
        "reasoning": "The verified evidence directly supports the claim element."
    }
    """

    with patch(
        "app.agents.claim_mapper.GeminiService"
    ) as mock_gemini:

        mock_gemini.return_value.generate.return_value = (
            fake_gemini_response
        )

        mapper = ClaimMapper()

        result = mapper.map(
            element,
            [verified_evidence]
        )

    assert result.claim_element_id == "1.2"
    assert result.supported is True
    assert result.confidence == 0.98
    assert len(result.evidence) == 1
    assert result.evidence[0].claim_element_id == "1.2"
    assert result.evidence[0].source_title == (
        "Samsung Galaxy S26 Ultra"
    )
    assert result.reasoning == (
        "The verified evidence directly supports the claim element."
    )

    mock_gemini.return_value.generate.assert_called_once()


def test_claim_mapper_without_verified_evidence():

    element = ClaimElement(
        id="1.3",
        claim_number="1",
        text="a memory controller configured to store processed image data"
    )

    with patch(
        "app.agents.claim_mapper.GeminiService"
    ) as mock_gemini:

        mapper = ClaimMapper()

        result = mapper.map(
            element,
            []
        )

    assert result.claim_element_id == "1.3"
    assert result.supported is False
    assert result.confidence == 0.0
    assert result.evidence == []
    assert result.reasoning == (
        "No verified evidence supports this claim element."
    )

    mock_gemini.return_value.generate.assert_not_called()
