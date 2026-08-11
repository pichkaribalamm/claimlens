from app.models.schemas import (
    ClaimElement,
    Evidence,
    EvidenceVerificationResult,
    EvidenceVerificationBatchResult,
)
from app.services.gemini_service import GeminiService


class EvidenceVerifier:

    def __init__(self):
        self.llm = GeminiService()

    def verify(
        self,
        claim_element: ClaimElement,
        evidence: Evidence,
    ) -> EvidenceVerificationResult:

        prompt = f"""
You are a patent evidence verification assistant.

Determine whether the evidence excerpt directly supports
the technical limitations of the claim element.

RULES:

1. Evaluate only the claim element and evidence excerpt.
2. Use no outside knowledge.
3. Do not infer facts not explicitly supported by the excerpt.
4. Similar terminology is not sufficient.
5. The excerpt must support the technical substance of the
   claim element.
6. When ambiguous or incomplete, mark unsupported.
7. Return only the requested structured output.

CLAIM ELEMENT:
ID: {claim_element.id}
TEXT: {claim_element.text}

EVIDENCE EXCERPT:
{evidence.excerpt}
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=EvidenceVerificationResult,
        )

        return EvidenceVerificationResult.model_validate_json(
            result
        )

    def verify_batch(
        self,
        claim_element: ClaimElement,
        evidence_list: list[Evidence],
    ) -> list[EvidenceVerificationResult]:

        if not evidence_list:
            return []

        evidence_text = "\n\n".join(
            (
                f"EVIDENCE INDEX: {index}\n"
                f"EXCERPT:\n"
                f"{evidence.excerpt}"
            )
            for index, evidence in enumerate(evidence_list)
        )

        prompt = f"""
You are a patent evidence verification assistant.

Determine whether each evidence excerpt directly supports
the technical limitations of the claim element.

Evaluate each evidence excerpt independently.

RULES:

1. Evaluate only the claim element and the provided evidence excerpts.
2. Use no outside knowledge.
3. Do not infer facts not explicitly supported by an excerpt.
4. Similar terminology is not sufficient.
5. An excerpt must support the technical substance of the
   claim element.
6. When an excerpt is ambiguous or incomplete, mark it unsupported.
7. Return exactly one verification result for every evidence index.
8. Preserve the evidence index exactly as provided.
9. Do not skip any evidence index.
10. Do not combine evidence excerpts when evaluating an individual
    evidence item.
11. Return only the requested structured output.

CLAIM ELEMENT:

ID:
{claim_element.id}

TEXT:
{claim_element.text}

EVIDENCE EXCERPTS:

{evidence_text}
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=EvidenceVerificationBatchResult,
        )

        parsed = EvidenceVerificationBatchResult.model_validate_json(
            result
        )

        expected_indexes = set(
            range(len(evidence_list))
        )

        actual_indexes = [
            item.evidence_index
            for item in parsed.results
        ]

        actual_index_set = set(actual_indexes)

        if actual_index_set != expected_indexes:
            raise ValueError(
                "Evidence verification batch returned "
                "invalid evidence indexes."
            )

        if len(actual_indexes) != len(
            expected_indexes
        ):
            raise ValueError(
                "Evidence verification batch returned "
                "duplicate evidence indexes."
            )

        results_by_index = {
            item.evidence_index: item
            for item in parsed.results
        }

        return [
            EvidenceVerificationResult(
                claim_element_id=claim_element.id,
                evidence_supported=results_by_index[
                    index
                ].evidence_supported,
                confidence=results_by_index[
                    index
                ].confidence,
                reasoning=results_by_index[
                    index
                ].reasoning,
            )
            for index in range(len(evidence_list))
        ]
