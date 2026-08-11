from unittest.mock import patch

import pytest

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
        text="a processor configured to receive image data",
    )

    target = TargetScope(
        company="Samsung",
        product="Galaxy S26 Ultra",
    )

    technology_profile = TechnologyProfile(
        claim_element_id="1.1",
        target=target,
        core_concept="Processor reception of image data",
        technical_concepts=[
            "Image Signal Processing",
            "MIPI CSI",
        ],
        alternative_terminology=[
            "ISP",
            "Image Processor",
        ],
        likely_components=[
            "Image Signal Processor",
            "Camera Interface",
        ],
        implementation_hypotheses=[
            "The target may use a dedicated ISP",
            "The target may receive camera data through MIPI CSI",
        ],
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
            technology_profile,
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

    mock_gemini.return_value.generate.assert_called_once()


def test_search_planner_batch_without_elements():

    target = TargetScope(
        company="Samsung",
        product="Galaxy S26 Ultra",
    )

    with patch(
        "app.agents.search_planner.GeminiService"
    ) as mock_gemini:

        planner = SearchPlanner()

        result = planner.plan_batch(
            [],
            target,
            [],
        )

    assert result == []

    mock_gemini.return_value.generate.assert_not_called()


def test_search_planner_batch_multiple_elements():

    elements = [
        ClaimElement(
            id="1.1",
            claim_number="1",
            text="a processor configured to receive image data",
        ),
        ClaimElement(
            id="1.2",
            claim_number="1",
            text="a memory configured to store processed image data",
        ),
    ]

    target = TargetScope(
        company="Samsung",
        product="Galaxy S26 Ultra",
    )

    technology_profiles = [
        TechnologyProfile(
            claim_element_id="1.1",
            target=target,
            core_concept="Processor reception of image data",
            technical_concepts=[
                "Image Signal Processing",
                "MIPI CSI",
            ],
            alternative_terminology=[
                "ISP",
                "Image Processor",
            ],
            likely_components=[
                "Image Signal Processor",
                "Camera Interface",
            ],
            implementation_hypotheses=[
                "The target may use a dedicated ISP",
            ],
        ),
        TechnologyProfile(
            claim_element_id="1.2",
            target=target,
            core_concept="Storage of processed image data",
            technical_concepts=[
                "Image data storage",
                "Memory controller",
            ],
            alternative_terminology=[
                "Image buffer",
                "Frame buffer",
            ],
            likely_components=[
                "Memory",
                "Memory controller",
            ],
            implementation_hypotheses=[
                "The target may store processed image data in memory",
            ],
        ),
    ]

    fake_gemini_response = """
    {
        "results": [
            {
                "claim_element_id": "1.1",
                "queries": [
                    {
                        "query": "Samsung Galaxy S26 Ultra image processor",
                        "rationale": "Search for product-specific image processing information.",
                        "priority": 1
                    },
                    {
                        "query": "site:samsung.com Galaxy S26 image signal processing",
                        "rationale": "Search Samsung sources for image processing information.",
                        "priority": 2
                    }
                ],
                "preferred_sources": [
                    "Samsung official documentation",
                    "Samsung technical publications"
                ],
                "search_strategy": "Prioritize authoritative product sources for image processing."
            },
            {
                "claim_element_id": "1.2",
                "queries": [
                    {
                        "query": "Samsung Galaxy S26 Ultra image memory",
                        "rationale": "Search for product-specific image memory information.",
                        "priority": 1
                    },
                    {
                        "query": "Galaxy S26 Ultra memory controller image data",
                        "rationale": "Search for implementation-level evidence concerning image data storage.",
                        "priority": 2
                    }
                ],
                "preferred_sources": [
                    "Samsung official documentation",
                    "Samsung technical publications"
                ],
                "search_strategy": "Prioritize authoritative sources for image data storage."
            }
        ]
    }
    """

    with patch(
        "app.agents.search_planner.GeminiService"
    ) as mock_gemini:

        mock_gemini.return_value.generate.return_value = (
            fake_gemini_response
        )

        planner = SearchPlanner()

        result = planner.plan_batch(
            elements,
            target,
            technology_profiles,
        )

    assert len(result) == 2

    assert result[0].claim_element_id == "1.1"

    assert result[0].queries[0].priority == 1

    assert any(
        "Galaxy S26 Ultra" in query.query
        for query in result[0].queries
    )

    assert result[1].claim_element_id == "1.2"

    assert result[1].queries[0].priority == 1

    assert any(
        "memory" in query.query.lower()
        for query in result[1].queries
    )

    assert len(result[0].preferred_sources) > 0
    assert len(result[1].preferred_sources) > 0

    assert result[0].search_strategy != ""
    assert result[1].search_strategy != ""

    mock_gemini.return_value.generate.assert_called_once()


def test_search_planner_batch_invalid_element_ids():

    elements = [
        ClaimElement(
            id="1.1",
            claim_number="1",
            text="a processor configured to receive image data",
        ),
        ClaimElement(
            id="1.2",
            claim_number="1",
            text="a memory configured to store processed image data",
        ),
    ]

    target = TargetScope(
        company="Samsung",
        product="Galaxy S26 Ultra",
    )

    technology_profiles = [
        TechnologyProfile(
            claim_element_id="1.1",
            target=target,
            core_concept="Processor reception of image data",
            technical_concepts=[],
            alternative_terminology=[],
            likely_components=[],
            implementation_hypotheses=[],
        ),
        TechnologyProfile(
            claim_element_id="1.2",
            target=target,
            core_concept="Storage of processed image data",
            technical_concepts=[],
            alternative_terminology=[],
            likely_components=[],
            implementation_hypotheses=[],
        ),
    ]

    fake_gemini_response = """
    {
        "results": [
            {
                "claim_element_id": "1.1",
                "queries": [],
                "preferred_sources": [],
                "search_strategy": ""
            },
            {
                "claim_element_id": "1.3",
                "queries": [],
                "preferred_sources": [],
                "search_strategy": ""
            }
        ]
    }
    """

    with patch(
        "app.agents.search_planner.GeminiService"
    ) as mock_gemini:

        mock_gemini.return_value.generate.return_value = (
            fake_gemini_response
        )

        planner = SearchPlanner()

        with pytest.raises(
            ValueError,
            match="invalid claim element IDs",
        ):
            planner.plan_batch(
                elements,
                target,
                technology_profiles,
            )

    mock_gemini.return_value.generate.assert_called_once()


def test_search_planner_batch_mismatched_profiles():

    elements = [
        ClaimElement(
            id="1.1",
            claim_number="1",
            text="a processor configured to receive image data",
        ),
    ]

    target = TargetScope(
        company="Samsung",
        product="Galaxy S26 Ultra",
    )

    technology_profiles = [
        TechnologyProfile(
            claim_element_id="1.2",
            target=target,
            core_concept="Unexpected profile",
            technical_concepts=[],
            alternative_terminology=[],
            likely_components=[],
            implementation_hypotheses=[],
        ),
    ]

    with patch(
        "app.agents.search_planner.GeminiService"
    ) as mock_gemini:

        planner = SearchPlanner()

        with pytest.raises(
            ValueError,
            match="do not match claim element IDs",
        ):
            planner.plan_batch(
                elements,
                target,
                technology_profiles,
            )

    mock_gemini.return_value.generate.assert_not_called()
