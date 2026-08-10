from app.models.schemas import (
    ClaimElement,
    Evidence,
    ClaimElementMapping,
)


class ClaimMapper:

    def map(
        self,
        claim_element: ClaimElement,
        evidence: list[Evidence],
    ) -> ClaimElementMapping:
        """
        Map verified evidence to a claim element.

        AI-powered claim mapping will be added in the next step.
        """

        return ClaimElementMapping(
            claim_element_id=claim_element.id,
            supported=False,
            confidence=0.0,
            evidence=[],
            reasoning="Claim mapping not yet implemented."
        )
