from app.models.schemas import ClaimElement
from app.services.page_content_reducer import PageContentReducer


def test_reducer_extracts_relevant_context():

    claim_element = ClaimElement(
        id="1.1",
        claim_number="1",
        text="a processor configured to receive image data",
    )

    page_content = (
        "This is unrelated content. " * 100
        + "The device includes an image signal processor "
        + "that handles image data from the camera. "
        + "This is important technical information. "
        + "More unrelated content. " * 100
    )

    reducer = PageContentReducer()

    result = reducer.reduce(
        claim_element,
        page_content,
    )

    assert "image signal processor" in result
    assert "image data" in result
    assert len(result) < len(page_content)


def test_reducer_returns_empty_when_no_terms_match():

    claim_element = ClaimElement(
        id="1.1",
        claim_number="1",
        text="a processor configured to receive image data",
    )

    page_content = (
        "This page discusses battery capacity "
        "and display resolution only."
    )

    reducer = PageContentReducer()

    result = reducer.reduce(
        claim_element,
        page_content,
    )

    assert result == ""


def test_reducer_respects_max_chars():

    claim_element = ClaimElement(
        id="1.1",
        claim_number="1",
        text="a processor configured to receive image data",
    )

    page_content = (
        "processor image data camera "
        + ("technical information " * 1000)
    )

    reducer = PageContentReducer(
        max_chars=1000,
    )

    result = reducer.reduce(
        claim_element,
        page_content,
    )

    assert len(result) <= 1000
