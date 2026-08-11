from app.models.schemas import (
    ClaimElement,
    VerifiedEvidence,
    ClaimElementMapping,
)
from app.services.gemini_service import GeminiService


class ClaimMapper:

    def __init__(self):
        self.llm = GeminiService()

    def map(
        self,
        claim_element: ClaimElement,
        verified_evidence: list[VerifiedEvidence],
    ) -> ClaimElementMapping:

        if not verified_evidence:
            return ClaimElementMapping(
                claim_element_id=claim_element.id,
                supported=False,
                confidence=0.0,
                evidence=[],
                reasoning=(
                    "No verified evidence is available "
                    "for this claim element."
                ),
                support_level="unsupported",
                evidence_combinations=[],
            )

        # ========================================================
        # BUILD EVIDENCE CONTEXT
        # ========================================================

        evidence_sections = []

        for index, item in enumerate(
            verified_evidence
        ):

            evidence_sections.append(
                f"""
EVIDENCE INDEX: {index}

SOURCE TITLE:
{item.evidence.source_title}

SOURCE URL:
{item.evidence.url}

SOURCE EVIDENCE TYPE:
{item.evidence.evidence_type}

EXCERPT:
{item.evidence.excerpt}

INDIVIDUAL SUPPORT LEVEL:
{item.verification.support_level}

INDIVIDUAL CONFIDENCE:
{item.verification.confidence}

INDIVIDUAL REASONING:
{item.verification.reasoning}
""".strip()
            )

        evidence_text = "\n\n".join(
            evidence_sections
        )

        # ========================================================
        # MAPPING PROMPT
        # ========================================================

        prompt = f"""
You are a patent claim-element mapping and evidence
aggregation assistant.

Your task is to determine how strongly the available verified
technical evidence supports ONE specific patent claim element.

This is an ELEMENT-LEVEL assessment.

The evidence has already gone through individual evidence
verification.

Your task is NOT to re-verify every excerpt from scratch.

Your task is to determine whether the available evidence,
individually and collectively, provides a technically reasonable
basis for the COMPLETE claim element.


============================================================
CLAIM ELEMENT
============================================================

ID:
{claim_element.id}

TEXT:
{claim_element.text}


============================================================
VERIFIED EVIDENCE
============================================================

{evidence_text}


============================================================
CORE PRINCIPLE
============================================================

Be LIBERAL about useful evidence but DISCIPLINED about the
final conclusion.

Do not reject an element simply because:

- one excerpt does not contain the entire limitation;
- terminology differs;
- the implementation is described rather than the claim
  wording;
- multiple excerpts are needed;
- a reasonable technical inference is required.

However, do not declare an element supported merely by
assembling unrelated facts from unrelated sources.

The question is:

"Taken together, do these evidence items provide a technically
reasonable basis for the complete claim element?"


============================================================
STEP 1 — DECOMPOSE THE CLAIM ELEMENT
============================================================

First identify the meaningful technical limitations contained
within the claim element.

Consider:

- components;
- structures;
- operations;
- inputs;
- outputs;
- conditions;
- relationships;
- sequencing;
- dependencies;
- functional interactions;
- configuration;
- causality.

Do NOT rewrite the claim.

Use the decomposition internally to evaluate coverage.


============================================================
STEP 2 — MAP EVIDENCE TO LIMITATIONS
============================================================

For each meaningful limitation, determine which evidence item
or items provide support.

An individual evidence item may support:

- an entire limitation;
- part of a limitation;
- a technical relationship;
- an implementation detail;
- contextual information.

A single evidence item does NOT need to establish the entire
claim element.


============================================================
PARTIAL EVIDENCE IS VALID
============================================================

Do NOT require one excerpt to establish every limitation.

For example, suppose the claim element requires:

A. a controller;

B. receiving traffic information;

C. determining whether the traffic satisfies criteria; and

D. routing the qualifying traffic through a specialized system.

The available evidence might contain:

Evidence 0:
A source describing the controller receiving traffic
information.

Evidence 1:
A source describing classification or determination of
qualifying traffic.

Evidence 2:
A source describing routing qualifying traffic through a
specialized system.

These may collectively support the claim element if they form
a technically coherent implementation.


============================================================
TECHNICAL TERMINOLOGY
============================================================

Do NOT require identical terminology.

A source may describe a claimed concept using different
technical terminology.

Examples:

"route traffic"
vs.
"traffic steering"

"characteristic value"
vs.
"attribute value"

"specialized network edge"
vs.
"service edge"

"configured to receive"
vs.
"accepts"

Different terminology does NOT automatically mean unsupported.

Evaluate the underlying technical substance.

If the terminology represents only a superficial similarity,
do not treat it as technical support.


============================================================
TECHNICAL EQUIVALENCE VS INFERENCE
============================================================

Do not automatically classify terminology differences as
"inferential."

If the source clearly describes the same technical operation
using different industry terminology, it may still be
DIRECT or SUPPORTIVE.

Use INFERENTIAL when the evidence establishes underlying facts
from which a claimed relationship or functionality must
reasonably be inferred.

Do not invent missing facts.


============================================================
EVIDENCE COMBINATION
============================================================

Multiple evidence items may be combined.

Combine evidence when:

1. the technical facts are complementary;

2. the combination addresses different limitations of the same
   claim element;

3. the evidence describes the same product, system,
   implementation, architecture, or clearly connected
   technical environment; OR

4. the relationship between the sources is reasonably
   established by the evidence itself.

A combination does NOT require every source to explicitly
reference every other source.

However, do not assume unrelated sources describe the same
implementation merely because they use similar terminology.


============================================================
CROSS-SOURCE EVIDENCE
============================================================

Cross-source combination is allowed.

But apply this rule:

SIMILAR TECHNOLOGY ≠ SAME IMPLEMENTATION.

For example, two unrelated pages about Bluetooth technology
should not automatically be combined to construct a particular
product implementation.

Similarly, two unrelated networking articles should not be
combined merely because both discuss traffic routing.

Prefer combinations where sources share identifiable
connections such as:

- same company;
- same product;
- same platform;
- same component;
- same architecture;
- same protocol implementation;
- same documentation family;
- explicit references between the sources;
- clearly compatible technical descriptions.

If such a connection cannot reasonably be established,
describe the evidence as contextual or inferential rather
than treating it as strong collective proof.


============================================================
RELATIONSHIPS ARE CRITICAL
============================================================

Pay special attention to relationships in the claim.

Examples:

X receives Y.

X determines Z based on Y.

X performs A in response to B.

X routes Y through Z.

X writes A to B.

X reads A from B.

X communicates with Y.

X controls Y.

A source describing the individual components is NOT
automatically equivalent to a source describing the claimed
relationship between those components.

Where the claim depends on a relationship, the evidence should
support that relationship directly or through a reasonable
technical inference.


============================================================
DO NOT OVER-PENALIZE MISSING WORDS
============================================================

The absence of exact claim wording is not itself a technical
gap.

Do NOT conclude:

"The source does not use the exact phrase, therefore
unsupported."

Instead ask:

"Does the source disclose the underlying technical function,
structure, or relationship?"


============================================================
DO NOT OVER-CREDIT GENERIC INFORMATION
============================================================

Do not treat generic background information as substantive
support.

Examples of weak evidence:

- generic descriptions of a technology;
- generic product marketing;
- broad statements that a system is capable of networking;
- generic descriptions of a processor;
- generic statements that Bluetooth supports characteristics.

The evidence must contribute to the actual limitation being
mapped.


============================================================
SUPPORT LEVEL
============================================================

Return exactly one overall support level.

Allowed values:

"direct"
"supportive"
"inferential"
"contextual"
"unsupported"


------------------------------------------------------------
DIRECT
------------------------------------------------------------

Use DIRECT when the complete claim element is explicitly
established by the evidence.

This may come from:

- one strong source; OR
- multiple coherent sources where the relevant limitations
  and relationships are explicitly disclosed.


------------------------------------------------------------
SUPPORTIVE
------------------------------------------------------------

Use SUPPORTIVE when the evidence provides strong technical
correspondence to the complete claim element, but there are
minor differences in:

- terminology;
- implementation detail;
- expression;
- documentation granularity.

The technical substance is nevertheless strongly established.


------------------------------------------------------------
INFERENTIAL
------------------------------------------------------------

Use INFERENTIAL when the evidence establishes the underlying
technical facts, but one or more claimed relationships or
functional conclusions require reasonable technical inference.

Reasonable technical inference is allowed.

Do NOT use INFERENTIAL merely because terminology differs.


------------------------------------------------------------
CONTEXTUAL
------------------------------------------------------------

Use CONTEXTUAL when the evidence is relevant to the technology,
product, or architecture but does not provide enough support
for the complete claim element.


------------------------------------------------------------
UNSUPPORTED
------------------------------------------------------------

Use UNSUPPORTED when a genuine material technical limitation
remains unestablished after considering the available evidence.


============================================================
CRITICAL DISTINCTION
============================================================

Do NOT treat:

"not explicitly stated"

as automatically equivalent to:

"unsupported."

Instead determine whether the available evidence provides a
reasonable technical basis for the limitation.

At the same time, do not manufacture a missing limitation from
generic technical knowledge.


============================================================
MATERIAL GAPS
============================================================

If an important limitation genuinely remains unsupported,
the element should normally NOT be marked supported.

Examples of material gaps include:

- the claimed component is absent;
- the claimed operation is absent;
- the claimed input/output relationship is absent;
- the claimed condition is absent;
- the claimed causal relationship is absent;
- the claimed interaction between components is absent.

Minor wording differences are NOT material gaps.


============================================================
SUPPORTED FLAG
============================================================

Set:

supported = TRUE

only when the complete claim element is reasonably supported by
the available evidence.

A claim element can be supported even if:

- multiple evidence items are needed;
- terminology differs;
- some technical relationships are reasonably inferred;
- no single source contains the entire element.

Set:

supported = FALSE

when a material limitation or relationship remains genuinely
unsupported.


============================================================
EVIDENCE TO RETURN
============================================================

The "evidence" field should contain the actual Evidence objects
that materially contribute to the final element-level conclusion.

Do NOT automatically return every evidence item.

Exclude evidence that is merely:

- unrelated;
- generic;
- duplicative;
- purely contextual;
- unnecessary to the conclusion.

If the element is supported, return the evidence that forms the
supporting evidence chain.

If the element is unsupported but useful partial evidence exists,
return the relevant partial evidence that explains the conclusion.


============================================================
EVIDENCE COMBINATIONS
============================================================

Use "evidence_combinations" to explicitly describe meaningful
groups of evidence considered together.

For each combination:

- evidence_indexes must contain exact indexes from the provided
  evidence;
- support_level must describe the strength of that combination;
- supported indicates whether that combination contributes to
  supporting the relevant limitation(s);
- confidence represents the strength of that combination;
- reasoning explains what the combination establishes.

Do NOT create combinations merely because several evidence items
exist.

Create a combination only when the items meaningfully work
together.


============================================================
EVIDENCE INDEX RULES
============================================================

Only use evidence indexes that were actually provided.

Valid indexes are:

0 through {len(verified_evidence) - 1}

Do not invent indexes.

Every evidence combination must reference only valid indexes.


============================================================
CONFIDENCE
============================================================

Confidence represents the strength of the COMPLETE
element-level mapping.

It is NOT the number of evidence items.

It is NOT an average of individual evidence confidence values.


Use approximately:

0.90–1.00
Complete, strong technical support with little ambiguity.

0.80–0.89
Strong collective support with minor terminology or
implementation differences.

0.70–0.79
Reasonable collective support requiring some technical
inference.

0.60–0.69
Meaningful but incomplete or ambiguous support.

0.00–0.59
Insufficient support for the complete claim element.


Do not inflate confidence because multiple weak sources exist.

A large number of weak sources does not compensate for a
genuine material technical gap.


============================================================
REASONING
============================================================

The reasoning MUST explain:

1. the major limitations of the claim element;

2. which evidence items address those limitations;

3. how evidence items relate to one another;

4. any reasonable technical inference;

5. any genuine remaining gap;

6. why the final support level was selected;

7. why the evidence is technically coherent when multiple
   sources are combined.


Avoid generic statements such as:

"Evidence supports the claim."

Instead explain the actual evidence chain.


============================================================
FINAL DECISION
============================================================

Before returning the result, internally ask:

1. What are the actual technical limitations?

2. Which evidence addresses each limitation?

3. Are the evidence items technically connected?

4. Is the claimed relationship supported?

5. Am I rejecting evidence only because the wording differs?

6. Am I treating generic technical background as substantive
   evidence?

7. Am I combining unrelated sources?

8. Is there a genuine material technical gap?

9. Does the final support level accurately reflect the strength
   of the complete mapping?

Return only the requested structured output.
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=ClaimElementMapping,
        )

        mapping = (
            ClaimElementMapping
            .model_validate_json(result)
        )

        # ========================================================
        # BASIC OUTPUT VALIDATION
        # ========================================================

        if (
            mapping.claim_element_id
            != claim_element.id
        ):
            raise ValueError(
                "Claim mapper returned an invalid "
                "claim element ID."
            )

        valid_evidence_count = len(
            verified_evidence
        )

        for combination in (
            mapping.evidence_combinations
        ):

            for evidence_index in (
                combination.evidence_indexes
            ):

                if (
                    evidence_index < 0
                    or evidence_index >= valid_evidence_count
                ):
                    raise ValueError(
                        "Claim mapper returned an invalid "
                        "evidence index."
                    )

        # ========================================================
        # SUPPORT-LEVEL CONSISTENCY
        # ========================================================

        # A mapping marked supported=True should not simultaneously
        # claim that the complete element is unsupported/contextual.
        #
        # We do not override the model's judgment about the
        # technical substance, but we prevent internally
        # contradictory output.

        if (
            mapping.supported
            and mapping.support_level
            in {
                "contextual",
                "unsupported",
            }
        ):
            raise ValueError(
                "Claim mapper returned supported=True with "
                f"support level '{mapping.support_level}'."
            )

        if (
            not mapping.supported
            and mapping.support_level
            in {
                "direct",
                "supportive",
            }
        ):
            raise ValueError(
                "Claim mapper returned supported=False with "
                f"support level '{mapping.support_level}'."
            )

        return mapping
