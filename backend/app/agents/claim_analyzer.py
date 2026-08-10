from app.models.schemas import (
    Claim,
    ClaimElementMapping,
    ClaimAnalysisResult,
)


class ClaimAnalyzer:

    def analyze(
        self,
        claim: Claim,
        element_mappings: list[ClaimElementMapping],
    ) -> ClaimAnalysisResult:
        """
        Aggregate claim-element mappings into a claim-level
        technical evidence coverage result.

        AI-powered claim analysis will be added later.
        """

        return ClaimAnalysisResult(
            claim_number=claim.claim_number,
            coverage_status="NOT_SUPPORTED",
            confidence=0.0,
            element_mappings=[],
            reasoning="Claim analysis not yet implemented.",
        )
