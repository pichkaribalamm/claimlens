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

1. First analyze the actual technical substance and
   limitations expressed in the claim element.

2. Generate multiple complementary search queries.

3. The search plan must use the following priority structure:

   PRIORITY 1 — DIRECT CLAIM-SUBSTANCE SEARCH

   At least one query MUST have priority 1.

   A priority-1 query must search for the actual technical
   relationship, action, structure, condition, or limitation
   expressed in the claim element.

   It should remain close to the claim's technical substance,
   while using natural technical terminology where appropriate.

   Do NOT replace the claimed functionality with a presumed
   implementation.

   Example:
   If the claim describes a controller receiving information
   about incoming network traffic, search for concepts such as
   a controller receiving traffic information, ingress traffic
   information, or a network edge system reporting traffic
   information.

4. PRIORITY 2 — TERMINOLOGY / CONCEPT SEARCH

   At least one query MUST have priority 2.

   A priority-2 query should use alternative terminology or
   closely related technical concepts from the technology
   profile that could describe the SAME claimed functionality.

   Priority 2 may broaden terminology, but must still remain
   technically connected to the claim element.

5. PRIORITY 3–5 — IMPLEMENTATION-HYPOTHESIS SEARCHES

   Queries involving possible implementation approaches,
   architectures, protocols, interfaces, components, or
   technologies must normally have priority 3, 4, or 5.

   These searches are secondary investigative paths.

6. NEVER assign priority 1 or priority 2 to a query whose
   primary basis is an unconfirmed implementation hypothesis.

7. An implementation hypothesis must never replace the actual
   claim language or core technical relationship.

8. Do not assume that a likely component, protocol,
   architecture, interface, standard, or implementation
   exists in the target.

9. Do not introduce specific technologies, protocols,
   architectures, components, interfaces, or standards merely
   because they are commonly associated with the technology.

10. If an implementation hypothesis is used in a query,
    the rationale must clearly identify it as an investigative
    possibility rather than a confirmed characteristic of
    the target.

11. Use the target company, product, and technology when
    available.

12. Use technical concepts and alternative terminology from
    the technology profile.

13. Prefer authoritative sources such as:
    - manufacturer documentation
    - manufacturer technical pages
    - chipset/component manufacturer documentation
    - regulatory filings
    - standards organizations
    - developer documentation
    - reputable technical publications

14. Use site-restricted queries when a particular authoritative
    source is especially relevant.

15. Avoid overly broad queries that are likely to produce
    large numbers of irrelevant results.

16. Avoid queries that are so implementation-specific that
    they could miss evidence describing the same functionality
    using different terminology.

17. Do not perform the searches yourself.

18. Do not determine whether the target practices the claim.

19. Do not make unsupported claims about the target.

20. Each query must have a clear rationale.

21. Assign priority from 1 to 5, where 1 is highest priority.

22. The final output MUST contain:
    - at least one priority-1 query
    - at least one priority-2 query
    - zero priority-1 queries based primarily on implementation
      hypotheses
    - zero priority-2 queries based primarily on implementation
      hypotheses

23. Return only the requested structured output.

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

        parsed = SearchPlan.model_validate_json(result)

        priorities = [
            query.priority
            for query in parsed.queries
        ]

        if 1 not in priorities:
            raise ValueError(
                "Search plan must contain at least one "
                "priority-1 query."
            )

        if 2 not in priorities:
            raise ValueError(
                "Search plan must contain at least one "
                "priority-2 query."
            )

        return parsed

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

3. Generate multiple complementary search queries for
   every claim element.

4. Every claim element MUST use the following priority
   structure:

   PRIORITY 1 — DIRECT CLAIM-SUBSTANCE SEARCH

   Every claim element MUST have at least one priority-1
   query.

   The priority-1 query must search the actual technical
   relationship, action, structure, condition, or limitation
   expressed in that claim element.

   Keep the query close to the claim's technical substance.

   Do not replace the claimed functionality with a presumed
   implementation.

5. PRIORITY 2 — TERMINOLOGY / CONCEPT SEARCH

   Every claim element MUST have at least one priority-2
   query.

   The priority-2 query should use alternative terminology
   or closely related technical concepts from the corresponding
   technology profile that could describe the same claimed
   functionality.

6. PRIORITY 3–5 — IMPLEMENTATION-HYPOTHESIS SEARCHES

   Queries involving possible implementation approaches,
   architectures, protocols, interfaces, components, or
   technologies must normally have priority 3, 4, or 5.

   These are secondary investigative paths only.

7. NEVER assign priority 1 or priority 2 to a query whose
   primary basis is an unconfirmed implementation hypothesis.

8. Do not allow an implementation hypothesis to replace
   the actual claim language or core technical relationship.

9. Do not assume that a likely component, protocol,
   architecture, interface, standard, or implementation
   exists in the target.

10. Do not introduce specific technologies, protocols,
    architectures, components, interfaces, or standards
    merely because they are commonly associated with the
    technology.

11. If an implementation hypothesis is used in a query,
    the rationale must clearly identify it as an investigative
    possibility rather than a confirmed characteristic of
    the target.

12. Use the target company, product, and technology when
    available.

13. Use technical concepts and alternative terminology from
    the corresponding technology profile.

14. Prefer authoritative sources such as:
    - manufacturer documentation
    - manufacturer technical pages
    - chipset/component manufacturer documentation
    - regulatory filings
    - standards organizations
    - developer documentation
    - reputable technical publications

15. Use site-restricted queries when a particular authoritative
    source is especially relevant.

16. Avoid overly broad queries that are likely to produce
    large numbers of irrelevant results.

17. Avoid queries that are so implementation-specific that
    they could miss evidence describing the same functionality
    using different terminology.

18. Do not perform the searches yourself.

19. Do not determine whether the target practices any claim.

20. Do not make unsupported claims about the target.

21. Each query must have a clear rationale.

22. Assign priority from 1 to 5, where 1 is highest priority.

23. For EVERY claim element, the output MUST contain:
    - at least one priority-1 query
    - at least one priority-2 query
    - implementation-hypothesis queries, if any, at priority
      3 or lower

24. Do not omit any claim element.

25. Do not create search plans for claim element IDs that
    were not provided.

26. Return exactly one search plan for every claim element.

27. Return only the requested structured output.

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

        for plan in parsed.results:

            priorities = [
                query.priority
                for query in plan.queries
            ]

            if 1 not in priorities:
                raise ValueError(
                    f"Search plan for claim element "
                    f"{plan.claim_element_id} must contain "
                    "at least one priority-1 query."
                )

            if 2 not in priorities:
                raise ValueError(
                    f"Search plan for claim element "
                    f"{plan.claim_element_id} must contain "
                    "at least one priority-2 query."
                )

        plans_by_id = {
            plan.claim_element_id: plan
            for plan in parsed.results
        }

        return [
            plans_by_id[element.id]
            for element in claim_elements
        ]
