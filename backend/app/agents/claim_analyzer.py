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
        Aggregate claim-element mappings into a deterministic
        claim-level technical evidence coverage result.

        The analyzer does NOT reinterpret the underlying evidence.

        Element-level technical reasoning has already been performed
        by ClaimMapper. This layer only aggregates those results into
        an overall claim-level assessment.
        """

        if not element_mappings:

            return ClaimAnalysisResult(
                claim_number=claim.claim_number,
                coverage_status="NOT_SUPPORTED",
                confidence=0.0,
                element_mappings=[],
                reasoning=(
                    "No claim-element mappings were provided."
                ),
            )

        total_count = len(element_mappings)

        supported_mappings = [
            mapping
            for mapping in element_mappings
            if mapping.supported
        ]

        unsupported_mappings = [
            mapping
            for mapping in element_mappings
            if not mapping.supported
        ]

        supported_count = len(
            supported_mappings
        )

        # --------------------------------------------------------
        # FULL COVERAGE
        # --------------------------------------------------------

        if supported_count == total_count:

            coverage_status = "FULLY_SUPPORTED"

            confidence = min(
                mapping.confidence
                for mapping in element_mappings
            )

            reasoning = (
                f"All {total_count} claim elements are "
                "supported by the available technical evidence. "
                f"The overall claim-level confidence is governed "
                f"by the weakest supported element "
                f"({confidence:.2f})."
            )

        # --------------------------------------------------------
        # NO COVERAGE
        # --------------------------------------------------------

        elif supported_count == 0:

            coverage_status = "NOT_SUPPORTED"

            confidence = 0.0

            reasoning = (
                f"None of the {total_count} claim elements are "
                "supported by the available technical evidence."
            )

        # --------------------------------------------------------
        # PARTIAL COVERAGE
        # --------------------------------------------------------

        else:

            coverage_status = "PARTIALLY_SUPPORTED"

            # Claim-level confidence should reflect both:
            #
            # 1. How much of the claim is covered.
            # 2. How strong the covered elements are.
            #
            # We therefore calculate:
            #
            # coverage ratio × average confidence of supported
            # elements.
            #
            # This is deliberately deterministic.
            coverage_ratio = (
                supported_count / total_count
            )

            average_supported_confidence = (
                sum(
                    mapping.confidence
                    for mapping in supported_mappings
                )
                / supported_count
            )

            confidence = (
                coverage_ratio
                * average_supported_confidence
            )

            supported_ids = [
                mapping.claim_element_id
                for mapping in supported_mappings
            ]

            unsupported_ids = [
                mapping.claim_element_id
                for mapping in unsupported_mappings
            ]

            reasoning = (
                f"{supported_count} of {total_count} claim "
                "elements are supported by the available "
                "technical evidence. "
                f"Supported elements: "
                f"{', '.join(supported_ids)}. "
                f"Unsupported elements: "
                f"{', '.join(unsupported_ids)}."
            )

        return ClaimAnalysisResult(
            claim_number=claim.claim_number,
            coverage_status=coverage_status,
            confidence=confidence,
            element_mappings=element_mappings,
            reasoning=reasoning,
        )
