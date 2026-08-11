from unittest.mock import patch

import pytest

from app.agents.evidence_extractor import EvidenceExtractor
from app.models.schemas import ClaimElement, SearchResult


def test_evidence_extractor():

    element = ClaimElement(
        id="1.2",
        claim_number="1",
        text="a processor configured to receive image data",
    )

    search_result = SearchResult(
        title="Samsung Galaxy S26 Ultra",
        url="https://www.samsung.com/in/smartphones/galaxy-s26-ultra/",
        snippet="The Galaxy S26 Ultra uses a customized processor.",
        source="Samsung",
    )

    page_content = (
        "The Galaxy S26 Ultra uses a customized processor. "
        "The processor receives image data from the camera system "
        "for image processing."
    )

    fake_gemini_response = """
    {
        "evidence": [
            {
                "claim_element_id": "1.2",
                "source_title": "Samsung Galaxy S26 Ultra",
                "url": "https://www.samsung.com/in/smartphones/galaxy-s26-ultra/",
                "excerpt": "The processor receives image data from the camera system for image processing.",
                "evidence_type": "official product documentation",
                "relevance": "Directly describes the processor receiving image data."
            }
        ]
    }
    """

    with patch(
        "app.agents.evidence_extractor.GeminiService"
    ) as mock_gemini:

        mock_gemini.return_value.generate.return_value = (
            fake_gemini_response
        )

        extractor = EvidenceExtractor()

        result = extractor.extract(
            element,
            search_result,
            page_content,
        )

    assert len(result) == 1

    assert result[0].claim_element_id == "1.2"

    assert result[0].source_title == (
        "Samsung Galaxy S26 Ultra"
    )

    assert str(result[0].url) == (
        "https://www.samsung.com/in/smartphones/galaxy-s26-ultra/"
    )

    assert result[0].excerpt == (
        "The processor receives image data from the camera system "
        "for image processing."
    )

    assert result[0].evidence_type == (
        "official product documentation"
    )

    assert result[0].relevance == (
        "Directly describes the processor receiving image data."
    )

    mock_gemini.return_value.generate.assert_called_once()


def test_evidence_extractor_batch_without_sources():

    element = ClaimElement(
        id="1.2",
        claim_number="1",
        text="a processor configured to receive image data",
    )

    with patch(
        "app.agents.evidence_extractor.GeminiService"
    ) as mock_gemini:

        extractor = EvidenceExtractor()

        result = extractor.extract_batch(
            element,
            [],
        )

    assert result == []

    mock_gemini.return_value.generate.assert_not_called()


def test_evidence_extractor_batch_multiple_sources():

    element = ClaimElement(
        id="1.2",
        claim_number="1",
        text="a processor configured to receive image data",
    )

    search_result_one = SearchResult(
        title="Samsung Galaxy S26 Ultra",
        url="https://www.samsung.com/in/smartphones/galaxy-s26-ultra/",
        snippet="Processor and image processing details.",
        source="Samsung",
    )

    search_result_two = SearchResult(
        title="Samsung Galaxy S26 Ultra Technical Review",
        url="https://example.com/s26-ultra-review",
        snippet="Camera and processor architecture.",
        source="Technical Review",
    )

    reduced_content_one = (
        "The processor receives image data from the camera system."
    )

    reduced_content_two = (
        "The image processing subsystem receives data from the "
        "camera interface."
    )

    fake_gemini_response = """
    {
        "results": [
            {
                "source_index": 0,
                "evidence": [
                    {
                        "claim_element_id": "1.2",
                        "source_title": "Samsung Galaxy S26 Ultra",
                        "url": "https://www.samsung.com/in/smartphones/galaxy-s26-ultra/",
                        "excerpt": "The processor receives image data from the camera system.",
                        "evidence_type": "official product documentation",
                        "relevance": "Directly describes the processor receiving image data."
                    }
                ]
            },
            {
                "source_index": 1,
                "evidence": [
                    {
                        "claim_element_id": "1.2",
                        "source_title": "Samsung Galaxy S26 Ultra Technical Review",
                        "url": "https://example.com/s26-ultra-review",
                        "excerpt": "The image processing subsystem receives data from the camera interface.",
                        "evidence_type": "technical review",
                        "relevance": "Describes image data entering the image processing subsystem."
                    },
                    {
                        "claim_element_id": "1.2",
                        "source_title": "Samsung Galaxy S26 Ultra Technical Review",
                        "url": "https://example.com/s26-ultra-review",
                        "excerpt": "The processor handles incoming camera image data.",
                        "evidence_type": "technical review",
                        "relevance": "Describes the processor handling incoming camera image data."
                    }
                ]
            }
        ]
    }
    """

    with patch(
        "app.agents.evidence_extractor.GeminiService"
    ) as mock_gemini:

        mock_gemini.return_value.generate.return_value = (
            fake_gemini_response
        )

        extractor = EvidenceExtractor()

        result = extractor.extract_batch(
            element,
            [
                (
                    search_result_one,
                    reduced_content_one,
                ),
                (
                    search_result_two,
                    reduced_content_two,
                ),
            ],
        )

    assert len(result) == 2

    assert len(result[0]) == 1
    assert result[0][0].source_title == (
        "Samsung Galaxy S26 Ultra"
    )
    assert result[0][0].claim_element_id == "1.2"

    assert len(result[1]) == 2
    assert result[1][0].source_title == (
        "Samsung Galaxy S26 Ultra Technical Review"
    )
    assert result[1][1].source_title == (
        "Samsung Galaxy S26 Ultra Technical Review"
    )

    mock_gemini.return_value.generate.assert_called_once()


def test_evidence_extractor_batch_with_empty_source():

    element = ClaimElement(
        id="1.2",
        claim_number="1",
        text="a processor configured to receive image data",
    )

    search_result_one = SearchResult(
        title="Samsung Galaxy S26 Ultra",
        url="https://www.samsung.com/in/smartphones/galaxy-s26-ultra/",
        snippet="Processor information.",
        source="Samsung",
    )

    search_result_two = SearchResult(
        title="Empty Source",
        url="https://example.com/empty",
        snippet="",
        source="Unknown",
    )

    reduced_content = (
        "The processor receives image data from the camera."
    )

    fake_gemini_response = """
    {
        "results": [
            {
                "source_index": 0,
                "evidence": [
                    {
                        "claim_element_id": "1.2",
                        "source_title": "Samsung Galaxy S26 Ultra",
                        "url": "https://www.samsung.com/in/smartphones/galaxy-s26-ultra/",
                        "excerpt": "The processor receives image data from the camera.",
                        "evidence_type": "direct",
                        "relevance": "Directly describes the processor receiving image data."
                    }
                ]
            }
        ]
    }
    """

    with patch(
        "app.agents.evidence_extractor.GeminiService"
    ) as mock_gemini:

        mock_gemini.return_value.generate.return_value = (
            fake_gemini_response
        )

        extractor = EvidenceExtractor()

        result = extractor.extract_batch(
            element,
            [
                (
                    search_result_one,
                    reduced_content,
                ),
                (
                    search_result_two,
                    "",
                ),
            ],
        )

    assert len(result) == 2

    assert len(result[0]) == 1
    assert result[0][0].claim_element_id == "1.2"

    assert result[1] == []

    mock_gemini.return_value.generate.assert_called_once()


def test_evidence_extractor_batch_invalid_indexes():

    element = ClaimElement(
        id="1.2",
        claim_number="1",
        text="a processor configured to receive image data",
    )

    search_result_one = SearchResult(
        title="Source One",
        url="https://example.com/source-one",
        snippet="Processor information.",
        source="Source One",
    )

    search_result_two = SearchResult(
        title="Source Two",
        url="https://example.com/source-two",
        snippet="Processor information.",
        source="Source Two",
    )

    reduced_content_one = (
        "The processor receives image data."
    )

    reduced_content_two = (
        "The processor receives camera data."
    )

    fake_gemini_response = """
    {
        "results": [
            {
                "source_index": 0,
                "evidence": []
            },
            {
                "source_index": 2,
                "evidence": []
            }
        ]
    }
    """

    with patch(
        "app.agents.evidence_extractor.GeminiService"
    ) as mock_gemini:

        mock_gemini.return_value.generate.return_value = (
            fake_gemini_response
        )

        extractor = EvidenceExtractor()

        with pytest.raises(
            ValueError,
            match="invalid source indexes",
        ):
            extractor.extract_batch(
                element,
                [
                    (
                        search_result_one,
                        reduced_content_one,
                    ),
                    (
                        search_result_two,
                        reduced_content_two,
                    ),
                ],
            )

    mock_gemini.return_value.generate.assert_called_once()
