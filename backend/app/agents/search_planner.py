from app.models.schemas import (
    ClaimElement,
    TargetScope,
    TechnologyProfile,
    SearchPlan,
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
