from unittest.mock import patch

import pytest

from app.agents.evidence_verifier import EvidenceVerifier
from app.models.schemas import ClaimElement, Evidence


def test_evidence_verifier():

    element = ClaimElement(
        id="1.2",
        claim_number="1",
        text=(
            "an AI image signal processor (ISP) "
            "associated with the front camera"
        ),
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
        ),
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
            evidence,
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


def test_evidence_verifier_batch_without_evidence():

    element = ClaimElement(
        id="1.3",
        claim_number="1",
        text=(
            "a memory controller configured to store "
            "processed image data"
        ),
    )

    with patch(
        "app.agents.evidence_verifier.GeminiService"
    ) as mock_gemini:

        verifier = EvidenceVerifier()

        result = verifier.verify_batch(
            element,
            [],
        )

    assert result == []

    mock_gemini.return_value.generate.assert_not_called()


def test_evidence_verifier_batch_multiple_evidence():

    element = ClaimElement(
        id="1.2",
        claim_number="1",
        text=(
            "an AI image signal processor (ISP) "
            "associated with the front camera"
        ),
    )

    evidence_one = Evidence(
        claim_element_id="1.2",
        source_title="Samsung Galaxy S26 Ultra",
        url="https://www.samsung.com/in/smartphones/galaxy-s26-ultra/",
        excerpt=(
            "The front camera features an AI image signal "
            "processor (ISP)."
        ),
        evidence_type="direct",
        relevance=(
            "The excerpt directly identifies an ISP associated "
            "with the front camera."
        ),
    )

    evidence_two = Evidence(
        claim_element_id="1.2",
        source_title="Samsung Technical Documentation",
        url="https://example.com/samsung-documentation",
        excerpt=(
            "The image processing subsystem receives image "
            "data from the camera."
        ),
        evidence_type="direct",
        relevance=(
            "The excerpt describes image data being received "
            "by the image processing subsystem."
        ),
    )

    fake_gemini_response = """
    {
        "results": [
            {
                "evidence_index": 0,
                "evidence_supported": true,
                "confidence": 0.98,
                "reasoning": "The excerpt explicitly identifies an AI image signal processor associated with the front camera."
            },
            {
                "evidence_index": 1,
                "evidence_supported": true,
                "confidence": 0.91,
                "reasoning": "The excerpt explicitly states that the image processing subsystem receives image data from the camera."
            }
        ]
    }
    """

    with patch(
        "app.agents.evidence_verifier.GeminiService"
    ) as mock_gemini:

        mock_gemini.return_value.generate.return_value = (
            fake_gemini_response
        )

        verifier = EvidenceVerifier()

        results = verifier.verify_batch(
            element,
            [
                evidence_one,
                evidence_two,
            ],
        )

    assert len(results) == 2

    assert results[0].claim_element_id == "1.2"
    assert results[0].evidence_supported is True
    assert results[0].confidence == 0.98
    assert results[0].reasoning == (
        "The excerpt explicitly identifies an AI image signal "
        "processor associated with the front camera."
    )

    assert results[1].claim_element_id == "1.2"
    assert results[1].evidence_supported is True
    assert results[1].confidence == 0.91
    assert results[1].reasoning == (
        "The excerpt explicitly states that the image processing "
        "subsystem receives image data from the camera."
    )

    mock_gemini.return_value.generate.assert_called_once()


def test_evidence_verifier_batch_unsupported_evidence():

    element = ClaimElement(
        id="1.2",
        claim_number="1",
        text=(
            "a processor configured to receive image data"
        ),
    )

    evidence_one = Evidence(
        claim_element_id="1.2",
        source_title="Samsung Galaxy S26 Ultra",
        url="https://www.samsung.com/in/smartphones/galaxy-s26-ultra/",
        excerpt=(
            "The device features an AI image signal processor."
        ),
        evidence_type="direct",
        relevance=(
            "The excerpt identifies an image signal processor "
            "but does not establish that it receives image data."
        ),
    )

    evidence_two = Evidence(
        claim_element_id="1.2",
        source_title="Samsung Technical Documentation",
        url="https://example.com/samsung-documentation",
        excerpt=(
            "The processor receives image data from the camera."
        ),
        evidence_type="direct",
        relevance=(
            "The excerpt explicitly states that the processor "
            "receives image data."
        ),
    )

    fake_gemini_response = """
    {
        "results": [
            {
                "evidence_index": 0,
                "evidence_supported": false,
                "confidence": 0.90,
                "reasoning": "The excerpt identifies an image signal processor but does not explicitly establish that it receives image data."
            },
            {
                "evidence_index": 1,
                "evidence_supported": true,
                "confidence": 0.97,
                "reasoning": "The excerpt explicitly states that the processor receives image data from the camera."
            }
        ]
    }
    """

    with patch(
        "app.agents.evidence_verifier.GeminiService"
    ) as mock_gemini:

        mock_gemini.return_value.generate.return_value = (
            fake_gemini_response
        )

        verifier = EvidenceVerifier()

        results = verifier.verify_batch(
            element,
            [
                evidence_one,
                evidence_two,
            ],
        )

    assert len(results) == 2

    assert results[0].evidence_supported is False
    assert results[0].confidence == 0.90

    assert results[1].evidence_supported is True
    assert results[1].confidence == 0.97

    mock_gemini.return_value.generate.assert_called_once()


def test_evidence_verifier_batch_invalid_indexes():

    element = ClaimElement(
        id="1.2",
        claim_number="1",
        text=(
            "a processor configured to receive image data"
        ),
    )

    evidence_one = Evidence(
        claim_element_id="1.2",
        source_title="Source One",
        url="https://example.com/source-one",
        excerpt=(
            "The processor receives image data."
        ),
        evidence_type="direct",
        relevance=(
            "The excerpt directly supports the claim element."
        ),
    )

    evidence_two = Evidence(
        claim_element_id="1.2",
        source_title="Source Two",
        url="https://example.com/source-two",
        excerpt=(
            "The processor receives camera data."
        ),
        evidence_type="direct",
        relevance=(
            "The excerpt describes data being received by "
            "the processor."
        ),
    )

    fake_gemini_response = """
    {
        "results": [
            {
                "evidence_index": 0,
                "evidence_supported": true,
                "confidence": 0.95,
                "reasoning": "The excerpt explicitly states that the processor receives image data."
            },
            {
                "evidence_index": 2,
                "evidence_supported": true,
                "confidence": 0.80,
                "reasoning": "The excerpt describes data being received."
            }
        ]
    }
    """

    with patch(
        "app.agents.evidence_verifier.GeminiService"
    ) as mock_gemini:

        mock_gemini.return_value.generate.return_value = (
            fake_gemini_response
        )

        verifier = EvidenceVerifier()

        with pytest.raises(
            ValueError,
            match="invalid evidence indexes",
        ):
            verifier.verify_batch(
                element,
                [
                    evidence_one,
                    evidence_two,
                ],
            )

    mock_gemini.return_value.generate.assert_called_once()
