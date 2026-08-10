from app.models.schemas import SearchQuery, SearchResult


class SearchService:

    def search(
        self,
        query: SearchQuery,
    ) -> list[SearchResult]:
        """
        Execute a web search and return structured results.

        The actual search provider will be added in the next step.
        """

        return []
