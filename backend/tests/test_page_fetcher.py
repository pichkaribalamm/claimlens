from app.models.schemas import SearchResult
from app.services.page_fetcher import PageFetcher


def test_page_fetcher():

    search_result = SearchResult(
        title="Samsung Galaxy S26 Ultra",
        url="https://www.samsung.com/in/smartphones/galaxy-s26-ultra/",
        snippet="The Galaxy S26 Ultra uses a customized processor.",
        source="Samsung"
    )

    fetcher = PageFetcher()

    result = fetcher.fetch(search_result)

    assert result == ""
