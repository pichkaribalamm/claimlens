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

Your task is to identify concrete technical evidence from
a publicly available source that may help assess a patent
claim element.

You are an EVIDENCE EXTRACTOR, not the final verifier.

Your job is to find useful passages from the provided source.
Do not decide whether the claim element is ultimately proven.

IMPORTANT RULES:

1. Use ONLY the provided source content.
2. Do not use outside knowledge.
3. Do not invent technical facts.
4. Do not paraphrase the source.
5. Every excerpt MUST be copied exactly from the provided
   source content.
6. Extract only passages that contain meaningful technical
   information relevant to the claim element.
7. Prefer concise evidence-bearing excerpts.
8. Each excerpt should normally contain one to three sentences.
9. Do not return large paragraphs merely because they contain
   relevant words.
10. A single source may contain multiple distinct pieces of
    evidence. Return each meaningful piece separately.
11. Different excerpts may establish different aspects of
    the claim element.
12. Preserve the distinction between separate technical facts.
13. Do not require one excerpt to establish the entire claim
    element.
14. Do not infer facts that are absent from the source.
15. Do not combine information from different parts of the page
    into an excerpt that does not exist verbatim.
16. If the source contains no meaningful technical evidence
    relevant to the claim element, return an empty list.
17. Return only the requested structured output.

For each evidence item:

- "excerpt" must be the exact wording from the provided content.
- "evidence_type" should briefly describe the nature of the
  source evidence, such as:
    "product functionality"
    "technical architecture"
    "implementation description"
    "product documentation"
    "technical specification"
    "system behavior"
    "technical capability"
- "relevance" should briefly explain what technical fact the
  excerpt establishes in relation to the claim element.
- Do not state that the claim element is proven.
- Do not assign a support level such as direct, supportive,
  or inferential. That decision belongs to evidence verification.

CLAIM ELEMENT:

ID:
{claim_element.id}

TEXT:
{claim_element.text}

SOURCE:

Title:
{search_result.title}

URL:
{search_result.url}

RELEVANT PAGE CONTENT:

{reduced_content}
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=EvidenceExtractionResult,
        )

        parsed = EvidenceExtractionResult.model_validate_json(
            result
        )

        return parsed.evidence

    def extract_batch(
        self,
        claim_element: ClaimElement,
        sources: list[tuple[SearchResult, str]],
    ) -> list[list[Evidence]]:

        if not sources:
            return []

        source_sections = []

        for index, (search_result, reduced_content) in enumerate(
            sources
        ):

            if not reduced_content:
                continue

            source_sections.append(
                (
                    f"SOURCE INDEX: {index}\n"
                    f"TITLE: {search_result.title}\n"
                    f"URL: {search_result.url}\n\n"
                    f"RELEVANT PAGE CONTENT:\n"
                    f"{reduced_content}"
                )
            )

        if not source_sections:
            return [[] for _ in sources]

        prompt = f"""
You are a patent evidence extraction assistant.

Your task is to identify concrete technical evidence from
multiple publicly available source pages that may help assess
a patent claim element.

You are an EVIDENCE EXTRACTOR, not the final verifier.

Evaluate each source independently.

IMPORTANT RULES:

1. Use ONLY the content provided for each source.
2. Do not use outside knowledge.
3. Do not invent technical facts.
4. Do not paraphrase the source.
5. Every excerpt MUST be copied exactly from its corresponding
   source content.
6. Extract only passages containing meaningful technical
   information relevant to the claim element.
7. Prefer concise evidence-bearing excerpts.
8. Each excerpt should normally contain one to three sentences.
9. Do not return large paragraphs merely because they contain
   relevant words.
10. A source may contain multiple distinct pieces of evidence.
11. Return separate evidence items when separate passages
    establish different technical facts.
12. Different evidence items may establish different aspects
    of the same claim element.
13. Do not require one excerpt to establish the entire claim
    element.
14. Do not combine text from different passages into one
    excerpt.
15. Do not combine information from different sources into one
    evidence item.
16. Do not infer facts that are absent from the source.
17. If a source contains no meaningful technical evidence
    relevant to the claim element, return an empty evidence
    list for that source.
18. Preserve every source index exactly as provided.
19. Return exactly one result for every source index that
    contains relevant page content.
20. Do not skip a source index.
21. Return only the requested structured output.

For each evidence item:

- "excerpt" must be the exact wording from the corresponding
  source content.
- "evidence_type" should briefly describe the nature of the
  source evidence, such as:
    "product functionality"
    "technical architecture"
    "implementation description"
    "product documentation"
    "technical specification"
    "system behavior"
    "technical capability"
- "relevance" should briefly explain what technical fact the
  excerpt establishes in relation to the claim element.
- Do not state that the claim element is proven.
- Do not assign a support level such as direct, supportive,
  or inferential. That decision belongs to evidence verification.

CLAIM ELEMENT:

ID:
{claim_element.id}

TEXT:
{claim_element.text}

SOURCE PAGES:

{chr(10).join(source_sections)}
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=EvidenceExtractionBatchResult,
        )

        parsed = EvidenceExtractionBatchResult.model_validate_json(
            result
        )

        expected_indexes = {
            index
            for index, (_, reduced_content) in enumerate(sources)
            if reduced_content
        }

        actual_indexes = [
            item.source_index
            for item in parsed.results
        ]

        actual_index_set = set(actual_indexes)

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
            results_by_index.get(index, [])
            if reduced_content
            else []
            for index, (_, reduced_content) in enumerate(
                sources
            )
        ]
