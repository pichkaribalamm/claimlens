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
        """

        if not element_mappings:
            return ClaimAnalysisResult(
                claim_number=claim.claim_number,
                coverage_status="NOT_SUPPORTED",
                confidence=0.0,
                element_mappings=[],
                reasoning="No claim-element mappings were provided.",
            )

        supported_count = sum(
            1
            for mapping in element_mappings
            if mapping.supported
        )

        total_count = len(element_mappings)

        if supported_count == 0:
            coverage_status = "NOT_SUPPORTED"
            confidence = 0.0
            reasoning = (
                "None of the claim elements are supported by "
                "the available technical evidence."
            )

        elif supported_count == total_count:
            coverage_status = "FULLY_SUPPORTED"
            confidence = min(
                mapping.confidence
                for mapping in element_mappings
            )
            reasoning = (
                "All claim elements are supported by the "
                "available technical evidence."
            )

        else:
            coverage_status = "PARTIALLY_SUPPORTED"
            confidence = supported_count / total_count
            reasoning = (
                f"{supported_count} of {total_count} claim elements "
                "are supported by the available technical evidence."
            )

        return ClaimAnalysisResult(
            claim_number=claim.claim_number,
            coverage_status=coverage_status,
            confidence=confidence,
            element_mappings=element_mappings,
            reasoning=reasoning,
        )
