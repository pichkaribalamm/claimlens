from app.models.schemas import SearchQuery
from app.services.search_service import SearchService


def test_search_service():

    query = SearchQuery(
        query="Samsung Galaxy S26 Ultra image processor",
        rationale="Find product-specific image processing information.",
        priority=1
    )

    service = SearchService()

    result = service.search(query)

    assert result == []
