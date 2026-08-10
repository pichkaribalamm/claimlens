from unittest.mock import patch

from app.models.schemas import SearchQuery
from app.services.search_service import SearchService


def test_search_service():

    query = SearchQuery(
        query="Samsung Galaxy S26 Ultra image processor",
        rationale="Find product-specific image processing information.",
        priority=1
    )

    fake_ddgs_results = [
        {
            "title": "Samsung Galaxy S26 Ultra",
            "href": "https://www.samsung.com/in/smartphones/galaxy-s26-ultra/",
            "body": "Galaxy S26 Ultra features a customized processor."
        },
        {
            "title": "Galaxy S26 Ultra Camera",
            "href": "https://example.com/camera",
            "body": "The device uses advanced image processing."
        }
    ]

    with patch(
        "app.services.search_service.DDGS"
    ) as mock_ddgs:

        mock_ddgs.return_value.text.return_value = (
            fake_ddgs_results
        )

        service = SearchService()

        result = service.search(query)

    assert len(result) == 2

    assert result[0].title == "Samsung Galaxy S26 Ultra"
    assert str(result[0].url) == (
        "https://www.samsung.com/in/smartphones/galaxy-s26-ultra/"
    )
    assert result[0].snippet == (
        "Galaxy S26 Ultra features a customized processor."
    )

    assert result[1].title == "Galaxy S26 Ultra Camera"
    assert str(result[1].url) == "https://example.com/camera"

    mock_ddgs.return_value.text.assert_called_once_with(
        query.query,
        max_results=10
    )
