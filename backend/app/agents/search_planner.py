from app.models.schemas import (
    ClaimElement,
    TargetScope,
    TechnologyProfile,
    SearchPlan,
)


class SearchPlanner:

    def plan(
        self,
        claim_element: ClaimElement,
        target: TargetScope,
        technology_profile: TechnologyProfile,
    ) -> SearchPlan:
        """
        Create a search plan for a claim element and target.

        AI-powered search planning will be added in the next step.
        """

        return SearchPlan(
            claim_element_id=claim_element.id,
            queries=[],
            preferred_sources=[],
            search_strategy=""
        )
