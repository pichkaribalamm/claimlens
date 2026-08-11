from app.models.schemas import (
    ClaimElement,
    TargetScope,
    TechnologyProfile,
    TechnologyProfileBatchResult,
)
from app.services.gemini_service import GeminiService


class TechnologyProfiler:

    def __init__(self):
        self.llm = GeminiService()

    def profile(
        self,
        claim_element: ClaimElement,
        target: TargetScope,
    ) -> TechnologyProfile:

        prompt = f"""
You are a technical research assistant supporting patent
evidence discovery.

Your task is to analyze a patent claim element in the
context of a specific target technology.

IMPORTANT:

1. Identify the core technical concept represented by
   the claim element.
2. Identify related technical concepts that could be
   relevant when researching the target.
3. Identify alternative terminology that manufacturers,
   engineers, technical documentation, or reviewers might
   use to describe the same or closely related concept.
4. Identify generic hardware, software, or system components
   that are commonly associated with implementing the claimed
   functionality. Do not assume that these components are
   present in the target.
5. Identify possible target-specific implementation hypotheses
   that could be investigated later. These are hypotheses only
   and must not be presented as established facts about the
   target.
6. Do not search the web.
7. Do not determine whether the target actually practices
   the claim.
8. Do not invent target-specific facts.
9. Keep the analysis technically grounded in the claim
   element itself.
10. Return only the requested structured output.

CLAIM ELEMENT:

ID:
{claim_element.id}

TEXT:
{claim_element.text}

TARGET SCOPE:

Company:
{target.company}

Product:
{target.product}

Technology:
{target.technology}
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=TechnologyProfile,
        )

        return TechnologyProfile.model_validate_json(
            result
        )

    def profile_batch(
        self,
        claim_elements: list[ClaimElement],
        target: TargetScope,
    ) -> list[TechnologyProfile]:

        if not claim_elements:
            return []

        element_sections = []

        for element in claim_elements:

            element_sections.append(
                f"""
CLAIM ELEMENT ID:
{element.id}

CLAIM ELEMENT TEXT:
{element.text}
""".strip()
            )

        prompt = f"""
You are a technical research assistant supporting patent
evidence discovery.

Your task is to analyze multiple patent claim elements in
the context of a specific target technology.

You must produce one technology profile for every claim
element provided.

IMPORTANT:

1. Analyze each claim element independently.
2. Preserve the exact claim element ID in its corresponding
   technology profile.
3. Identify the core technical concept represented by
   each claim element.
4. Identify related technical concepts that could be
   relevant when researching the target.
5. Identify alternative terminology that manufacturers,
   engineers, technical documentation, or reviewers might
   use to describe the same or closely related concept.
6. Identify generic hardware, software, or system components
   that are commonly associated with implementing the claimed
   functionality. Do not assume that these components are
   present in the target.
7. Identify possible target-specific implementation hypotheses
   that could be investigated later. These are hypotheses only
   and must not be presented as established facts about the
   target.
8. Do not search the web.
9. Do not determine whether the target actually practices
   any claim element.
10. Do not invent target-specific facts.
11. Keep each analysis technically grounded in its
    corresponding claim element.
12. Return exactly one technology profile for every claim
    element provided.
13. Do not omit any claim element.
14. Do not create profiles for claim element IDs that were
    not provided.
15. Return only the requested structured output.

TARGET SCOPE:

Company:
{target.company}

Product:
{target.product}

Technology:
{target.technology}

CLAIM ELEMENTS:

{chr(10).join(element_sections)}
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=TechnologyProfileBatchResult,
        )

        parsed = TechnologyProfileBatchResult.model_validate_json(
            result
        )

        expected_ids = [
            element.id
            for element in claim_elements
        ]

        expected_id_set = set(expected_ids)

        actual_ids = [
            profile.claim_element_id
            for profile in parsed.results
        ]

        actual_id_set = set(actual_ids)

        if actual_id_set != expected_id_set:
            raise ValueError(
                "Technology profile batch returned "
                "invalid claim element IDs."
            )

        if len(actual_ids) != len(expected_ids):
            raise ValueError(
                "Technology profile batch returned "
                "duplicate claim element IDs."
            )

        profiles_by_id = {
            profile.claim_element_id: profile
            for profile in parsed.results
        }

        return [
            profiles_by_id[element.id]
            for element in claim_elements
        ]
