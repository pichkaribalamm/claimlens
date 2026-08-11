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

Your task is to determine whether the provided evidence excerpt
supports the technical limitation expressed by the claim element.

The goal is TECHNICAL DISCLOSURE, not exact textual matching.

A claim element may be supported even when the evidence uses
different terminology, wording, or sentence structure, provided
that the technical meaning and relationship expressed by the
claim element are clearly disclosed by the evidence.

CLAIM ELEMENT:
ID: {claim_element.id}
TEXT: {claim_element.text}

EVIDENCE EXCERPT:
{evidence.excerpt}

VERIFICATION STANDARD:

Determine whether a technically reasonable reader, relying only
on the provided excerpt, would understand the claimed technical
limitation to be disclosed.

RULES:

1. Evaluate only the claim element and the provided evidence excerpt.

2. Do not use outside knowledge to add facts that are absent from
   the evidence.

3. Do not require the evidence to reproduce the exact wording of
   the claim element.

4. Different terminology is acceptable when the terminology clearly
   refers to the same technical concept.

5. Different sentence structure is acceptable when the same
   technical relationship is disclosed.

6. The evidence may support the claim element through an explicit
   technical description, even if the exact claim language is not
   present.

7. A reasonable technical interpretation of terminology that is
   actually present in the excerpt is allowed.

8. Do NOT assume an unstated component, property, relationship,
   operation, or capability merely because it would be technically
   plausible.

9. Distinguish between:
   - merely mentioning a related technology or concept, and
   - actually disclosing the technical limitation.

10. The important question is whether the technical substance of
    the claim element is disclosed, not whether every word appears
    in the evidence.

11. If the evidence clearly supports the limitation, mark it
    supported.

12. If the evidence provides only partial, vague, contextual, or
    speculative support for the limitation, mark it unsupported.

13. Confidence should reflect the strength and clarity of the
    disclosure:
    - 0.90-1.00: explicit and unambiguous disclosure
    - 0.75-0.89: strong technical disclosure with different wording
    - 0.60-0.74: reasonably clear disclosure but some interpretation
      is required
    - below 0.60: insufficient support; normally unsupported

14. Do not penalize an excerpt merely because it does not repeat
    terminology already present in the claim.

15. Do not mark evidence unsupported merely because the claim uses
    more formal or specific patent language than the evidence.

16. However, if an important technical limitation is genuinely
    absent from the excerpt, mark the evidence unsupported.

Return only the requested structured output.
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

Your task is to determine whether each evidence excerpt supports
the technical limitation expressed by the claim element.

The goal is TECHNICAL DISCLOSURE, not exact textual matching.

Each evidence excerpt must be evaluated independently.

CLAIM ELEMENT:

ID:
{claim_element.id}

TEXT:
{claim_element.text}

EVIDENCE EXCERPTS:

{evidence_text}

VERIFICATION STANDARD:

For each evidence excerpt, determine whether a technically
reasonable reader, relying only on that excerpt, would understand
the technical limitation in the claim element to be disclosed.

RULES:

1. Evaluate each evidence excerpt independently.

2. Do not combine evidence excerpts when determining whether an
   individual evidence item supports the claim element.

3. Do not use outside knowledge to add facts that are absent from
   the individual evidence excerpt.

4. Do not require exact textual matching between the claim element
   and the evidence.

5. Different terminology is acceptable when it clearly describes
   the same technical concept.

6. Different sentence structure is acceptable when it clearly
   describes the same technical relationship.

7. A technically reasonable interpretation of terminology actually
   present in the excerpt is allowed.

8. Do NOT assume an unstated component, property, relationship,
   operation, or capability merely because it would be technically
   plausible.

9. Distinguish between a source merely mentioning a related
   technology and a source actually disclosing the claimed
   technical limitation.

10. Focus on the technical substance and relationships expressed
    by the claim element.

11. Mark SUPPORTED when the excerpt clearly discloses the claimed
    technical limitation, even if the wording differs substantially
    from the claim.

12. Mark UNSUPPORTED when the excerpt only provides:
    - general background,
    - related terminology,
    - a nearby but different concept,
    - vague contextual information,
    - or requires an unstated technical fact to establish the claim
      limitation.

13. Confidence should reflect the strength of the disclosure:

    0.90-1.00:
    Explicit and unambiguous disclosure.

    0.75-0.89:
    Strong technical disclosure using different terminology or
    wording.

    0.60-0.74:
    Reasonably clear disclosure, but some limited interpretation
    is required.

    Below 0.60:
    Insufficient support. Normally mark unsupported.

14. Do not penalize evidence merely because the claim uses more
    formal, specific, or patent-style language.

15. If an important technical limitation is genuinely absent from
    the excerpt, mark the evidence unsupported.

16. The reasoning must explain WHAT part of the evidence supports
    the claim element and WHY the technical relationship is or is
    not disclosed.

17. Return exactly one verification result for every evidence index.

18. Preserve every evidence index exactly as provided.

19. Do not skip any evidence index.

20. Do not duplicate any evidence index.

21. Return only the requested structured output.

IMPORTANT:

Do not raise the verification threshold merely because the claim
language is more specific or formal than the evidence language.

The question is:

"Does this excerpt disclose the claimed technical substance?"

NOT:

"Does this excerpt literally contain every phrase in the claim?"

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

        expected_indexes = set(range(len(evidence_list)))

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

        if len(actual_indexes) != len(expected_indexes):
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
