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

Your task is to assess the TECHNICAL VALUE of ONE evidence
excerpt in relation to a patent claim element.

You are NOT deciding whether the complete claim element is
established.

You are NOT deciding whether the complete claim is supported.

You are evaluating only what this particular evidence excerpt
contributes to the claim element.

A later claim-mapping stage will combine multiple evidence items.


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


============================================================
PRIMARY QUESTION
============================================================

Ask:

"What technical fact or facts does this evidence actually
establish that are relevant to this claim element?"

The evidence does NOT need to establish the entire claim
element.

It is enough for the evidence to establish one meaningful
technical limitation, component, operation, condition, input,
output, or relationship contained within the claim element.


============================================================
IMPORTANT EVIDENCE-SCOPE RULE
============================================================

DO NOT penalize an evidence item because it fails to establish
other limitations of the claim element.

For example, if the claim element contains:

A + B + C + D

and this evidence clearly establishes:

B + C

then this is still meaningful evidence.

Do NOT mark it unsupported merely because A and D are not
present.

The later mapping stage will determine whether other evidence
establishes A and D.


============================================================
SUPPORT LEVEL
============================================================

Return exactly ONE of:

"direct"
"supportive"
"inferential"
"contextual"
"unsupported"


------------------------------------------------------------
DIRECT
------------------------------------------------------------

Use DIRECT when the excerpt explicitly describes the relevant
technical limitation, operation, component, condition, or
relationship.

The wording does NOT need to match the claim word-for-word.

Equivalent technical terminology is acceptable.


------------------------------------------------------------
SUPPORTIVE
------------------------------------------------------------

Use SUPPORTIVE when the excerpt strongly corresponds to a
claimed technical concept or describes a technically equivalent
implementation.

The relationship should be clear to a technically knowledgeable
reader even if the source uses different terminology.


------------------------------------------------------------
INFERENTIAL
------------------------------------------------------------

Use INFERENTIAL when the excerpt provides concrete technical
facts from which a relevant claimed concept can reasonably be
inferred.

Reasonable technical inference is explicitly allowed.

For example, if a source describes the component and its
operation in a way that naturally establishes the claimed
function, INFERENTIAL may be appropriate even if the source
does not state the function using the claim's exact wording.


------------------------------------------------------------
CONTEXTUAL
------------------------------------------------------------

Use CONTEXTUAL when the source is genuinely relevant to the
technology but the excerpt provides little meaningful
element-specific technical support.

Examples:

- general technology background;
- general product description;
- mention of a component without a relevant function;
- general discussion of the technology.


------------------------------------------------------------
UNSUPPORTED
------------------------------------------------------------

Use UNSUPPORTED only when the excerpt provides no meaningful
technical support for the claim element.

Examples:

- materially unrelated technology;
- coincidental terminology;
- technically different component;
- technically different operation;
- claimed concept is contradicted by the excerpt;
- the conclusion would require a substantial unstated fact.


============================================================
TECHNICAL EQUIVALENCE
============================================================

Accept reasonable technical equivalence.

The source and claim may use different:

- component names;
- operation names;
- industry terminology;
- implementation terminology;
- sentence structures;
- descriptions of the same technical behavior.

Do not require patent-style language.


============================================================
REASONABLE INFERENCE
============================================================

Reasonable technical inference is allowed.

Do NOT require the source to explicitly state every consequence
of a disclosed technical operation.

However, the inference must be grounded in facts actually present
in the excerpt.

Do not invent a missing component, operation, capability, or
relationship.


============================================================
OUTSIDE KNOWLEDGE
============================================================

Do not use outside knowledge to manufacture evidence.

However, ordinary technical interpretation of terminology that
actually appears in the excerpt is allowed.

For example, if the source uses a recognized technical term for
an operation, you may interpret that term according to its
ordinary technical meaning.

Do not add facts that are completely absent from the excerpt.


============================================================
WHAT YOU MUST NOT DO
============================================================

1. Do not require word-for-word matching.

2. Do not require identical terminology.

3. Do not reject evidence because it covers only part of the
   claim element.

4. Do not decide the complete claim element.

5. Do not decide the complete patent claim.

6. Do not require a single evidence item to establish every
   limitation.

7. Do not reject reasonable technical inference.

8. Do not assume a technical relationship merely because two
   components happen to be mentioned.

9. Do not manufacture facts from outside knowledge.

10. Do not treat general technology discussion as direct evidence.

11. Do not claim that the source explicitly states something
    that it does not state.


============================================================
EVIDENCE_SUPPORTED
============================================================

Set:

evidence_supported = TRUE

when support_level is:

- direct
- supportive
- inferential

Set:

evidence_supported = FALSE

when support_level is:

- contextual
- unsupported


============================================================
CONFIDENCE
============================================================

Confidence reflects the strength of THIS evidence item.

It does NOT represent confidence that the entire claim element
is supported.

Use approximately:

0.90 - 1.00
Explicit, clear technical disclosure.

0.80 - 0.89
Strong technical correspondence or equivalent implementation.

0.70 - 0.79
Reasonable technical inference grounded in disclosed facts.

0.40 - 0.69
Relevant context or limited technical contribution.

0.00 - 0.39
Little or no meaningful support.


Do NOT reduce confidence merely because other claim limitations
are absent from this evidence.

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

5. If the evidence is contextual or unsupported, identify the
   specific reason.

The reasoning must describe the contribution of THIS evidence.

Do not state that the complete claim element is proven.


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

        return parsed

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
            for index, evidence in enumerate(
                evidence_list
            )
        )

        prompt = f"""
You are a patent evidence verification assistant.

Your task is to assess the TECHNICAL VALUE of EACH evidence
excerpt in relation to a patent claim element.

Evaluate each evidence item independently.

You are NOT deciding whether the complete claim element is
established.

You are NOT deciding whether the complete claim is supported.

A later claim-mapping stage will combine multiple evidence
items.


CLAIM ELEMENT:

ID:
{claim_element.id}

TEXT:
{claim_element.text}


EVIDENCE EXCERPTS:

{evidence_text}


============================================================
PRIMARY QUESTION
============================================================

For EACH evidence item, ask:

"What technical fact or facts does this evidence establish
that are relevant to this claim element?"

An evidence item does NOT need to establish the entire claim
element.

It may establish one meaningful:

- component;
- operation;
- condition;
- input;
- output;
- technical relationship;
- implementation detail;
- functional behavior.

The later mapping stage will determine whether multiple pieces
collectively establish the complete element.


============================================================
CRITICAL RULE
============================================================

DO NOT mark an evidence item unsupported merely because it does
not contain every limitation of the claim element.

For example:

Claim element:

A + B + C + D

Evidence 0:

B + C

Evidence 0 can still be meaningful evidence.

Assess what Evidence 0 establishes.

Do NOT penalize it for the absence of A and D.


============================================================
SUPPORT LEVELS
============================================================

Use exactly one:

"direct"
"supportive"
"inferential"
"contextual"
"unsupported"


DIRECT:

The evidence explicitly discloses the relevant technical
limitation, operation, component, condition, or relationship.

Equivalent terminology is acceptable.


SUPPORTIVE:

The evidence strongly corresponds to the relevant claimed
technical concept or describes a technically equivalent
implementation.

Exact wording is not required.


INFERENTIAL:

The evidence provides concrete technical facts from which the
relevant claimed concept can reasonably be inferred.

Reasonable technical inference is allowed.

The inference must remain grounded in the excerpt.


CONTEXTUAL:

The evidence is relevant to the technology but provides little
meaningful support for the specific claim element.

Examples include general background, general product
description, or a component mentioned without the relevant
function.


UNSUPPORTED:

The evidence provides no meaningful technical support for the
claim element.

Use this only when there is a genuine technical gap or the
technology is materially different.


============================================================
TECHNICAL EQUIVALENCE
============================================================

Accept:

- equivalent terminology;
- ordinary industry terminology;
- different component names;
- different operation names;
- different sentence structures;
- different implementation descriptions;
- reasonable technical interpretation of terminology actually
  present in the evidence.


============================================================
REASONABLE INFERENCE
============================================================

Do NOT equate:

"not explicitly stated"

with:

"unsupported."

If the disclosed facts reasonably establish a relevant technical
concept through ordinary technical interpretation or inference,
use SUPPORTIVE or INFERENTIAL.

Only use UNSUPPORTED when the missing information creates a
genuine technical gap.


============================================================
OUTSIDE KNOWLEDGE
============================================================

Do not use outside knowledge to manufacture missing facts.

Ordinary technical interpretation of terminology actually present
in the evidence is allowed.

Do not assume a component, operation, capability, or relationship
that is completely absent from the evidence.


============================================================
DO NOT
============================================================

1. Require word-for-word matching.

2. Require identical terminology.

3. Require patent-style language.

4. Require the evidence to establish the entire claim element.

5. Reject an evidence item because another evidence item would be
   needed to establish another limitation.

6. Reject reasonable technical inference.

7. Assume relationships merely because components are mentioned.

8. Introduce substantive facts from outside the excerpt.

9. Treat generic technology discussion as proof of a specific
   technical limitation.

10. Decide the final element-level mapping.


============================================================
EVIDENCE_SUPPORTED
============================================================

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


The boolean describes whether the evidence has meaningful
technical value.

It does NOT mean that the complete claim element has been proven.


============================================================
CONFIDENCE
============================================================

Confidence reflects the strength of THIS evidence item.

0.90 - 1.00
Direct and unambiguous.

0.80 - 0.89
Strong technical correspondence.

0.70 - 0.79
Reasonable technical inference.

0.40 - 0.69
Relevant but limited/contextual.

0.00 - 0.39
Unsupported or nearly unsupported.


Do NOT reduce confidence simply because other claim limitations
are absent from this evidence item.


============================================================
REASONING
============================================================

For every evidence item explain:

1. What technical fact is disclosed.

2. Which part of the claim element it relates to.

3. Whether equivalent terminology is used.

4. Whether reasonable inference is required.

5. If contextual or unsupported, what the specific limitation is
   that prevents stronger support.


Do not state that the complete claim element is proven.


============================================================
OUTPUT REQUIREMENTS
============================================================

1. Return exactly one result for every evidence index.

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

        parsed = (
            EvidenceVerificationBatchResult
            .model_validate_json(result)
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
                evidence_supported=(
                    results_by_index[index]
                    .evidence_supported
                ),
                confidence=(
                    results_by_index[index]
                    .confidence
                ),
                reasoning=(
                    results_by_index[index]
                    .reasoning
                ),
                support_level=(
                    results_by_index[index]
                    .support_level
                ),
            )
            for index in range(
                len(evidence_list)
            )
        ]
