from unittest.mock import patch

import pytest

from app.agents.technology_profiler import TechnologyProfiler
from app.models.schemas import ClaimElement, TargetScope


def test_technology_profiler():

    element = ClaimElement(
        id="1.1",
        claim_number="1",
        text="a processor configured to receive image data",
    )

    target = TargetScope(
        company="Samsung",
        product="Galaxy S26 Ultra",
    )

    fake_gemini_response = """
    {
        "claim_element_id": "1.1",
        "target": {
            "company": "Samsung",
            "product": "Galaxy S26 Ultra",
            "technology": null
        },
        "core_concept": "Processor reception of image data",
        "technical_concepts": [
            "Image Signal Processing",
            "MIPI CSI"
        ],
        "alternative_terminology": [
            "ISP",
            "Image Processor"
        ],
        "likely_components": [
            "Image Signal Processor",
            "Camera Interface"
        ],
        "implementation_hypotheses": [
            "The target may use a dedicated ISP",
            "The target may receive camera data through MIPI CSI"
        ]
    }
    """

    with patch(
        "app.agents.technology_profiler.GeminiService"
    ) as mock_gemini:

        mock_gemini.return_value.generate.return_value = (
            fake_gemini_response
        )

        profiler = TechnologyProfiler()

        result = profiler.profile(
            element,
            target,
        )

    assert result.claim_element_id == "1.1"
    assert result.target.company == "Samsung"
    assert result.target.product == "Galaxy S26 Ultra"

    assert result.core_concept == (
        "Processor reception of image data"
    )

    assert "Image Signal Processing" in result.technical_concepts
    assert "MIPI CSI" in result.technical_concepts

    assert "ISP" in result.alternative_terminology

    assert "Image Signal Processor" in result.likely_components

    assert len(result.implementation_hypotheses) == 2

    mock_gemini.return_value.generate.assert_called_once()


def test_technology_profiler_batch_without_elements():

    target = TargetScope(
        company="Samsung",
        product="Galaxy S26 Ultra",
    )

    with patch(
        "app.agents.technology_profiler.GeminiService"
    ) as mock_gemini:

        profiler = TechnologyProfiler()

        result = profiler.profile_batch(
            [],
            target,
        )

    assert result == []

    mock_gemini.return_value.generate.assert_not_called()


def test_technology_profiler_batch_multiple_elements():

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

    fake_gemini_response = """
    {
        "results": [
            {
                "claim_element_id": "1.1",
                "target": {
                    "company": "Samsung",
                    "product": "Galaxy S26 Ultra",
                    "technology": null
                },
                "core_concept": "Processor reception of image data",
                "technical_concepts": [
                    "Image Signal Processing",
                    "MIPI CSI"
                ],
                "alternative_terminology": [
                    "ISP",
                    "Image Processor"
                ],
                "likely_components": [
                    "Image Signal Processor",
                    "Camera Interface"
                ],
                "implementation_hypotheses": [
                    "The target may use a dedicated ISP"
                ]
            },
            {
                "claim_element_id": "1.2",
                "target": {
                    "company": "Samsung",
                    "product": "Galaxy S26 Ultra",
                    "technology": null
                },
                "core_concept": "Storage of processed image data",
                "technical_concepts": [
                    "Image data storage",
                    "Memory controller"
                ],
                "alternative_terminology": [
                    "Image buffer",
                    "Frame buffer"
                ],
                "likely_components": [
                    "Memory",
                    "Memory controller"
                ],
                "implementation_hypotheses": [
                    "The target may store processed image data in memory"
                ]
            }
        ]
    }
    """

    with patch(
        "app.agents.technology_profiler.GeminiService"
    ) as mock_gemini:

        mock_gemini.return_value.generate.return_value = (
            fake_gemini_response
        )

        profiler = TechnologyProfiler()

        result = profiler.profile_batch(
            elements,
            target,
        )

    assert len(result) == 2

    assert result[0].claim_element_id == "1.1"
    assert result[0].core_concept == (
        "Processor reception of image data"
    )

    assert result[0].target.company == "Samsung"
    assert result[0].target.product == "Galaxy S26 Ultra"

    assert result[1].claim_element_id == "1.2"
    assert result[1].core_concept == (
        "Storage of processed image data"
    )

    assert result[1].target.company == "Samsung"
    assert result[1].target.product == "Galaxy S26 Ultra"

    mock_gemini.return_value.generate.assert_called_once()


def test_technology_profiler_batch_invalid_element_ids():

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

    fake_gemini_response = """
    {
        "results": [
            {
                "claim_element_id": "1.1",
                "target": {
                    "company": "Samsung",
                    "product": "Galaxy S26 Ultra",
                    "technology": null
                },
                "core_concept": "Processor reception of image data",
                "technical_concepts": [],
                "alternative_terminology": [],
                "likely_components": [],
                "implementation_hypotheses": []
            },
            {
                "claim_element_id": "1.3",
                "target": {
                    "company": "Samsung",
                    "product": "Galaxy S26 Ultra",
                    "technology": null
                },
                "core_concept": "Unexpected element",
                "technical_concepts": [],
                "alternative_terminology": [],
                "likely_components": [],
                "implementation_hypotheses": []
            }
        ]
    }
    """

    with patch(
        "app.agents.technology_profiler.GeminiService"
    ) as mock_gemini:

        mock_gemini.return_value.generate.return_value = (
            fake_gemini_response
        )

        profiler = TechnologyProfiler()

        with pytest.raises(
            ValueError,
            match="invalid claim element IDs",
        ):
            profiler.profile_batch(
                elements,
                target,
            )

    mock_gemini.return_value.generate.assert_called_once()
