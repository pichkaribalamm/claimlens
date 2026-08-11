from app.models.schemas import (
    ClaimElement,
    SearchResult,
    Evidence,
    EvidenceExtractionResult,
    EvidenceExtractionBatchResult,
)
from app.services.gemini_service import GeminiService


class EvidenceExtractor:

    def __init__(self):
        self.llm = GeminiService()

    # ============================================================
    # SINGLE SOURCE EXTRACTION
    # ============================================================

    def extract(
        self,
        claim_element: ClaimElement,
        search_result: SearchResult,
        reduced_content: str,
    ) -> list[Evidence]:

        if not reduced_content:
            return []

        prompt = f"""
You are a patent evidence extraction assistant.

Your task is to identify useful TECHNICAL EVIDENCE from the
provided source content that may contribute to assessing a
specific patent claim element.

You are an EVIDENCE EXTRACTOR.

You are NOT the final claim mapper.

You are NOT required to determine whether the complete claim
element is established.

Your job is to preserve concrete technical facts from the
source that could later be used by a separate verification
and claim-mapping stage.


============================================================
CLAIM ELEMENT
============================================================

ID:
{claim_element.id}

TEXT:
{claim_element.text}


============================================================
SOURCE
============================================================

TITLE:
{search_result.title}

URL:
{search_result.url}


============================================================
SOURCE CONTENT
============================================================

{reduced_content}


============================================================
PRIMARY OBJECTIVE
============================================================

Find concrete technical passages that may contribute to
establishing one or more parts of the claim element.

A useful evidence item may establish:

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
- a system interaction;
- a sequencing relationship;
- an implementation detail;
- a technical capability;
- a product behavior.


============================================================
PARTIAL EVIDENCE IS VALID
============================================================

An evidence excerpt does NOT need to establish the complete
claim element.

For example, if a claim element contains:

A + B + C + D

and the source contains a passage establishing:

B + C

that passage is still valuable evidence.

Do NOT reject it merely because A and D are not present.

Another source or another passage may establish A or D.

The later claim mapper will determine whether the available
evidence collectively supports the complete element.


============================================================
PRESERVE TECHNICAL RELATIONSHIPS
============================================================

Pay particular attention to relationships such as:

- receives X from Y;
- sends X to Y;
- routes X through Y;
- determines X based on Y;
- performs X in response to Y;
- identifies X according to Y;
- selects X based on Y;
- stores X in Y;
- writes X to Y;
- reads X from Y;
- controls X using Y;
- connects X to Y;
- communicates with Y;
- traffic entering through X;
- traffic originating from X;
- information received from X;
- data associated with X;
- a component interacting with another component.


A passage that establishes a relationship can be more valuable
than a passage that merely mentions the relevant components.


============================================================
TECHNICAL TERMINOLOGY
============================================================

Do not require exact claim terminology.

A source may use:

- different component names;
- implementation-specific terminology;
- abbreviated terminology;
- engineering terminology;
- product terminology;
- equivalent technical expressions.

If the source clearly describes a related technical concept,
extract it.

Do NOT discard evidence merely because the wording differs
from the claim.


============================================================
MULTIPLE EVIDENCE ITEMS
============================================================

A source may contain several distinct pieces of useful evidence.

Return separate evidence items when different passages establish
different technical facts.

For example:

Evidence 1:
describes a network edge controller.

Evidence 2:
describes traffic entering through an edge system.

Evidence 3:
describes identifying traffic according to criteria.

Evidence 4:
describes routing selected traffic to another edge system.

These may all be useful to the later mapper.

Do NOT force all of these facts into one evidence item.


============================================================
EXCERPT RULE
============================================================

Every "excerpt" MUST be copied EXACTLY from the provided
source content.

Do NOT:

- paraphrase;
- summarize;
- rewrite;
- combine non-contiguous text;
- invent connecting language;
- change technical terminology.

An excerpt may contain one, two, or three sentences when
necessary to preserve the technical relationship.

Prefer the shortest contiguous passage that preserves the
relevant technical fact or relationship.


============================================================
EVIDENCE GRANULARITY
============================================================

Prefer evidence units that are:

- technically meaningful;
- specific;
- concise;
- independently understandable.

Avoid returning:

- entire sections;
- large paragraphs;
- generic introductions;
- navigation text;
- marketing language;
- repeated boilerplate.

However, do NOT cut a passage so aggressively that the
technical relationship becomes unclear.


============================================================
DO NOT OVER-FILTER
============================================================

This stage should favor RECALL over final judgment.

If a passage contains a plausible and technically meaningful
connection to the claim element, it is better to preserve it
for later verification than to discard it prematurely.

Do NOT require the passage to independently prove the claim.

Do NOT require every claim limitation to appear in the
passage.


============================================================
DO NOT INFER
============================================================

Only extract facts that are actually present in the provided
source content.

Do not introduce facts from:

- general technical knowledge;
- memory;
- the target product;
- other sources;
- assumptions about how the product works.

The extractor may identify a passage as relevant, but the
technical fact must come from the source itself.


============================================================
EVIDENCE TYPE
============================================================

For each evidence item, "evidence_type" should describe the
nature of the source evidence.

Examples:

"product functionality"

"technical architecture"

"implementation description"

"product documentation"

"technical specification"

"system behavior"

"technical capability"

"network behavior"

"traffic handling"

"controller functionality"

"data flow"

"technical relationship"


Do NOT use:

- "direct";
- "supportive";
- "inferential";
- "contextual";
- "unsupported"

for evidence_type.

Those are verification classifications and belong to the
next pipeline stage.


============================================================
RELEVANCE
============================================================

The "relevance" field should briefly explain:

1. what technical fact the excerpt establishes; and
2. which part of the claim element that fact relates to.

Do not state that the claim element is proven.

Example:

"The passage describes traffic received from an ingress edge
system, which is relevant to the claimed receipt of information
about traffic entering the communication network."


============================================================
OUTPUT
============================================================

Return every meaningful evidence item you can identify from
the provided content.

If there is genuinely no technically meaningful evidence
related to the claim element, return an empty list.

Return only the requested structured output.
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=EvidenceExtractionResult,
        )

        parsed = (
            EvidenceExtractionResult
            .model_validate_json(result)
        )

        return parsed.evidence

    # ============================================================
    # BATCH EXTRACTION
    # ============================================================

    def extract_batch(
        self,
        claim_element: ClaimElement,
        sources: list[tuple[SearchResult, str]],
    ) -> list[list[Evidence]]:

        if not sources:
            return []

        source_sections = []

        for index, (
            search_result,
            reduced_content,
        ) in enumerate(sources):

            if not reduced_content:
                continue

            source_sections.append(
                (
                    f"SOURCE INDEX: {index}\n"
                    f"TITLE: {search_result.title}\n"
                    f"URL: {search_result.url}\n\n"
                    f"RELEVANT SOURCE CONTENT:\n"
                    f"{reduced_content}"
                )
            )

        if not source_sections:
            return [
                []
                for _ in sources
            ]

        prompt = f"""
You are a patent evidence extraction assistant.

Your task is to identify useful TECHNICAL EVIDENCE from
multiple source pages that may contribute to assessing one
specific patent claim element.

You are an EVIDENCE EXTRACTOR.

You are NOT the final claim mapper.

You are NOT required to determine whether the complete claim
element is established.

Evaluate each source independently and preserve useful
technical facts for later verification and claim mapping.


============================================================
CLAIM ELEMENT
============================================================

ID:
{claim_element.id}

TEXT:
{claim_element.text}


============================================================
SOURCE PAGES
============================================================

{chr(10).join(source_sections)}


============================================================
PRIMARY OBJECTIVE
============================================================

For each source, identify concrete technical passages that
may contribute to establishing one or more parts of the
claim element.

Useful evidence may establish:

- a component;
- a structure;
- an operation;
- a function;
- a condition;
- an input;
- an output;
- a technical relationship;
- data flow;
- control flow;
- system interaction;
- sequencing;
- implementation details;
- technical capabilities;
- product behavior.


============================================================
PARTIAL EVIDENCE IS VALID
============================================================

An evidence item does NOT need to establish the complete
claim element.

For example:

A + B + C + D

A source establishing B + C is still useful evidence.

Do NOT reject it because A and D are absent.

The mapper will later combine evidence from multiple passages
and sources.


============================================================
TECHNICAL RELATIONSHIPS
============================================================

Pay special attention to relationships such as:

- receives X from Y;
- sends X to Y;
- routes X through Y;
- determines X based on Y;
- performs X in response to Y;
- identifies X according to Y;
- selects X based on Y;
- stores X in Y;
- writes X to Y;
- reads X from Y;
- controls X using Y;
- communicates with Y;
- traffic entering through X;
- traffic originating from X;
- information received from X;
- data associated with X;
- interaction between components.


Do not focus only on matching nouns.

A passage explaining how components interact can be more
important than a passage merely mentioning the components.


============================================================
TECHNICAL TERMINOLOGY
============================================================

Do not require exact claim terminology.

Accept reasonable technical differences in:

- component names;
- implementation terminology;
- product terminology;
- engineering terminology;
- abbreviations;
- equivalent technical expressions.

Different wording alone is NOT a reason to discard useful
technical evidence.


============================================================
MULTIPLE EVIDENCE ITEMS
============================================================

A source may contain zero, one, or many evidence items.

Return separate evidence items when separate passages
establish different technical facts.

For example:

Evidence 1:
controller functionality.

Evidence 2:
traffic entering through an edge system.

Evidence 3:
identification according to criteria.

Evidence 4:
routing selected traffic.

Do NOT force these into one evidence item.


============================================================
EXCERPT RULE
============================================================

Every excerpt MUST be copied EXACTLY from its corresponding
source content.

Do NOT:

- paraphrase;
- summarize;
- rewrite;
- combine non-contiguous passages;
- invent connecting language;
- change technical terminology.

An excerpt may contain one, two, or three sentences.

Use the shortest contiguous passage that preserves the relevant
technical fact or relationship.


============================================================
EVIDENCE GRANULARITY
============================================================

Prefer excerpts that are:

- technically meaningful;
- specific;
- concise;
- independently understandable.

Avoid:

- entire sections;
- large paragraphs;
- navigation;
- marketing language;
- generic introductions;
- repeated boilerplate.

But do not remove necessary context merely to make an excerpt
shorter.


============================================================
RECALL OVER FINAL JUDGMENT
============================================================

This stage should favor RECALL.

If a passage contains a plausible and technically meaningful
connection to the claim element, preserve it for later
verification.

Do NOT require one passage to prove the complete claim.

Do NOT require every limitation to appear in one excerpt.


============================================================
NO OUTSIDE KNOWLEDGE
============================================================

Use ONLY the provided source content.

Do not introduce facts from:

- general technical knowledge;
- memory;
- target assumptions;
- other sources.

Every extracted technical fact must be grounded in the
corresponding source.


============================================================
EVIDENCE TYPE
============================================================

For each evidence item, "evidence_type" should describe the
nature of the source evidence.

Examples:

"product functionality"

"technical architecture"

"implementation description"

"product documentation"

"technical specification"

"system behavior"

"technical capability"

"network behavior"

"traffic handling"

"controller functionality"

"data flow"

"technical relationship"


Do NOT use verification labels such as:

"direct"

"supportive"

"inferential"

"contextual"

"unsupported"


============================================================
RELEVANCE
============================================================

Explain briefly:

1. what technical fact the excerpt establishes; and
2. which part of the claim element it relates to.

Do not state that the claim element is proven.


============================================================
SOURCE INDEX RULES
============================================================

1. Evaluate every source independently.

2. Preserve the exact source index.

3. Return exactly one result for every source index that
   contains non-empty source content.

4. Do not skip a source index.

5. Do not duplicate a source index.

6. Do not use evidence from one source to support another
   source.

7. Every evidence excerpt must come from the corresponding
   source.


============================================================
OUTPUT
============================================================

Return every meaningful evidence item identified for each
source.

If a source contains no meaningful technical evidence,
return an empty evidence list for that source.

Return only the requested structured output.
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=EvidenceExtractionBatchResult,
        )

        parsed = (
            EvidenceExtractionBatchResult
            .model_validate_json(result)
        )

        # ========================================================
        # INDEX VALIDATION
        # ========================================================

        expected_indexes = {
            index
            for index, (
                _,
                reduced_content,
            ) in enumerate(sources)
            if reduced_content
        }

        actual_indexes = [
            item.source_index
            for item in parsed.results
        ]

        actual_index_set = set(
            actual_indexes
        )

        if actual_index_set != expected_indexes:

            raise ValueError(
                "Evidence extraction batch returned "
                "invalid source indexes."
            )

        if len(actual_indexes) != len(
            expected_indexes
        ):

            raise ValueError(
                "Evidence extraction batch returned "
                "duplicate source indexes."
            )

        results_by_index = {
            item.source_index: item.evidence
            for item in parsed.results
        }

        return [
            results_by_index.get(
                index,
                [],
            )
            if reduced_content
            else []
            for index, (
                _,
                reduced_content,
            ) in enumerate(sources)
        ]
