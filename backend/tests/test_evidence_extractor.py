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

    extractor = EvidenceExtractor()

    result = extractor.extract(
        element,
        search_result
    )

    assert result == []
