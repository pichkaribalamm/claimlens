from urllib.parse import urlparse

from ddgs import DDGS

from app.models.schemas import SearchQuery, SearchResult


class SearchService:

    PATENT_DOMAINS = {
        "patents.google.com",
        "patents.justia.com",
        "patentscope.wipo.int",
        "worldwide.espacenet.com",
        "espacenet.com",
        "ppubs.uspto.gov",
        "patents.uspto.gov",
    }

    PATENT_PATH_MARKERS = {
        "/patent/",
        "/patents/",
        "/patent-search/",
        "/patent-search",
        "/patentnumber/",
    }

    def __init__(self):

        self.search_engine = DDGS()

    def search(
        self,
        query: SearchQuery,
    ) -> list[SearchResult]:

        results = self.search_engine.text(
            query.query,
            max_results=10,
        )

        search_results = []

        for result in results:

            url = result.get("href")

            if not url:
                continue

            # ------------------------------------------------
            # Hard patent exclusion.
            #
            # Patents must never enter ClaimLens as relevant
            # evidence candidates.
            # ------------------------------------------------

            if self._is_patent_source(url):
                continue

            title = result.get(
                "title",
                "",
            )

            snippet = result.get(
                "body"
            )

            search_results.append(
                SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source=None,
                )
            )

        return self._deduplicate(
            search_results
        )

    def _is_patent_source(
        self,
        url: str,
    ) -> bool:

        try:

            parsed = urlparse(
                str(url)
            )

        except Exception:

            return False

        hostname = (
            parsed.hostname or ""
        ).lower()

        hostname = hostname.removeprefix(
            "www."
        )

        if hostname in self.PATENT_DOMAINS:
            return True

        path = (
            parsed.path or ""
        ).lower()

        for marker in self.PATENT_PATH_MARKERS:

            if marker in path:
                return True

        return False

    def _deduplicate(
        self,
        results: list[SearchResult],
    ) -> list[SearchResult]:

        seen_urls = set()

        unique_results = []

        for result in results:

            normalized_url = (
                self._normalize_url(
                    result.url
                )
            )

            if normalized_url in seen_urls:
                continue

            seen_urls.add(
                normalized_url
            )

            unique_results.append(
                result
            )

        return unique_results

    def _normalize_url(
        self,
        url: str,
    ) -> str:

        parsed = urlparse(
            str(url)
        )

        scheme = (
            parsed.scheme.lower()
        )

        hostname = (
            parsed.hostname or ""
        ).lower()

        hostname = hostname.removeprefix(
            "www."
        )

        path = (
            parsed.path or ""
        ).rstrip("/")

        return (
            f"{scheme}://"
            f"{hostname}"
            f"{path}"
        )
