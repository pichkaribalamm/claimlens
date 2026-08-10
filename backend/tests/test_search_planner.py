from app.agents.search_planner import SearchPlanner
from app.models.schemas import (
    ClaimElement,
    TargetScope,
    TechnologyProfile,
)


def test_search_planner():

    element = ClaimElement(
        id="1.1",
        claim_number="1",
        text="a processor configured to receive image data"
    )

    target = TargetScope(
        company="Samsung",
        product="Galaxy S26 Ultra"
    )

    technology_profile = TechnologyProfile(
        claim_element_id="1.1",
        target=target,
        core_concept="Processor reception of image data",
        technical_concepts=[
            "Image Signal Processing",
            "MIPI CSI"
        ],
        alternative_terminology=[
            "ISP",
            "Image Processor"
        ],
        likely_components=[
            "Image Signal Processor",
            "Camera Interface"
        ],

            implementation_hypotheses=[
        "The target may use a dedicated ISP",
        "The target may receive camera data through MIPI CSI"
    ]
    )

    planner = SearchPlanner()

    result = planner.plan(
        element,
        target,
        technology_profile
    )

    assert result.claim_element_id == "1.1"
    assert len(result.queries) == 2

    assert result.queries[0].query == (
    "Samsung Galaxy S26 Ultra image processor"
)

    assert result.queries[0].priority == 1

    assert "Samsung official documentation" in (
    result.preferred_sources
)

    assert "product-specific" in result.search_strategy
