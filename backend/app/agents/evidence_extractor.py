from app.models.schemas import ClaimElement, SearchResult, Evidence


class EvidenceExtractor:

    def extract(
        self,
        claim_element: ClaimElement,
        search_result: SearchResult,
        page_content: str,
    ) -> list[Evidence]:
        """
        Extract evidence from page content for a claim element.

        AI-powered evidence extraction will be added in the next step.
        """

        return []
