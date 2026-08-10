from unittest.mock import patch

from app.agents.evidence_verifier import EvidenceVerifier
from app.models.schemas import ClaimElement, Evidence


def test_evidence_verifier():

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

    fake_gemini_response = """
    {
        "claim_element_id": "1.2",
        "evidence_supported": true,
        "confidence": 0.98,
        "reasoning": "The excerpt explicitly states that the front camera features an AI image signal processor (ISP), directly supporting the claim element."
    }
    """

    with patch(
        "app.agents.evidence_verifier.GeminiService"
    ) as mock_gemini:

        mock_gemini.return_value.generate.return_value = (
            fake_gemini_response
        )

        verifier = EvidenceVerifier()

        result = verifier.verify(
            element,
            evidence
        )

    assert result.claim_element_id == "1.2"
    assert result.evidence_supported is True
    assert result.confidence == 0.98
    assert result.reasoning == (
        "The excerpt explicitly states that the front camera "
        "features an AI image signal processor (ISP), directly "
        "supporting the claim element."
    )

    mock_gemini.return_value.generate.assert_called_once()
