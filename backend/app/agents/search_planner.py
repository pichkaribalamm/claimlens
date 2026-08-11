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

1. Analyze the claim element itself before considering
   implementation hypotheses.

2. Generate multiple complementary search queries.

3. The search plan must contain THREE search layers:

   Layer 1 — Direct claim-substance searches:
   Search the core technical relationship and limitations
   expressed directly in the claim element.

   Layer 2 — Terminology and concept searches:
   Search alternative terminology and closely related
   technical concepts from the technology profile that
   could describe the same claimed functionality.

   Layer 3 — Implementation-hypothesis searches:
   Search possible implementation approaches only as
   secondary investigative paths.

4. Prioritize Layer 1 over Layer 2, and Layer 2 over Layer 3.

5. Do not let an implementation hypothesis replace the
   actual claim language or core technical concept.

6. At least one high-priority query should remain close to
   the technical substance of the claim element.

7. Use the target company, product, and technology when
   available.

8. Use technical concepts and alternative terminology from
   the technology profile.

9. Implementation hypotheses are investigative possibilities
   only. They are not established facts about the target.

10. Do not assume that a likely component, protocol,
    architecture, interface, or implementation hypothesis
    exists in the target.

11. Do not introduce specific technologies, protocols,
    architectures, components, interfaces, or standards
    that are not present in the claim element or technology
    profile merely because they are commonly associated
    with the technology.

12. If an implementation hypothesis is used in a query,
    the rationale must make clear that it is an investigative
    hypothesis rather than a confirmed target characteristic.

13. Do not perform the searches yourself.

14. Do not determine whether the target practices the claim.

15. Do not make unsupported claims about the target.

16. Prefer authoritative sources such as:
    - manufacturer documentation
    - manufacturer technical pages
    - chipset/component manufacturer documentation
    - regulatory filings
    - standards organizations
    - developer documentation
    - reputable technical publications

17. Use site-restricted queries when a particular authoritative
    source is especially relevant.

18. Avoid overly broad queries that are likely to produce
    large numbers of irrelevant results.

19. Avoid queries that are so implementation-specific that
    they could miss evidence describing the same functionality
    using different terminology.

20. Each query must have a clear rationale.

21. Assign priority from 1 to 5, where 1 is highest priority.

22. Return only the requested structured output.

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

4. For every claim element, use THREE search layers:

   Layer 1 — Direct claim-substance searches:
   Search the core technical relationship and limitations
   expressed directly in the claim element.

   Layer 2 — Terminology and concept searches:
   Search alternative terminology and closely related
   technical concepts from the corresponding technology
   profile that could describe the same claimed functionality.

   Layer 3 — Implementation-hypothesis searches:
   Search possible implementation approaches only as
   secondary investigative paths.

5. Prioritize Layer 1 over Layer 2, and Layer 2 over Layer 3.

6. At least one high-priority query for every claim element
   should remain close to the technical substance of that
   claim element.

7. Do not let an implementation hypothesis replace the
   actual claim language or core technical concept.

8. Use the target company, product, and technology when
   available.

9. Use technical concepts and alternative terminology from
   the corresponding technology profile.

10. Treat likely components and implementation hypotheses
    as investigative possibilities only.

11. Do not assume that a likely component, protocol,
    architecture, interface, or implementation hypothesis
    exists in the target.

12. Do not introduce specific technologies, protocols,
    architectures, components, interfaces, or standards
    that are not present in the claim element or technology
    profile merely because they are commonly associated
    with the technology.

13. If an implementation hypothesis is used in a query,
    its rationale must make clear that it is an investigative
    hypothesis rather than a confirmed target characteristic.

14. Do not perform the searches yourself.

15. Do not determine whether the target practices any claim.

16. Do not make unsupported claims about the target.

17. Prefer authoritative sources such as:
    - manufacturer documentation
    - manufacturer technical pages
    - chipset/component manufacturer documentation
    - regulatory filings
    - standards organizations
    - developer documentation
    - reputable technical publications

18. Use site-restricted queries when a particular authoritative
    source is especially relevant.

19. Avoid overly broad queries that are likely to produce
    large numbers of irrelevant results.

20. Avoid queries that are so implementation-specific that
    they could miss evidence describing the same functionality
    using different terminology.

21. Each query must have a clear rationale.

22. Assign priority from 1 to 5, where 1 is highest priority.

23. Return exactly one search plan for every claim element.

24. Do not omit any claim element.

25. Do not create search plans for claim element IDs that were
    not provided.

26. Return only the requested structured output.

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
