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

        evidence_text = "\n\n".join(
            (
                f"EVIDENCE INDEX: {index}\n"
                f"Source: {item.evidence.source_title}\n"
                f"Evidence Type: "
                f"{item.evidence.evidence_type}\n"
                f"Excerpt:\n"
                f"{item.evidence.excerpt}\n"
                f"Individual Support Level: "
                f"{item.verification.support_level}\n"
                f"Individual Confidence: "
                f"{item.verification.confidence}\n"
                f"Individual Reasoning: "
                f"{item.verification.reasoning}"
            )
            for index, item in enumerate(
                verified_evidence
            )
        )

        prompt = f"""
You are a patent claim mapping and evidence aggregation
assistant.

Your task is to determine whether the available verified
evidence, considered collectively, supports the complete
technical substance of a specific patent claim element.

This is an ELEMENT-LEVEL assessment.

Individual evidence has already been evaluated separately.

Your task is now to determine whether multiple pieces of
evidence can reasonably be combined to establish the claim
element.


CLAIM ELEMENT:

ID:
{claim_element.id}

TEXT:
{claim_element.text}


VERIFIED EVIDENCE:

{evidence_text}


CORE METHOD:

First, decompose the claim element into its meaningful
technical limitations.

Consider:

- components;
- operations;
- conditions;
- inputs;
- outputs;
- technical relationships;
- sequencing;
- dependencies;
- functional interactions.

Then determine which evidence item or combination of evidence
items establishes each limitation.


IMPORTANT: EVIDENCE MAY BE COMBINED

Do NOT require a single evidence item to establish the entire
claim element.

A claim element may be supported by multiple pieces of
evidence where:

- one source establishes one technical component;
- another source establishes another component;
- another source establishes an operation;
- another source establishes a condition;
- another source establishes the relationship between them.

The evidence may therefore form a technical evidence chain.


EXAMPLE:

Suppose a claim element requires:

A → analyzes traffic

B → identifies traffic satisfying criteria

C → routes qualifying traffic to a specialized system

The evidence could consist of:

Evidence 0:
A source describing traffic analysis.

Evidence 1:
A source describing identification/classification of
qualifying traffic.

Evidence 2:
A source describing diversion of qualifying traffic to
the specialized system.

If those pieces describe the same relevant product/system
and form a coherent technical workflow, they may collectively
support the claim element.

Do NOT reject the element merely because no single excerpt
contains A + B + C.


EVIDENCE COMBINATION RULES:

Evidence may be combined when the combination is technically
coherent and the relationship between the pieces is reasonably
supported.

Reasonable technical inference is allowed.

However, do NOT invent missing technical facts merely to make
the evidence fit the claim.

The combination must be grounded in the actual evidence.


SUPPORT LEVELS:

Use exactly one overall support level:

"direct"
"supportive"
"inferential"
"contextual"
"unsupported"


DIRECT:

The complete claim element is explicitly established by the
available evidence, either through one source or through
multiple sources that directly disclose the relevant
limitations and relationships.


SUPPORTIVE:

The evidence collectively provides strong technical
correspondence to the complete claim element.

Some terminology, implementation detail, or expression may
differ from the claim, but the technical correspondence is
clear.


INFERENTIAL:

The evidence collectively supports the claim element through
reasonable technical inference.

The underlying technical facts are present, but one or more
relationships or conclusions must be reasonably inferred.

This is allowed.

Do not use INFERENTIAL merely because the claim and evidence
use different terminology.


CONTEXTUAL:

The evidence is relevant to the technology or product but
does not collectively establish the claimed technical
limitations.


UNSUPPORTED:

The evidence contains a genuine technical gap that prevents
the claim element from being reasonably established.


CRITICAL DISTINCTION:

Do NOT treat:

"not explicitly stated"

as automatically meaning:

"unsupported."

The relevant question is:

"Do the available pieces of evidence, taken together, provide
a technically reasonable basis for the claimed limitation and
relationships?"

If yes, the element may be SUPPORTIVE or INFERENTIAL.


CROSS-SOURCE EVIDENCE:

Multiple sources may be combined when they describe the same
product, system, technology, implementation, or technically
connected environment.

Do not assume that unrelated sources describe the same system
merely because they use similar terminology.

When combining sources, explain why the combination is
technically coherent.


SOURCE RELATIONSHIPS:

Consider the source title, source content, product references,
technical terminology, and described architecture when
determining whether evidence belongs to the same technical
system.

Do not use outside facts to establish a connection that the
provided evidence does not reasonably support.


INDIVIDUAL SUPPORT LEVELS:

The individual verification levels are informative.

A combination may be stronger than any individual evidence
item.

For example:

- inferential + direct may produce supportive element-level
  support;
- supportive + supportive may produce strong element-level
  support;
- several contextual items should NOT automatically become
  supporting evidence.

Do not simply average confidence scores.


MISSING LIMITATIONS:

If an important claim limitation remains genuinely unsupported
after considering all evidence, the element should normally
remain unsupported.

However, do not treat a limitation as missing merely because:

- it uses different terminology;
- it appears in another evidence item;
- the evidence describes the implementation rather than the
  patent-style wording;
- the relationship can reasonably be inferred from disclosed
  technical facts.


EVIDENCE INDEXES:

For every evidence combination, use the exact evidence indexes
provided above.

Do not invent evidence indexes.

The returned "evidence" field must contain the actual evidence
objects that contribute to the element-level conclusion.


REASONING:

The reasoning should:

1. Identify the major technical limitations of the claim element.
2. Explain which evidence item(s) establish each limitation.
3. Explain how the evidence items relate to one another.
4. Explain any reasonable technical inference.
5. Identify any genuine remaining gap.
6. Explain why the final support level was selected.

Do not simply state:

"Evidence supports the claim."

Explain the evidence chain.


CONFIDENCE:

Confidence represents the strength of the COMPLETE
element-level mapping.

It is NOT an average of individual evidence confidence scores.

Use approximately:

0.90 - 1.00:
Complete and strong technical support with little ambiguity.

0.80 - 0.89:
Strong collective technical support with minor terminology
or implementation differences.

0.70 - 0.79:
Reasonable collective support requiring some technical
inference.

0.60 - 0.69:
Meaningful but incomplete or ambiguous support.

0.00 - 0.59:
Insufficient support for the complete claim element.


IMPORTANT:

Do not artificially increase confidence merely because there
are many evidence items.

Three weak sources do not automatically outweigh one genuine
technical gap.


OUTPUT:

Return exactly the requested structured output.

The output must:

- preserve the claim_element_id;
- return supported=True only when the complete element is
  reasonably supported;
- return the relevant evidence objects;
- populate support_level;
- populate evidence_combinations;
- provide a clear technical reasoning chain.
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=ClaimElementMapping,
        )

        mapping = ClaimElementMapping.model_validate_json(
            result
        )

        return mapping
