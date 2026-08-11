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

Your task is to examine a patent claim element and
relevant content extracted from a publicly available
source page.

Determine whether the provided content contains
evidence that is relevant to the claim element.

IMPORTANT:

1. Only identify evidence that is actually supported by
   the provided content.
2. Do not rely on outside knowledge.
3. Do not infer facts that are not present in the content.
4. Extract the exact wording from the content that supports
   the finding.
5. Do not paraphrase the excerpt.
6. The excerpt must come directly from the provided content.
7. Evidence should be specific to the claim element.
8. If the content does not contain relevant evidence,
   return an empty list.
9. Return only the requested structured output.

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

Your task is to examine a patent claim element against
multiple relevant source pages.

For each source, determine whether the provided content
contains evidence that is relevant to the claim element.

IMPORTANT:

1. Evaluate each source independently.
2. Only identify evidence that is actually supported by
   the provided source content.
3. Do not rely on outside knowledge.
4. Do not infer facts that are not present in the content.
5. Extract the exact wording from the source content that
   supports the finding.
6. Do not paraphrase the excerpt.
7. Every excerpt must come directly from the corresponding
   source content.
8. Evidence must be specific to the claim element.
9. A source may contain zero, one, or multiple evidence items.
10. If a source does not contain relevant evidence, return
    an empty evidence list for that source.
11. Do not use evidence from one source to support another source.
12. Preserve every source index exactly as provided.
13. Return exactly one result for every source index provided.
14. Do not skip a source index.
15. Return only the requested structured output.

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
            for index, (_, reduced_content) in enumerate(sources)
        ]
