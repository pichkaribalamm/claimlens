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

Your task is to assess how strongly the provided evidence
supports the technical substance of the claim element.

You are evaluating the EVIDENCE itself.

You are NOT yet deciding whether the entire claim element
is established by the overall body of evidence.

The overall claim-element assessment may later combine
multiple evidence items.

CLAIM ELEMENT:

ID:
{claim_element.id}

TEXT:
{claim_element.text}

EVIDENCE:

SOURCE:
{evidence.source_title}

EXCERPT:
{evidence.excerpt}


VERIFICATION METHOD:

First, mentally decompose the claim element into its meaningful
technical limitations, components, operations, conditions,
and relationships.

Then determine what technical facts are actually established
by the evidence excerpt.

Assess the technical meaning of the evidence rather than
requiring literal textual matching.


SUPPORT LEVELS:

Use exactly one of the following support levels.

1. "direct"

Use DIRECT when the evidence explicitly discloses the claimed
technical limitation or relationship.

The wording does not need to be identical to the claim.

Equivalent technical terminology is acceptable.

Typical confidence:
0.90 - 1.00


2. "supportive"

Use SUPPORTIVE when the evidence strongly corresponds to the
claimed technical limitation or describes a technically
equivalent implementation, but does not state the limitation
in exactly the same form.

The technical correspondence should be clear to a technically
knowledgeable reader.

Typical confidence:
0.80 - 0.89


3. "inferential"

Use INFERENTIAL when the evidence provides concrete technical
facts from which the claimed limitation or relationship can
reasonably be inferred.

This category is IMPORTANT.

Do NOT reject evidence merely because the claimed relationship
is not stated word-for-word.

Reasonable technical inference is allowed when the inference
follows naturally from the facts actually disclosed in the
evidence.

However, the inference must remain grounded in the provided
evidence.

Do not introduce an unstated component, capability, operation,
or relationship merely because it would be technically possible.

Typical confidence:
0.70 - 0.79


4. "contextual"

Use CONTEXTUAL when the evidence is genuinely relevant to the
technical subject matter but provides little or no meaningful
support for the particular claim limitation.

Examples:

- general discussion of the technology;
- description of a related product;
- mention of a relevant component without the claimed function;
- background information.

Contextual evidence may still be useful to the overall
investigation, but should not normally establish an element
by itself.

Typical confidence:
0.40 - 0.69


5. "unsupported"

Use UNSUPPORTED when the evidence does not meaningfully support
the claim limitation.

Examples:

- materially different technology;
- merely coincidental terminology;
- required technical component is absent;
- required operation is absent;
- required relationship is absent;
- conclusion depends on a substantial unstated technical fact.

Typical confidence:
0.00 - 0.39


IMPORTANT DISTINCTION:

Do NOT treat "not explicitly stated" as automatically meaning
"unsupported."

Instead ask:

"Are the technical facts actually disclosed in the evidence
sufficient for a reasonable technical reader to understand the
claimed limitation or relationship?"

If yes, the evidence may be SUPPORTIVE or INFERENTIAL.

Only classify it as UNSUPPORTED when the missing information
creates a genuine technical gap rather than merely a wording
difference.


TECHNICAL EQUIVALENCE:

The following are allowed:

- different terminology describing the same component;
- different terminology describing the same operation;
- different terminology describing the same technical
  relationship;
- ordinary industry terminology corresponding to patent-style
  terminology;
- different sentence structure expressing the same technical
  behavior;
- a reasonable technical interpretation of terminology actually
  present in the evidence.


DO NOT:

1. Require word-for-word matching.
2. Require the claim and evidence to use identical terminology.
3. Reject evidence merely because it uses ordinary technical
   language rather than patent-style language.
4. Reject an inference simply because the source does not use
   the exact claim wording.
5. Use outside knowledge to add substantive technical facts.
6. Assume a component or capability that is completely absent.
7. Assume a technical relationship merely because two components
   appear somewhere in the excerpt.
8. Treat general discussion of the technology as proof of a
   specific limitation.
9. Decide the entire claim element using evidence that establishes
   only one small part of it.


OUTSIDE KNOWLEDGE:

Do not use outside knowledge to manufacture evidence.

However, ordinary technical interpretation of terminology that
is actually present in the excerpt is allowed.

For example, if the evidence explicitly describes a known type
of technical operation using a different but equivalent term,
that terminology may be interpreted according to its ordinary
technical meaning.

Do not introduce additional facts that are not reasonably
grounded in the excerpt.


EVIDENCE SCOPE:

An individual evidence item does NOT need to establish every
limitation of the claim element.

It is acceptable for the evidence to establish one or more
important technical aspects of the element.

The later evidence aggregation stage will determine whether
multiple evidence items collectively establish the complete
claim element.

Therefore:

- Do NOT mark evidence unsupported merely because it does not
  establish the entire claim element.
- Assess the technical value of THIS evidence for THIS claim
  element.
- Identify what portion or aspect of the claim element the
  evidence actually supports.


EVIDENCE_SUPPORTED:

Set evidence_supported = TRUE when the evidence provides
meaningful technical support at the DIRECT, SUPPORTIVE, or
INFERENTIAL level.

Set evidence_supported = FALSE when the evidence is only
CONTEXTUAL or UNSUPPORTED.


CONFIDENCE:

Confidence reflects the strength of the relationship between
the evidence and the claim element.

Use approximately:

0.90 - 1.00:
Explicit and unambiguous disclosure.

0.80 - 0.89:
Strong technical correspondence or equivalent implementation.

0.70 - 0.79:
Reasonable technical inference grounded in disclosed facts.

0.40 - 0.69:
Relevant context with limited element-specific support.

0.00 - 0.39:
Little or no meaningful support.


REASONING:

Explain:

1. What technical fact or facts the evidence establishes.
2. Which part of the claim element those facts relate to.
3. Whether the evidence uses equivalent terminology.
4. Whether reasonable technical inference is required.
5. If unsupported, identify the specific technical gap.

Do NOT claim that the source explicitly states something
that it does not state.

Do NOT say that the entire claim element is proven merely
because this evidence supports one part of it.


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
                f"SOURCE: {evidence.source_title}\n"
                f"EXCERPT:\n{evidence.excerpt}"
            )
            for index, evidence in enumerate(evidence_list)
        )

        prompt = f"""
You are a patent evidence verification assistant.

Your task is to assess how strongly EACH evidence excerpt
supports the technical substance of the claim element.

You are evaluating each evidence item independently.

You are NOT yet deciding whether the entire claim element
is established by the complete evidence set.

Multiple evidence items may later be combined by a separate
element-level evidence aggregation stage.


CLAIM ELEMENT:

ID:
{claim_element.id}

TEXT:
{claim_element.text}


EVIDENCE EXCERPTS:

{evidence_text}


VERIFICATION METHOD:

For each evidence item:

1. Identify the meaningful technical facts actually disclosed.
2. Determine which aspect of the claim element those facts relate to.
3. Assess the technical relationship between the evidence and
   the claim.
4. Determine the appropriate support level.


SUPPORT LEVELS:

Use exactly one of:

"direct"
"supportive"
"inferential"
"contextual"
"unsupported"


DIRECT:

The evidence explicitly discloses the claimed limitation or
technical relationship.

Equivalent terminology is acceptable.

Typical confidence:
0.90 - 1.00


SUPPORTIVE:

The evidence strongly corresponds to the claimed limitation or
describes a technically equivalent implementation.

The technical correspondence is clear even if the claim's exact
language is not used.

Typical confidence:
0.80 - 0.89


INFERENTIAL:

The evidence provides concrete technical facts from which the
claimed limitation or relationship can reasonably be inferred.

Reasonable technical inference IS allowed.

This is especially important when technical documentation
describes the implementation through several related facts
rather than stating the claim limitation verbatim.

The inference must remain grounded in the evidence.

Do not introduce a substantial unstated technical fact.

Typical confidence:
0.70 - 0.79


CONTEXTUAL:

The evidence is relevant to the technical subject matter but
does not provide meaningful element-specific support.

Typical confidence:
0.40 - 0.69


UNSUPPORTED:

The evidence does not meaningfully support the claim limitation.

Typical confidence:
0.00 - 0.39


CRITICAL DISTINCTION:

Do NOT equate:

"not explicitly stated"

with:

"unsupported."

If the disclosed technical facts reasonably establish the
claimed concept through technical interpretation or inference,
use SUPPORTIVE or INFERENTIAL.

Only use UNSUPPORTED when there is a genuine technical gap.


TECHNICAL EQUIVALENCE:

Accept:

- equivalent terminology;
- ordinary technical terminology;
- different sentence structures;
- different ways of describing the same operation;
- different ways of describing the same component;
- different ways of describing the same technical relationship;
- reasonable technical interpretation of terminology actually
  present in the evidence.


EVIDENCE DOES NOT NEED TO ESTABLISH THE ENTIRE ELEMENT:

This is critical.

An individual evidence item may establish only one important
aspect of a claim element.

Do NOT mark an evidence item unsupported merely because another
piece of information would be needed to establish the rest of
the claim element.

The later aggregation stage will combine evidence items.

Assess the value of THIS evidence independently.


OUTSIDE KNOWLEDGE:

Do not use outside knowledge to manufacture missing facts.

However, ordinary technical interpretation of terminology that
is actually present in the evidence is allowed.

Do not assume a component, capability, operation, or relationship
that is completely absent from the evidence.


DO NOT:

1. Require word-for-word matching.
2. Require identical terminology.
3. Reject ordinary technical terminology.
4. Reject reasonable inference merely because the inference is
   not stated verbatim.
5. Treat related technology as equivalent to the claimed
   technology without technical support.
6. Assume relationships merely because components are mentioned.
7. Add substantive facts from outside the excerpt.


EVIDENCE_SUPPORTED:

Set:

evidence_supported = TRUE

for:

- direct
- supportive
- inferential

Set:

evidence_supported = FALSE

for:

- contextual
- unsupported


CONFIDENCE:

Use confidence to reflect the strength of the evidence:

0.90 - 1.00 → direct and unambiguous
0.80 - 0.89 → strong technical correspondence
0.70 - 0.79 → reasonable technical inference
0.40 - 0.69 → contextual / limited support
0.00 - 0.39 → unsupported


REASONING:

For every evidence item explain:

1. What technical fact is disclosed.
2. Which part of the claim element it relates to.
3. Whether equivalent terminology is used.
4. Whether reasonable inference is required.
5. If unsupported, what specific technical gap exists.


OUTPUT REQUIREMENTS:

1. Return exactly one verification result for every evidence index.
2. Preserve every evidence index exactly as provided.
3. Do not skip any evidence index.
4. Do not duplicate any evidence index.
5. Evaluate each evidence item independently.
6. Populate support_level for every result.
7. Set evidence_supported consistently with support_level.
8. Return only the requested structured output.
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
                support_level=results_by_index[
                    index
                ].support_level,
            )
            for index in range(
                len(evidence_list)
            )
        ]
