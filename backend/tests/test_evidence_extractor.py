from unittest.mock import patch

from app.agents.evidence_extractor import EvidenceExtractor
from app.models.schemas import ClaimElement, SearchResult


def test_evidence_extractor():

    element = ClaimElement(
        id="1.2",
        claim_number="1",
        text="a processor configured to receive image data"
    )

    search_result = SearchResult(
        title="Samsung Galaxy S26 Ultra",
        url="https://www.samsung.com/in/smartphones/galaxy-s26-ultra/",
        snippet="The Galaxy S26 Ultra uses a customized processor.",
        source="Samsung"
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
