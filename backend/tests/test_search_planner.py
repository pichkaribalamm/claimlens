from unittest.mock import patch

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

    fake_gemini_response = """
    {
        "claim_element_id": "1.1",
        "queries": [
            {
                "query": "Samsung Galaxy S26 Ultra image processor",
                "rationale": "Search for product-specific information about image processing.",
                "priority": 1
            },
            {
                "query": "site:samsung.com Galaxy S26 image signal processing",
                "rationale": "Search Samsung's official sources for image processing information.",
                "priority": 1
            },
            {
                "query": "Galaxy S26 Ultra MIPI CSI camera",
                "rationale": "Search for implementation-level evidence involving the camera interface.",
                "priority": 2
            }
        ],
        "preferred_sources": [
            "Samsung official documentation",
            "Samsung technical publications"
        ],
        "search_strategy": "Prioritize product-specific searches and authoritative Samsung sources while using implementation terminology to investigate image data reception."
    }
    """

    with patch(
        "app.agents.search_planner.GeminiService"
    ) as mock_gemini:

        mock_gemini.return_value.generate.return_value = (
            fake_gemini_response
        )

        planner = SearchPlanner()

        result = planner.plan(
            element,
            target,
            technology_profile
        )

    assert result.claim_element_id == "1.1"

    assert len(result.queries) >= 2

    assert result.queries[0].priority == 1

    assert any(
        "Galaxy S26 Ultra" in query.query
        for query in result.queries
    )

    assert any(
        query.priority == 1
        for query in result.queries
    )

    assert len(result.preferred_sources) > 0

    assert result.search_strategy != ""
