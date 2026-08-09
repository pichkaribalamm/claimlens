from app.models.schemas import ClaimElement, TargetScope


class TechnologyProfiler:

    def profile(
        self,
        claim_element: ClaimElement,
        target: TargetScope,
    ):
        """
        Build a technology profile for a claim element
        in the context of a target scope.

        AI reasoning will be added in the next step.
        """

        return {
            "claim_element_id": claim_element.id,
            "claim_element": claim_element.text,
            "target": target.model_dump(),
        }
