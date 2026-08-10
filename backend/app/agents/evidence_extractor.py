from app.models.schemas import ClaimElement, SearchResult, Evidence


class EvidenceExtractor:

    def extract(
        self,
        claim_element: ClaimElement,
        search_result: SearchResult,
    ) -> list[Evidence]:
        """
        Extract evidence from a search result for a claim element.

        AI-powered evidence extraction will be added in the next step.
        """

        return []
