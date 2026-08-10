from app.models.schemas import (
    ClaimElement,
    Evidence,
    EvidenceVerificationResult,
)


class EvidenceVerifier:

    def verify(
        self,
        claim_element: ClaimElement,
        evidence: Evidence,
    ) -> EvidenceVerificationResult:
        """
        Verify whether an evidence excerpt actually supports
        the claim element.

        AI-powered verification will be added in the next step.
        """

        return EvidenceVerificationResult(
            claim_element_id=claim_element.id,
            evidence_supported=False,
            confidence=0.0,
            reasoning="Verification not yet implemented."
        )
