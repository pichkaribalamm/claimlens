from app.models.schemas import (
    ClaimElement,
    TargetScope,
    TechnologyProfile,
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

        return TechnologyProfile.model_validate_json(result)
