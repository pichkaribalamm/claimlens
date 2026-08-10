from ddgs import DDGS

from app.models.schemas import SearchQuery, SearchResult


class SearchService:

    def __init__(self):
        self.search_engine = DDGS()

    def search(
        self,
        query: SearchQuery,
    ) -> list[SearchResult]:

        results = self.search_engine.text(
            query.query,
            max_results=10
        )

        search_results = []

        for result in results:
            search_results.append(
                SearchResult(
                    title=result["title"],
                    url=result["href"],
                    snippet=result.get("body"),
                    source=None
                )
            )

        return search_results
