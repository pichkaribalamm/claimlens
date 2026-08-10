from unittest.mock import patch

from app.agents.technology_profiler import TechnologyProfiler
from app.models.schemas import ClaimElement, TargetScope


def test_technology_profiler():

    element = ClaimElement(
        id="1.1",
        claim_number="1",
        text="a processor configured to receive image data"
    )

    target = TargetScope(
        company="Samsung",
        product="Galaxy S26 Ultra"
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
            target
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

    assert len(result.implementation_hypotheses) == 2        "likely_components": [
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
            target
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

    assert len(result.implementation_hypotheses) == 2        "likely_components": [
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
            target
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

    assert len(result.implementation_hypotheses) == 2        "likely_components": [
            "Image Signal Processor",
            "Camera Interface"
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
            target
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
