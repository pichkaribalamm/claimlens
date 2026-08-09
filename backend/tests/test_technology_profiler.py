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

    profiler = TechnologyProfiler()

    result = profiler.profile(element, target)

    assert result["claim_element_id"] == "1.1"
    assert result["claim_element"] == (
        "a processor configured to receive image data"
    )
    assert result["target"]["company"] == "Samsung"
    assert result["target"]["product"] == "Galaxy S26 Ultra"
