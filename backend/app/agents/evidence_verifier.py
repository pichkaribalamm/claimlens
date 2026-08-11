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

    # ============================================================
    # SINGLE EVIDENCE VERIFICATION
    # ============================================================

    def verify(
        self,
        claim_element: ClaimElement,
        evidence: Evidence,
    ) -> EvidenceVerificationResult:

        prompt = f"""
You are a patent evidence verification assistant.

Your task is to assess the TECHNICAL VALUE of ONE evidence
excerpt in relation to ONE patent claim element.

You are NOT deciding whether the complete claim element is
established.

You are NOT deciding whether the complete patent claim is
supported.

A later claim-mapping stage will combine multiple evidence
items.

Your job is simply:

"What technical fact or facts does THIS excerpt establish
that are relevant to THIS claim element?"


============================================================
CLAIM ELEMENT
============================================================

ID:
{claim_element.id}

TEXT:
{claim_element.text}


============================================================
EVIDENCE
============================================================

SOURCE:
{evidence.source_title}

EXCERPT:
{evidence.excerpt}


============================================================
EVIDENCE SCOPE
============================================================

An evidence item does NOT need to establish the entire claim
element.

A claim element may contain multiple technical limitations.

For example:

A + B + C + D

If this excerpt establishes:

B + C

then the excerpt contains meaningful technical evidence.

Do NOT mark it unsupported merely because A and D are absent.

The mapper will later determine whether other evidence covers
A and D.


============================================================
WHAT TO EVALUATE
============================================================

Evaluate whether the excerpt establishes one or more meaningful
technical aspects of the claim element, including:

- component;
- structure;
- operation;
- condition;
- input;
- output;
- technical relationship;
- functional behavior;
- implementation detail;
- interaction;
- sequencing.


============================================================
SUPPORT LEVEL
============================================================

Return exactly one of:

"direct"
"supportive"
"inferential"
"contextual"
"unsupported"


DIRECT
------

Use "direct" when the excerpt explicitly describes the relevant
technical limitation, operation, component, condition, or
relationship.

Exact claim wording is NOT required.

Equivalent technical terminology is acceptable.


SUPPORTIVE
----------

Use "supportive" when the excerpt strongly corresponds to the
claimed technical concept or describes a technically equivalent
implementation.

The technical correspondence should be clear to a technically
knowledgeable reader.


INFERENTIAL
-----------

Use "inferential" when the excerpt provides concrete technical
facts from which a relevant claimed concept can reasonably be
inferred.

Reasonable technical inference is explicitly allowed.

The inference must be grounded in information actually present
in the excerpt.


CONTEXTUAL
----------

Use "contextual" when the excerpt is genuinely relevant to the
technology, product, or architecture but contributes little
specific technical support to the claim element.

Examples:

- general technology background;
- general product description;
- generic capability;
- mention of a component without the relevant function.


UNSUPPORTED
-----------

Use "unsupported" only when the excerpt provides no meaningful
technical support for the claim element.

Examples:

- materially unrelated technology;
- coincidental terminology;
- technically different component;
- technically different operation;
- contradictory technical disclosure;
- conclusion requires a substantial unstated fact.


============================================================
TECHNICAL TERMINOLOGY
============================================================

Do NOT require word-for-word matching.

Do NOT require patent-style language.

Accept reasonable differences in:

- component names;
- operation names;
- industry terminology;
- implementation terminology;
- sentence structure;
- descriptions of technical behavior.

Evaluate the underlying technical substance.

Different terminology alone is NOT a reason to mark evidence
unsupported.


============================================================
REASONABLE TECHNICAL INFERENCE
============================================================

Reasonable inference is allowed.

Do not require every consequence of a disclosed technical
operation to be explicitly written in the source.

For example, if the excerpt describes a technical operation
whose ordinary implementation necessarily or reasonably
corresponds to part of the claim element, that may be
inferential support.

However:

Do NOT invent a missing component.

Do NOT invent a missing operation.

Do NOT invent a missing capability.

Do NOT invent a missing relationship.

Do NOT use outside facts to bridge a substantial technical gap.


============================================================
OUTSIDE KNOWLEDGE
============================================================

Use only the evidence excerpt as factual evidence.

Ordinary technical interpretation of terminology actually
present in the excerpt is allowed.

Do not import target-specific facts or implementation details
that are absent from the excerpt.


============================================================
IMPORTANT DISTINCTION
============================================================

The following are NOT automatically unsupported:

- different terminology;
- different sentence structure;
- implementation-oriented wording;
- absence of other claim limitations;
- a reasonable technical inference.

The following ARE reasons for unsupported:

- materially different technical functionality;
- unrelated subject matter;
- merely coincidental terminology;
- a missing technical fact that cannot reasonably be inferred;
- a claimed relationship that the excerpt does not reasonably
  establish.


============================================================
EVIDENCE SUPPORTED
============================================================

Set:

evidence_supported = true

when the evidence has meaningful technical value:

- direct;
- supportive;
- inferential.

Set:

evidence_supported = false

when the evidence is:

- contextual;
- unsupported.

IMPORTANT:

evidence_supported means:

"This evidence is useful to the later mapping stage."

It does NOT mean:

"The complete claim element has been proven."


============================================================
CONFIDENCE
============================================================

Confidence reflects the strength of THIS evidence item.

It does NOT represent confidence that the complete claim
element is supported.

Use approximately:

0.90 - 1.00
Clear and explicit technical disclosure.

0.80 - 0.89
Strong technical correspondence or equivalent implementation.

0.70 - 0.79
Reasonable technical inference grounded in disclosed facts.

0.40 - 0.69
Relevant but limited technical contribution.

0.00 - 0.39
Little or no meaningful support.


Do NOT reduce confidence merely because other claim limitations
are absent from this excerpt.

Do NOT increase confidence merely because the excerpt contains
many related words.


============================================================
REASONING
============================================================

Explain:

1. What technical fact or facts the excerpt establishes.

2. Which part of the claim element those facts relate to.

3. Whether the source uses equivalent terminology.

4. Whether reasonable technical inference is required.

5. If the evidence is contextual or unsupported, identify why.

The reasoning must describe the contribution of THIS evidence
item.

Do NOT state that the complete claim element is proven.


============================================================
OUTPUT
============================================================

Return only the requested structured output.
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=EvidenceVerificationResult,
        )

        parsed = (
            EvidenceVerificationResult
            .model_validate_json(result)
        )

        # ========================================================
        # OUTPUT VALIDATION
        # ========================================================

        if (
            parsed.claim_element_id
            != claim_element.id
        ):
            raise ValueError(
                "Evidence verification returned an invalid "
                "claim element ID."
            )

        expected_supported = (
            parsed.support_level
            in {
                "direct",
                "supportive",
                "inferential",
            }
        )

        if (
            parsed.evidence_supported
            != expected_supported
        ):
            raise ValueError(
                "Evidence verification returned an "
                "inconsistent evidence_supported value."
            )

        return parsed

    # ============================================================
    # BATCH EVIDENCE VERIFICATION
    # ============================================================

    def verify_batch(
        self,
        claim_element: ClaimElement,
        evidence_list: list[Evidence],
    ) -> list[EvidenceVerificationResult]:

        if not evidence_list:
            return []

        evidence_sections = []

        for index, evidence in enumerate(
            evidence_list
        ):

            evidence_sections.append(
                f"""
EVIDENCE INDEX: {index}

SOURCE:
{evidence.source_title}

EXCERPT:
{evidence.excerpt}
""".strip()
            )

        evidence_text = "\n\n".join(
            evidence_sections
        )

        prompt = f"""
You are a patent evidence verification assistant.

Your task is to assess the TECHNICAL VALUE of EACH evidence
excerpt in relation to ONE patent claim element.

Evaluate every evidence item independently.

You are NOT deciding whether the complete claim element is
established.

You are NOT deciding whether the complete patent claim is
supported.

A later claim-mapping stage will combine the individual
evidence assessments.


============================================================
CLAIM ELEMENT
============================================================

ID:
{claim_element.id}

TEXT:
{claim_element.text}


============================================================
EVIDENCE EXCERPTS
============================================================

{evidence_text}


============================================================
PRIMARY QUESTION
============================================================

For EACH evidence item ask:

"What technical fact or facts does this excerpt establish
that are relevant to this claim element?"


============================================================
PARTIAL EVIDENCE IS VALID
============================================================

An evidence item does NOT need to establish the entire claim
element.

For example:

Claim element:

A + B + C + D

Evidence 0:

B + C

Evidence 0 is still meaningful evidence.

Do NOT mark Evidence 0 unsupported merely because A and D
are absent.

Evaluate what Evidence 0 actually establishes.

The mapper will later determine whether other evidence
establishes A and D.


============================================================
SUPPORT LEVEL
============================================================

For EACH evidence item return exactly one:

"direct"
"supportive"
"inferential"
"contextual"
"unsupported"


DIRECT
------

The excerpt explicitly discloses the relevant technical
limitation, component, operation, condition, or relationship.

Equivalent terminology is acceptable.


SUPPORTIVE
----------

The excerpt strongly corresponds to the relevant technical
concept or describes a technically equivalent implementation.

Exact wording is not required.


INFERENTIAL
-----------

The excerpt provides concrete technical facts from which the
relevant claimed concept can reasonably be inferred.

Reasonable technical inference is allowed.

The inference must remain grounded in the excerpt.


CONTEXTUAL
----------

The excerpt is relevant to the technology or product but
provides little meaningful support for the specific claim
element.

Examples:

- general background;
- general product description;
- generic capability;
- component mentioned without the relevant function.


UNSUPPORTED
-----------

Use only when the excerpt provides no meaningful technical
support.

Examples:

- materially unrelated technology;
- coincidental terminology;
- technically different component;
- technically different operation;
- substantial missing technical fact.


============================================================
TECHNICAL TERMINOLOGY
============================================================

Do NOT require:

- word-for-word matching;
- identical terminology;
- patent-style language.

Accept reasonable differences in:

- component names;
- operation names;
- industry terminology;
- implementation descriptions;
- sentence structures;
- descriptions of the same technical behavior.

Different terminology alone is NOT a reason for unsupported.


============================================================
REASONABLE TECHNICAL INFERENCE
============================================================

Do NOT equate:

"not explicitly stated"

with:

"unsupported."

If the disclosed technical facts reasonably establish a relevant
concept through ordinary technical interpretation or inference,
use SUPPORTIVE or INFERENTIAL.

However, do not invent:

- components;
- operations;
- capabilities;
- relationships;
- target-specific facts.


============================================================
OUTSIDE KNOWLEDGE
============================================================

Use the evidence excerpt as the factual basis.

Ordinary technical interpretation of terminology actually
present in the excerpt is allowed.

Do not import substantive facts that are completely absent
from the evidence.


============================================================
DO NOT
============================================================

1. Require word-for-word matching.

2. Require identical terminology.

3. Require patent-style language.

4. Require one evidence item to establish the complete element.

5. Reject an evidence item because another evidence item would
   be needed for another limitation.

6. Reject reasonable technical inference.

7. Assume a technical relationship merely because two
   components are mentioned.

8. Introduce substantive facts from outside the excerpt.

9. Treat generic technology discussion as specific technical
   support.

10. Decide the final element-level mapping.


============================================================
EVIDENCE SUPPORTED
============================================================

Set:

evidence_supported = true

for:

- direct;
- supportive;
- inferential.

Set:

evidence_supported = false

for:

- contextual;
- unsupported.

This boolean means:

"This evidence has meaningful technical value for later
mapping."

It does NOT mean:

"The complete claim element has been proven."


============================================================
CONFIDENCE
============================================================

Confidence reflects the strength of THIS evidence item.

Use approximately:

0.90 - 1.00
Direct and unambiguous.

0.80 - 0.89
Strong technical correspondence.

0.70 - 0.79
Reasonable technical inference.

0.40 - 0.69
Relevant but limited technical contribution.

0.00 - 0.39
Unsupported or nearly unsupported.


Do NOT reduce confidence merely because other claim limitations
are absent from the evidence item.

Do NOT increase confidence merely because the excerpt contains
many related words.


============================================================
REASONING
============================================================

For every evidence item explain:

1. What technical fact is disclosed.

2. Which part of the claim element it relates to.

3. Whether equivalent terminology is used.

4. Whether reasonable inference is required.

5. If contextual or unsupported, what prevents stronger support.

Do NOT state that the complete claim element is proven.


============================================================
OUTPUT REQUIREMENTS
============================================================

1. Return exactly one result for every evidence index.

2. Preserve every evidence index exactly.

3. Do not skip any evidence index.

4. Do not duplicate any evidence index.

5. Evaluate every evidence item independently.

6. Populate support_level for every result.

7. Set evidence_supported consistently with support_level.

8. Return only the requested structured output.
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=EvidenceVerificationBatchResult,
        )

        parsed = (
            EvidenceVerificationBatchResult
            .model_validate_json(result)
        )

        # ========================================================
        # INDEX VALIDATION
        # ========================================================

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

        # ========================================================
        # SUPPORT-LEVEL VALIDATION
        # ========================================================

        results_by_index = {
            item.evidence_index: item
            for item in parsed.results
        }

        normalized_results = []

        for index in range(
            len(evidence_list)
        ):

            item = results_by_index[index]

            expected_supported = (
                item.support_level
                in {
                    "direct",
                    "supportive",
                    "inferential",
                }
            )

            if (
                item.evidence_supported
                != expected_supported
            ):
                raise ValueError(
                    "Evidence verification batch returned "
                    f"inconsistent evidence_supported value "
                    f"for evidence index {index}."
                )

            normalized_results.append(
                EvidenceVerificationResult(
                    claim_element_id=claim_element.id,
                    evidence_supported=(
                        item.evidence_supported
                    ),
                    confidence=item.confidence,
                    reasoning=item.reasoning,
                    support_level=item.support_level,
                )
            )

        return normalized_results
