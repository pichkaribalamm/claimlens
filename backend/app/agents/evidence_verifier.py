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
supports the technical limitations of the claim element.

The verification standard is TECHNICAL DISCLOSURE, not literal
textual matching.

CLAIM ELEMENT:

ID:
{claim_element.id}

TEXT:
{claim_element.text}

EVIDENCE EXCERPT:

{evidence.excerpt}


VERIFICATION METHOD:

First, mentally decompose the claim element into its meaningful
technical limitations, components, operations, conditions, and
relationships.

Then determine whether the evidence excerpt discloses those
technical limitations and relationships.

Evaluate the TECHNICAL MEANING of the evidence rather than requiring
the evidence to use the same words as the claim.


IMPORTANT RULES:

1. Evaluate only the claim element and the provided evidence excerpt.

2. Do not use outside knowledge to add technical facts that are
   absent from the evidence.

3. Do not require literal word-for-word correspondence between the
   claim and the evidence.

4. Different terminology is acceptable when it clearly describes
   the same technical component, operation, condition, or
   relationship.

5. Different sentence structure is acceptable when the same
   technical meaning is disclosed.

6. Patent-style language in the claim may correspond to ordinary
   technical language in the evidence.

7. A technically knowledgeable reader may reasonably interpret
   terminology that is actually present in the evidence.

8. Do not invent or assume a component, operation, capability,
   condition, or relationship that is not reasonably supported by
   the evidence.

9. Distinguish between:
   a. a source actually disclosing the claimed technical limitation,
   and
   b. a source merely mentioning a related technology, component,
      product, or general concept.

10. The evidence does NOT need to reproduce every claim phrase if
    the claimed technical substance and relationships are clearly
    disclosed.

11. An evidence excerpt can support a claim element even when the
    evidence uses substantially different terminology, provided that
    the technical concept is clearly equivalent.

12. Do not reject evidence merely because the claim uses more
    specific, formal, or patent-oriented terminology.

13. However, do not treat a merely related concept as equivalent to
    the claimed limitation.

14. If an important technical limitation or relationship is genuinely
    absent from the evidence, mark the evidence unsupported.

15. If the evidence establishes most of the concept but an important
    limitation is missing, mark it unsupported rather than filling
    the gap using outside knowledge.

16. Do not combine facts from outside the provided excerpt.

17. Do not assume that two components interact merely because they
    are both mentioned in the same excerpt. The required technical
    relationship must be reasonably supported by the excerpt.

18. Do not require unnecessary implementation detail that is not
    actually part of the claim element.

19. The question is:

       "Does this evidence disclose the claimed technical substance?"

    NOT:

       "Does this evidence literally repeat the claim?"


SUPPORT DECISION:

Mark evidence_supported = TRUE when:

- the claimed limitation is explicitly disclosed; OR
- the claimed limitation is disclosed using technically equivalent
  terminology; OR
- the claimed technical relationship is clearly expressed using
  different wording or sentence structure; OR
- only ordinary interpretation of terminology actually present in
  the evidence is needed to understand the claimed limitation.

Mark evidence_supported = FALSE when:

- the evidence only discusses a related technology;
- the evidence only mentions one component without the claimed
  operation or relationship;
- an important claim limitation is absent;
- the claimed relationship between components is not established;
- the evidence is too vague to establish the limitation;
- supporting the claim would require an unstated technical fact;
- or the evidence actually describes a materially different
  operation or architecture.


CONFIDENCE:

Use confidence to reflect the strength of the technical disclosure.

0.90 - 1.00:
Explicit and unambiguous disclosure of the claimed technical
limitation and relationship.

0.80 - 0.89:
Strong technical disclosure using different terminology or
sentence structure, but the technical equivalence is clear.

0.70 - 0.79:
Good technical disclosure where a reasonable technical
interpretation is required, but the claimed substance remains clear.

0.60 - 0.69:
Borderline technical disclosure with meaningful ambiguity.
Normally mark unsupported unless the limitation is still reasonably
clear.

Below 0.60:
Insufficient evidence. Mark unsupported.


REASONING:

The reasoning must explain:

1. Which technical limitation(s) are disclosed.
2. What wording or concept in the evidence establishes them.
3. Whether the evidence uses equivalent terminology or structure.
4. If unsupported, identify the specific missing limitation or
   relationship.

Do not claim that something is disclosed if it is not present in
the evidence.

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
the technical limitations of the claim element.

The verification standard is TECHNICAL DISCLOSURE, not literal
textual matching.

Each evidence excerpt must be evaluated independently.


CLAIM ELEMENT:

ID:
{claim_element.id}

TEXT:
{claim_element.text}


EVIDENCE EXCERPTS:

{evidence_text}


VERIFICATION METHOD:

First, mentally decompose the claim element into its meaningful
technical limitations, components, operations, conditions, and
relationships.

Then evaluate each evidence excerpt independently and determine
whether it discloses those technical limitations and relationships.

Evaluate the TECHNICAL MEANING of each excerpt rather than requiring
the same words used by the claim.


IMPORTANT RULES:

1. Evaluate every evidence excerpt independently.

2. Do not combine multiple evidence excerpts when deciding whether
   an individual evidence item supports the claim element.

3. Do not use outside knowledge to add technical facts that are
   absent from the individual evidence excerpt.

4. Do not require literal word-for-word correspondence between the
   claim and evidence.

5. Different terminology is acceptable when it clearly describes
   the same technical component, operation, condition, or
   relationship.

6. Different sentence structure is acceptable when it clearly
   describes the same technical meaning.

7. Patent-style terminology in the claim may correspond to ordinary
   technical terminology in the evidence.

8. A technically knowledgeable reader may reasonably interpret
   terminology that is actually present in the evidence.

9. Do not invent or assume a component, operation, capability,
   condition, or relationship that is not reasonably supported by
   the evidence.

10. Distinguish between:
    a. actual disclosure of the claimed technical limitation; and
    b. mere mention of a related technology, component, product,
       feature, or general concept.

11. The evidence does NOT need to reproduce every phrase of the
    claim if the claimed technical substance and relationships are
    clearly disclosed.

12. Different terminology may still constitute strong evidence when
    the technical meaning is clearly equivalent.

13. Do not reject evidence merely because the claim uses more formal,
    specific, or patent-oriented language.

14. Do not treat merely related concepts as equivalent to the claimed
    limitation.

15. If an important technical limitation or relationship is genuinely
    absent, mark the evidence unsupported.

16. If supporting the claim would require adding an unstated technical
    fact, mark the evidence unsupported.

17. Do not assume that two components interact merely because they
    appear in the same excerpt. The required technical relationship
    must be reasonably supported.

18. Do not require unnecessary implementation detail that is not part
    of the claim element.

19. The question is:

        "Does this evidence disclose the claimed technical substance?"

    NOT:

        "Does this evidence literally repeat the claim?"


SUPPORT DECISION:

Mark evidence_supported = TRUE when:

- the limitation is explicitly disclosed; OR
- equivalent terminology clearly describes the same limitation; OR
- different wording clearly expresses the same technical
  relationship; OR
- only ordinary interpretation of terminology actually present in
  the evidence is required.

Mark evidence_supported = FALSE when:

- the evidence only discusses related technology;
- only one component of the claimed relationship is mentioned;
- an important limitation is absent;
- the claimed technical relationship is not established;
- the evidence is too vague;
- the conclusion requires an unstated technical fact;
- or the evidence describes a materially different operation.


CONFIDENCE:

0.90 - 1.00:
Explicit and unambiguous technical disclosure.

0.80 - 0.89:
Strong technical disclosure using different terminology or
structure, with clear technical equivalence.

0.70 - 0.79:
Good technical disclosure requiring some reasonable technical
interpretation.

0.60 - 0.69:
Borderline or ambiguous disclosure. Normally unsupported unless
the claimed limitation remains reasonably clear.

Below 0.60:
Insufficient evidence. Mark unsupported.


REASONING:

For every evidence item, explain:

1. Which technical limitation(s) are disclosed.
2. What part of the excerpt establishes them.
3. Whether equivalent terminology or wording is being used.
4. If unsupported, identify the specific missing limitation or
   relationship.

Do not claim that something is disclosed if it is not present.


OUTPUT REQUIREMENTS:

1. Return exactly one verification result for every evidence index.

2. Preserve every evidence index exactly as provided.

3. Do not skip any evidence index.

4. Do not duplicate any evidence index.

5. Evaluate each evidence item independently.

6. Return only the requested structured output.
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

        actual_index_set = set(
            actual_indexes
        )

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
            for index in range(
                len(evidence_list)
            )
        ]
