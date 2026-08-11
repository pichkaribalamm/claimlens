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
    # SINGLE SOURCE
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
You are a high-recall technical evidence extraction assistant
supporting patent claim analysis.

Your task is to identify useful technical passages from a
publicly available source that may help assess a patent claim
element.

You are an EVIDENCE EXTRACTOR.

You are NOT the final verifier.

Your job is to collect technically useful evidence.

Do NOT decide whether the claim element is proven.


============================================================
CORE PRINCIPLE
============================================================

Prefer RECALL over premature rejection.

If a passage contains a concrete technical fact that is
meaningfully related to any part of the claim element, it may
be useful evidence and should generally be extracted.

The passage does NOT need to establish the complete claim
element.

A later verification and mapping stage will determine:

- how directly it supports the claim;
- whether terminology is technically equivalent;
- whether an inference is reasonable;
- whether multiple evidence items collectively support the
  element.


============================================================
USE ONLY THE PROVIDED SOURCE
============================================================

1. Use ONLY the provided source content.

2. Do not use outside knowledge to add facts.

3. Do not invent technical details.

4. Do not assume that the source says something merely because
   it would be technically reasonable.

5. Do not use the claim itself as evidence.

6. Do not use information from another source.


============================================================
WHAT TO EXTRACT
============================================================

Extract passages that contain concrete technical information
related to the claim element.

Useful evidence may include:

- explicit product functionality;
- technical behavior;
- system architecture;
- component functionality;
- communication behavior;
- data flow;
- control flow;
- configuration;
- interfaces;
- protocols;
- implementation details;
- technical capabilities;
- system relationships;
- input/output behavior;
- operating conditions;
- technical specifications.

A passage may be useful even if it establishes only ONE PART
of the claim element.


============================================================
PARTIAL EVIDENCE IS VALID
============================================================

Do NOT require an excerpt to establish the entire claim element.

For example, if a claim element contains:

1. a controller;
2. receiving information;
3. determining a condition based on the information; and
4. performing an action in response,

then different source passages may establish different parts.

Extract those passages separately when they are technically
useful.

Do NOT reject a useful passage merely because it does not contain
every limitation.


============================================================
TECHNICAL EQUIVALENCE
============================================================

Do NOT decide whether two terms are equivalent.

For example, if the claim says:

"route traffic"

and the source says:

"traffic steering"

the extractor should still consider the passage for extraction
if the passage contains concrete technical information about the
traffic-handling operation.

The verifier will later decide how strongly that terminology
corresponds to the claim.


============================================================
CLAIM RELATIONSHIPS
============================================================

Preserve technical relationships when they appear in the source.

Pay attention to:

- receives X from Y;
- sends X to Y;
- routes X through Y;
- determines X based on Y;
- performs X in response to Y;
- connects X to Y;
- configures X to perform Y;
- stores X in Y;
- writes X to Y;
- reads X from Y;
- communicates with Y;
- controls Y.

A passage containing such a relationship is particularly useful.


============================================================
EXCERPT REQUIREMENTS
============================================================

Every excerpt MUST:

1. come directly from the provided source content;

2. be copied exactly;

3. preserve the original wording;

4. contain enough surrounding context to understand the
   technical fact;

5. normally contain one to three sentences.

Do NOT paraphrase.

Do NOT rewrite.

Do NOT combine separate passages into a new sentence.

Do NOT create an excerpt that does not exist verbatim.


============================================================
EXCERPT LENGTH
============================================================

Prefer concise evidence-bearing passages.

Normally use one to three sentences.

A fourth sentence is acceptable only when necessary to preserve
the technical meaning or relationship.

Do NOT return entire paragraphs simply because one sentence
contains a relevant word.

Do NOT return large blocks of page content.


============================================================
MULTIPLE EVIDENCE ITEMS
============================================================

A source may contain multiple useful passages.

Return separate evidence items when different passages establish
different technical facts.

For example:

Evidence 1:
describes the controller receiving information.

Evidence 2:
describes the controller determining a condition.

Evidence 3:
describes the resulting routing behavior.

Do not merge those passages into one invented excerpt.


============================================================
DO NOT OVER-EXTRACT
============================================================

Do not extract passages merely because they contain:

- generic technology names;
- generic product names;
- broad marketing language;
- unrelated background information;
- generic descriptions of the technology;
- isolated claim terminology without technical substance.

The passage should contain an actual technical fact that could
reasonably contribute to later assessment.


============================================================
EVIDENCE TYPE
============================================================

"evidence_type" describes the TYPE OF SOURCE EVIDENCE.

Use concise categories such as:

- product functionality
- technical architecture
- implementation description
- product documentation
- technical specification
- system behavior
- technical capability
- component functionality
- interface description
- protocol behavior
- configuration
- data flow
- control flow

Do NOT use:

- direct
- supportive
- inferential
- contextual
- unsupported

Those are support classifications and belong to the verification
stage.


============================================================
RELEVANCE
============================================================

"relevance" should briefly explain:

1. what technical fact the excerpt contains; and
2. which aspect of the claim element that fact may help assess.

Keep this concise.

Do NOT say:

"this proves the claim."

Instead say something like:

"This passage describes traffic being directed through an edge
routing function, which may be relevant to the claimed routing
operation."


============================================================
NO FINAL JUDGMENT
============================================================

Do NOT:

- determine whether the claim element is supported;
- assign a support level;
- assign direct/supportive/inferential status;
- decide technical equivalence;
- perform infringement analysis;
- determine whether the target practices the claim.


============================================================
EMPTY RESULT
============================================================

Return an empty evidence list only when the provided source
content does not contain a concrete technical fact that could
reasonably contribute to assessing the claim element.

Do NOT return an empty list merely because:

- the passage does not establish the entire element;
- the source uses different terminology;
- the relationship is only one part of the element;
- another evidence item would be needed to establish the rest.


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

Title:
{search_result.title}

URL:
{search_result.url}


============================================================
SOURCE CONTENT
============================================================

{reduced_content}


Return only the requested structured output.
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=EvidenceExtractionResult,
        )

        parsed = EvidenceExtractionResult.model_validate_json(
            result
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
                    f"SOURCE CONTENT:\n"
                    f"{reduced_content}"
                )
            )

        if not source_sections:
            return [
                []
                for _ in sources
            ]

        prompt = f"""
You are a high-recall technical evidence extraction assistant
supporting patent claim analysis.

Your task is to identify useful technical passages from MULTIPLE
publicly available sources that may help assess a patent claim
element.

You are an EVIDENCE EXTRACTOR.

You are NOT the final verifier.

Your job is to collect technically useful evidence.

Do NOT decide whether the claim element is proven.


============================================================
CORE PRINCIPLE
============================================================

Prefer RECALL over premature rejection.

If a source passage contains a concrete technical fact that is
meaningfully related to any part of the claim element, it may be
useful evidence.

The passage does NOT need to establish the complete claim
element.

Later verification and claim mapping will determine:

- how directly it supports the claim;
- whether terminology is technically equivalent;
- whether an inference is reasonable;
- whether multiple evidence items collectively support the
  element.


============================================================
SOURCE INDEPENDENCE
============================================================

Evaluate each source independently.

Use ONLY the content provided under that source's index.

Never use information from one source to create evidence for
another source.

Never combine text from multiple sources into one excerpt.


============================================================
WHAT TO EXTRACT
============================================================

Extract passages containing concrete technical information
related to the claim element.

Useful evidence may include:

- product functionality;
- technical behavior;
- architecture;
- component functionality;
- data flow;
- control flow;
- communication behavior;
- configuration;
- interface behavior;
- protocol behavior;
- implementation details;
- technical capabilities;
- technical specifications;
- system relationships;
- input/output behavior;
- operating conditions.


============================================================
PARTIAL EVIDENCE
============================================================

A source does NOT need to establish the complete claim element.

Different evidence items may establish different parts.

For example, if an element contains:

- receiving information;
- determining a condition based on the information; and
- performing an operation in response,

then a source describing only the receiving operation can still
be useful evidence.

Extract it.

Do not reject it merely because it does not establish the other
limitations.


============================================================
TECHNICAL TERMINOLOGY
============================================================

Do NOT decide whether source terminology is technically
equivalent to the claim terminology.

If a source uses different but technically relevant terminology,
the passage may still be extracted.

The verification stage will determine the strength of the
correspondence.


============================================================
TECHNICAL RELATIONSHIPS
============================================================

Preserve relationships contained in the source.

Pay particular attention to:

- receives X from Y;
- sends X to Y;
- routes X through Y;
- determines X based on Y;
- performs X in response to Y;
- connects X to Y;
- configures X to perform Y;
- stores X in Y;
- writes X to Y;
- reads X from Y;
- communicates with Y;
- controls Y.


============================================================
EXCERPT REQUIREMENTS
============================================================

Every excerpt MUST:

1. come directly from its corresponding source content;

2. be copied exactly;

3. preserve the source wording;

4. contain enough context to understand the technical fact;

5. normally contain one to three sentences.

A fourth sentence is acceptable only when necessary to preserve
technical meaning.

Do NOT paraphrase.

Do NOT combine separate passages.

Do NOT invent excerpts.


============================================================
MULTIPLE EVIDENCE ITEMS PER SOURCE
============================================================

A source may contain multiple useful passages.

Return separate evidence items when separate passages establish
different technical facts.

For example:

Evidence 1:
controller receives information.

Evidence 2:
controller determines a condition.

Evidence 3:
system performs a routing operation.

Do not combine those passages unless the exact combined wording
exists in the source.


============================================================
DO NOT OVER-EXTRACT
============================================================

Do not extract passages merely because they contain a relevant
word.

Avoid:

- generic technology descriptions;
- marketing statements without technical substance;
- unrelated background information;
- isolated terminology;
- generic product descriptions with no technical fact.


============================================================
EVIDENCE TYPE
============================================================

"evidence_type" describes the TYPE OF SOURCE EVIDENCE.

Use concise categories such as:

- product functionality
- technical architecture
- implementation description
- product documentation
- technical specification
- system behavior
- technical capability
- component functionality
- interface description
- protocol behavior
- configuration
- data flow
- control flow

Do NOT use:

- direct
- supportive
- inferential
- contextual
- unsupported

Those classifications belong to evidence verification.


============================================================
RELEVANCE
============================================================

"relevance" should briefly state:

1. what technical fact the excerpt contains; and
2. what aspect of the claim element it may help assess.

Keep the explanation concise.

Do NOT state that the claim is proven.


============================================================
NO FINAL JUDGMENT
============================================================

Do NOT:

- determine whether the claim element is supported;
- assign support levels;
- determine technical equivalence;
- perform infringement analysis;
- determine whether the target practices the claim.


============================================================
EMPTY RESULTS
============================================================

Return an empty evidence list for a source only when that source
does not contain a concrete technical fact that could reasonably
contribute to assessing the claim element.

Do NOT reject a source merely because its evidence is:

- partial;
- expressed using different terminology;
- only one part of the claim element;
- insufficient by itself.


============================================================
OUTPUT REQUIREMENTS
============================================================

1. Evaluate every source independently.

2. Preserve every source index.

3. Return exactly one result for every source index that has
   non-empty source content.

4. Do not skip a source index.

5. A source may return zero, one, or multiple evidence items.

6. Do not create evidence for a source index that was not
   provided.

7. Return only the requested structured output.


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
