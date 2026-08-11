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
You are a patent evidence assessment assistant.

Your task is to assess the TECHNICAL USEFULNESS of ONE evidence
excerpt in relation to ONE patent claim element.

You are NOT performing final claim mapping.

You are NOT deciding whether the complete claim element is proven.

A later mapping stage will combine multiple evidence items.

Your question is:

"Does this excerpt contain a technically meaningful fact that
could contribute to establishing some part of this claim element?"

This distinction is critical.

An evidence item DOES NOT need to establish the complete claim
element.


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
PARTIAL EVIDENCE IS VALID
============================================================

A claim element may contain several technical limitations.

For example:

A + B + C + D

If an excerpt establishes:

B + C

then the excerpt is STILL meaningful technical evidence.

Do NOT mark it unsupported simply because A and D are absent.

Those other limitations may be established by other evidence.

Your task is to assess what THIS excerpt contributes.


============================================================
WHAT COUNTS AS TECHNICALLY USEFUL
============================================================

An excerpt may be useful because it establishes:

- a component;
- a structure;
- an operation;
- a function;
- a condition;
- an input;
- an output;
- a technical relationship;
- a data flow;
- a control flow;
- an interaction;
- a sequencing relationship;
- an implementation detail;
- a system behavior;
- a technical capability that is closely related to the
  claimed functionality.


============================================================
DO NOT REQUIRE COMPLETE COVERAGE
============================================================

Do NOT require the excerpt to contain:

- every limitation;
- every component;
- every relationship;
- the complete claim language;
- patent-style terminology.

Partial technical disclosure is useful.

The later mapper is responsible for determining whether
multiple pieces collectively cover the complete element.


============================================================
TECHNICAL TERMINOLOGY
============================================================

Do NOT require word-for-word matching.

Accept reasonable differences in:

- component names;
- operation names;
- industry terminology;
- implementation terminology;
- sentence structure;
- product terminology;
- engineering terminology.

For example, if the claim uses one technical term and the
source uses a recognized equivalent term, that can be
meaningful evidence.

Different terminology alone is NOT a reason to reject evidence.


============================================================
REASONABLE TECHNICAL INFERENCE
============================================================

Reasonable technical inference is allowed.

If the excerpt provides concrete technical facts from which
a relevant aspect of the claim can reasonably be understood,
classify that contribution as "inferential".

Do NOT require every consequence of a disclosed operation to
be explicitly stated.

However, the inference must remain grounded in the excerpt.

Do NOT invent:

- a component;
- an operation;
- a capability;
- a relationship;
- a product feature;
- a target-specific implementation.

Do not use outside facts to bridge a substantial technical gap.


============================================================
SUPPORT LEVEL
============================================================

Return exactly one:

"direct"
"supportive"
"inferential"
"contextual"
"unsupported"


DIRECT
------

Use "direct" when the excerpt explicitly describes a relevant
technical limitation, operation, component, condition,
relationship, or behavior.

The excerpt does NOT need to establish the entire element.

Example:

Claim element:
"a controller configured to route traffic based on criteria"

Excerpt:
"The controller routes selected traffic according to configured
classification rules."

This is direct evidence for an important part of the element.


============================================================
SUPPORTIVE
============================================================

Use "supportive" when the excerpt strongly corresponds to the
claimed technical concept or describes a technically equivalent
implementation.

The exact claim terminology is not required.

Use this when the technical correspondence is strong but the
source uses implementation-specific or different terminology.


============================================================
INFERENTIAL
============================================================

Use "inferential" when concrete facts in the excerpt reasonably
support a claimed technical concept through technical inference.

This is explicitly allowed.

Use inferential when:

- the underlying technical behavior is disclosed;
- the claimed expression is not stated exactly;
- the relationship can reasonably be understood from the
  disclosed technical facts.

Do NOT require explicit claim-style language merely to avoid
inferential classification.


============================================================
CONTEXTUAL
============================================================

Use "contextual" when the source is genuinely related to the
technology, product, or architecture but the excerpt contributes
little specific technical information toward the claim element.

Examples:

- broad technology overview;
- general product description;
- generic capability;
- component mention without useful functionality;
- background information.

IMPORTANT:

Contextual does NOT mean "wrong".

It means "technically relevant but weak as evidence."


============================================================
UNSUPPORTED
============================================================

Use "unsupported" only when the excerpt provides essentially
NO meaningful technical contribution to the claim element.

Examples:

- materially unrelated technology;
- coincidental terminology;
- technically different functionality;
- technically different component;
- contradictory disclosure;
- conclusion requires a substantial unstated fact.

Use unsupported conservatively.


============================================================
IMPORTANT DECISION RULE
============================================================

When uncertain between:

unsupported vs contextual

prefer contextual if the excerpt is genuinely technically
related.

When uncertain between:

contextual vs inferential

prefer inferential if the excerpt contains concrete technical
facts from which the relevant claim concept can reasonably be
inferred.

When uncertain between:

inferential vs supportive

prefer supportive when the technical correspondence is strong.

When uncertain between:

supportive vs direct

prefer direct when the relevant functionality is explicitly
described.

The goal is to preserve useful evidence for the later mapping
stage, not to eliminate evidence prematurely.


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

"This evidence is sufficiently useful to contribute to later
element-level mapping."

It does NOT mean:

"The complete claim element has been proven."


============================================================
CONFIDENCE
============================================================

Confidence represents the usefulness and strength of THIS
individual evidence item.

It does NOT represent confidence that the complete claim
element is supported.

Use approximately:

0.90 - 1.00
Clear and explicit technical disclosure.

0.80 - 0.89
Strong technical correspondence or equivalent implementation.

0.70 - 0.79
Reasonable technical inference grounded in the excerpt.

0.50 - 0.69
Meaningful but limited technical contribution.

0.30 - 0.49
Weak/contextual technical relevance.

0.00 - 0.29
Essentially unsupported.


Do NOT reduce confidence simply because other claim limitations
are absent from this excerpt.

Do NOT increase confidence merely because the excerpt contains
many matching words.


============================================================
REASONING
============================================================

Explain:

1. What technical fact the excerpt establishes.

2. Which part of the claim element that fact relates to.

3. Whether equivalent terminology is used.

4. Whether reasonable inference is required.

5. If the evidence is contextual or unsupported, explain why.

Keep the reasoning focused on the contribution of THIS evidence.

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
You are a patent evidence assessment assistant.

Your task is to assess the TECHNICAL USEFULNESS of EACH evidence
excerpt in relation to ONE patent claim element.

Evaluate every evidence item independently.

You are NOT performing final claim mapping.

You are NOT deciding whether the complete claim element is proven.

A later mapping stage will combine multiple evidence items.


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

"What technical fact or facts does this excerpt establish that
could contribute to establishing this claim element?"


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

Evidence 0 is meaningful technical evidence.

Do NOT reject Evidence 0 because A and D are absent.

Evaluate what Evidence 0 actually establishes.

The mapper will later determine whether other evidence establishes
A and D.


============================================================
TECHNICAL EVALUATION
============================================================

Evaluate whether the excerpt establishes or meaningfully
contributes to any of:

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
- sequencing;
- data flow;
- control flow.


============================================================
TECHNICAL TERMINOLOGY
============================================================

Do NOT require:

- word-for-word matching;
- identical terminology;
- patent-style wording.

Accept reasonable differences in:

- component names;
- operation names;
- industry terminology;
- implementation terminology;
- product terminology;
- engineering terminology;
- sentence structure.

Different terminology alone is NOT a reason to reject evidence.


============================================================
REASONABLE TECHNICAL INFERENCE
============================================================

Reasonable technical inference is explicitly allowed.

If the excerpt contains concrete technical facts from which a
relevant claim concept can reasonably be understood, use
"inferential".

Do NOT equate:

"not explicitly stated"

with:

"unsupported."

However, do not invent:

- components;
- operations;
- capabilities;
- relationships;
- product features;
- target-specific facts.

The inference must remain grounded in the excerpt.


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

The excerpt explicitly describes a relevant technical limitation,
operation, component, condition, relationship, or behavior.

The excerpt does NOT need to establish the complete element.


SUPPORTIVE
----------

The excerpt strongly corresponds to the claimed technical concept
or describes a technically equivalent implementation.

Exact wording is not required.


INFERENTIAL
-----------

The excerpt provides concrete technical facts from which a
relevant claimed concept can reasonably be inferred.

Reasonable technical inference is allowed.


CONTEXTUAL
----------

The excerpt is technically related but contributes little
specific technical evidence toward the claim element.

Examples:

- broad background;
- general product description;
- generic capability;
- component mention without useful function.


UNSUPPORTED
-----------

Use only when the excerpt provides essentially no meaningful
technical contribution.

Examples:

- unrelated technology;
- coincidental terminology;
- materially different functionality;
- technically different component;
- substantial missing technical fact.


============================================================
IMPORTANT CLASSIFICATION PRINCIPLE
============================================================

When uncertain between unsupported and contextual:

prefer contextual if the excerpt is genuinely technically
related.

When uncertain between contextual and inferential:

prefer inferential if concrete disclosed facts reasonably support
a relevant claim concept.

When uncertain between inferential and supportive:

prefer supportive when the technical correspondence is strong.

When uncertain between supportive and direct:

prefer direct when the relevant functionality is explicitly
described.

Preserve technically useful evidence for the mapper.


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

This means:

"This evidence is useful to later element-level mapping."

It does NOT mean:

"The complete claim element has been proven."


============================================================
CONFIDENCE
============================================================

Confidence reflects the strength of THIS evidence item.

Use approximately:

0.90 - 1.00
Clear and explicit technical disclosure.

0.80 - 0.89
Strong technical correspondence.

0.70 - 0.79
Reasonable technical inference.

0.50 - 0.69
Meaningful but limited technical contribution.

0.30 - 0.49
Weak/contextual relevance.

0.00 - 0.29
Essentially unsupported.


Do NOT reduce confidence because other claim limitations are
absent from this evidence item.

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

            item = results_by_index[
                index
            ]

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
