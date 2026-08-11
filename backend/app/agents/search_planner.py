from app.models.schemas import (
    ClaimElement,
    TargetScope,
    TechnologyProfile,
    SearchPlan,
    SearchPlanBatchResult,
)
from app.services.gemini_service import GeminiService


class SearchPlanner:

    def __init__(self):
        self.llm = GeminiService()

    def plan(
        self,
        claim_element: ClaimElement,
        target: TargetScope,
        technology_profile: TechnologyProfile,
    ) -> SearchPlan:

        prompt = f"""
You are a search strategy specialist supporting patent
technical evidence discovery.

Your task is to create a targeted web search plan for
one patent claim element and a specified target.

The objective is to discover publicly available technical
evidence that may later support analysis of the claim element.

IMPORTANT RULES:

1. Generate multiple complementary search queries.
2. Do not perform the searches yourself.
3. Do not determine whether the target practices the claim.
4. Do not make unsupported claims about the target.
5. Use the target company, product, and technology when
   available.
6. Use the technical concepts and alternative terminology
   from the technology profile.
7. Include both product-focused and implementation-focused
   searches where appropriate.
8. Prefer authoritative sources such as:
   - manufacturer documentation
   - manufacturer technical pages
   - chipset/component manufacturer documentation
   - regulatory filings
   - standards organizations
   - developer documentation
   - reputable technical publications
9. Use site-restricted queries when a particular authoritative
   source is especially relevant.
10. Do not assume or assert target-specific facts that are not
    explicitly provided in the input.
11. Treat items from the technology profile such as likely
    components or implementation approaches as hypotheses for
    search generation, not as established facts about the target.
12. If a possible target architecture, chipset, component,
    or implementation is not established by the input, do not
    present it as confirmed in the search strategy.
13. Avoid overly broad queries that are likely to produce
    large numbers of irrelevant results.
14. Each query must have a clear rationale.
15. Assign priority from 1 to 5, where 1 is highest priority.
16. Return only the requested structured output.

CLAIM ELEMENT

ID:
{claim_element.id}

TEXT:
{claim_element.text}

TARGET

Company:
{target.company}

Product:
{target.product}

Technology:
{target.technology}

TECHNOLOGY PROFILE

Core concept:
{technology_profile.core_concept}

Technical concepts:
{technology_profile.technical_concepts}

Alternative terminology:
{technology_profile.alternative_terminology}

Likely components:
{technology_profile.likely_components}

Implementation hypotheses:
{technology_profile.implementation_hypotheses}
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=SearchPlan,
        )

        return SearchPlan.model_validate_json(result)

    def plan_batch(
        self,
        claim_elements: list[ClaimElement],
        target: TargetScope,
        technology_profiles: list[TechnologyProfile],
    ) -> list[SearchPlan]:

        if not claim_elements:
            return []

        expected_element_ids = {
            element.id
            for element in claim_elements
        }

        profile_ids = {
            profile.claim_element_id
            for profile in technology_profiles
        }

        if profile_ids != expected_element_ids:
            raise ValueError(
                "Technology profiles do not match claim element IDs."
            )

        if len(technology_profiles) != len(claim_elements):
            raise ValueError(
                "Technology profiles do not match claim element IDs."
            )

        profiles_by_id = {
            profile.claim_element_id: profile
            for profile in technology_profiles
        }

        element_sections = []

        for element in claim_elements:

            profile = profiles_by_id[element.id]

            element_sections.append(
                f"""
CLAIM ELEMENT ID:
{element.id}

CLAIM ELEMENT TEXT:
{element.text}

TECHNOLOGY PROFILE:

Core concept:
{profile.core_concept}

Technical concepts:
{profile.technical_concepts}

Alternative terminology:
{profile.alternative_terminology}

Likely components:
{profile.likely_components}

Implementation hypotheses:
{profile.implementation_hypotheses}
""".strip()
            )

        prompt = f"""
You are a search strategy specialist supporting patent
technical evidence discovery.

Your task is to create targeted web search plans for
multiple patent claim elements and a specified target.

You must create one independent search plan for every
claim element provided.

The objective is to discover publicly available technical
evidence that may later support analysis of each claim element.

IMPORTANT RULES:

1. Analyze each claim element independently.
2. Preserve the exact claim element ID in its corresponding
   search plan.
3. Generate multiple complementary search queries for each
   claim element.
4. Do not perform the searches yourself.
5. Do not determine whether the target practices any claim.
6. Do not make unsupported claims about the target.
7. Use the target company, product, and technology when
   available.
8. Use the technical concepts and alternative terminology
   from the corresponding technology profile.
9. Include both product-focused and implementation-focused
   searches where appropriate.
10. Prefer authoritative sources such as:
    - manufacturer documentation
    - manufacturer technical pages
    - chipset/component manufacturer documentation
    - regulatory filings
    - standards organizations
    - developer documentation
    - reputable technical publications
11. Use site-restricted queries when a particular authoritative
    source is especially relevant.
12. Do not assume or assert target-specific facts that are not
    explicitly provided in the input.
13. Treat likely components and implementation hypotheses as
    hypotheses for search generation, not as established facts.
14. Avoid overly broad queries that are likely to produce
    large numbers of irrelevant results.
15. Each query must have a clear rationale.
16. Assign priority from 1 to 5, where 1 is highest priority.
17. Return exactly one search plan for every claim element.
18. Do not omit any claim element.
19. Do not create search plans for claim element IDs that were
    not provided.
20. Return only the requested structured output.

TARGET

Company:
{target.company}

Product:
{target.product}

Technology:
{target.technology}

CLAIM ELEMENTS AND TECHNOLOGY PROFILES:

{chr(10).join(element_sections)}
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=SearchPlanBatchResult,
        )

        parsed = SearchPlanBatchResult.model_validate_json(
            result
        )

        actual_ids = [
            plan.claim_element_id
            for plan in parsed.results
        ]

        actual_id_set = set(actual_ids)

        if actual_id_set != expected_element_ids:
            raise ValueError(
                "Search plan batch returned "
                "invalid claim element IDs."
            )

        if len(actual_ids) != len(expected_element_ids):
            raise ValueError(
                "Search plan batch returned "
                "duplicate claim element IDs."
            )

        plans_by_id = {
            plan.claim_element_id: plan
            for plan in parsed.results
        }

        return [
            plans_by_id[element.id]
            for element in claim_elements
        ]
