from urllib.parse import (
    parse_qsl,
    urlencode,
    urlparse,
    urlunparse,
)

from ddgs import DDGS

from app.models.schemas import (
    SearchQuery,
    SearchResult,
)


class SearchService:

    # ============================================================
    # PATENT DOMAINS
    #
    # Patents are never allowed to enter ClaimLens as evidence
    # candidates.
    # ============================================================

    PATENT_DOMAINS = {
        "patents.google.com",
        "patents.justia.com",
        "patentscope.wipo.int",
        "worldwide.espacenet.com",
        "espacenet.com",
        "ppubs.uspto.gov",
        "patents.uspto.gov",
        "patentscope2.wipo.int",
    }

    # ============================================================
    # PATENT PATH MARKERS
    #
    # Used in addition to domain-level filtering because patent
    # pages may appear on less obvious domains.
    # ============================================================

    PATENT_PATH_MARKERS = {
        "/patent/",
        "/patents/",
        "/patent-search/",
        "/patent-search",
        "/patentnumber/",
        "/patent-number/",
        "/patentscope/",
        "/publication/",
        "/publications/",
    }

    # ============================================================
    # PATENT QUERY / URL MARKERS
    #
    # These are deliberately conservative.
    #
    # We do NOT reject a normal technical page merely because
    # its URL contains a generic word such as "publication".
    # Domain/path detection above has priority.
    # ============================================================

    PATENT_QUERY_MARKERS = {
        "patentnumber",
        "publicationnumber",
        "patentid",
        "patent_id",
    }

    # ============================================================
    # SEARCH CONFIGURATION
    # ============================================================

    DEFAULT_MAX_RESULTS = 10

    def __init__(
        self,
        max_results: int = DEFAULT_MAX_RESULTS,
    ):

        if max_results < 1:
            raise ValueError(
                "max_results must be at least 1."
            )

        self.max_results = max_results

        self.search_engine = DDGS()

    # ============================================================
    # SEARCH
    # ============================================================

    def search(
        self,
        query: SearchQuery,
    ) -> list[SearchResult]:
        """
        Execute a web search and return cleaned SearchResult
        objects.

        SearchService is responsible for candidate discovery.

        It deliberately does NOT perform general source-quality
        qualification. That belongs to SourceQualifier.

        Patents are the one hard exception: they are removed here
        because ClaimLens must never treat patents as relevant
        product/technology evidence.
        """

        results = self.search_engine.text(
            query.query,
            max_results=self.max_results,
        )

        search_results = []

        for result in results:

            if not isinstance(
                result,
                dict,
            ):
                continue

            url = result.get(
                "href"
            )

            if not url:
                continue

            url = str(
                url
            ).strip()

            if not url:
                continue

            # ----------------------------------------------------
            # HARD PATENT EXCLUSION
            #
            # Patents must never enter ClaimLens as evidence
            # candidates.
            # ----------------------------------------------------

            if self._is_patent_source(
                url
            ):
                continue

            # ----------------------------------------------------
            # Validate URL before creating SearchResult.
            # ----------------------------------------------------

            if not self._is_valid_http_url(
                url
            ):
                continue

            title = str(
                result.get(
                    "title",
                    "",
                )
            ).strip()

            snippet = result.get(
                "body"
            )

            if snippet is not None:

                snippet = str(
                    snippet
                ).strip()

            source = self._domain(
                url
            )

            try:

                search_results.append(
                    SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                        source=source,
                    )
                )

            except Exception:
                # A malformed result should not terminate the
                # entire search.
                continue

        return self._deduplicate(
            search_results
        )

    # ============================================================
    # PATENT DETECTION
    # ============================================================

    def _is_patent_source(
        self,
        url: str,
    ) -> bool:
        """
        Determine whether a URL is a patent source.

        This is intentionally stricter than ordinary source
        qualification.

        Returning True here means the result is completely removed
        from the ClaimLens evidence pipeline.
        """

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

        # --------------------------------------------------------
        # Domain-level patent detection.
        # --------------------------------------------------------

        if hostname in self.PATENT_DOMAINS:
            return True

        # --------------------------------------------------------
        # Path-level patent detection.
        # --------------------------------------------------------

        path = (
            parsed.path or ""
        ).lower()

        for marker in self.PATENT_PATH_MARKERS:

            if marker in path:
                return True

        # --------------------------------------------------------
        # Query parameter detection.
        # --------------------------------------------------------

        query_parameters = {
            key.lower()
            for key, _ in parse_qsl(
                parsed.query,
                keep_blank_values=True,
            )
        }

        if (
            query_parameters
            & self.PATENT_QUERY_MARKERS
        ):
            return True

        # --------------------------------------------------------
        # Conservative textual URL detection.
        #
        # We only use "patent" here when it appears as an obvious
        # URL path/query component, rather than rejecting arbitrary
        # technical content containing the word in its title.
        # --------------------------------------------------------

        normalized_path = (
            path.replace(
                "-",
                "/",
            ).replace(
                "_",
                "/",
            )
        )

        path_parts = {
            part
            for part in normalized_path.split("/")
            if part
        }

        if "patent" in path_parts:
            return True

        if "patents" in path_parts:
            return True

        return False

    # ============================================================
    # URL VALIDATION
    # ============================================================

    def _is_valid_http_url(
        self,
        url: str,
    ) -> bool:

        try:

            parsed = urlparse(
                str(url)
            )

        except Exception:

            return False

        if parsed.scheme.lower() not in {
            "http",
            "https",
        }:
            return False

        if not parsed.hostname:
            return False

        return True

    # ============================================================
    # DOMAIN EXTRACTION
    # ============================================================

    def _domain(
        self,
        url: str,
    ) -> str:

        try:

            parsed = urlparse(
                str(url)
            )

        except Exception:

            return ""

        hostname = (
            parsed.hostname or ""
        ).lower()

        return hostname.removeprefix(
            "www."
        )

    # ============================================================
    # DEDUPLICATION
    # ============================================================

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

            if not normalized_url:
                continue

            if normalized_url in seen_urls:
                continue

            seen_urls.add(
                normalized_url
            )

            unique_results.append(
                result
            )

        return unique_results

    # ============================================================
    # URL NORMALIZATION
    # ============================================================

    def _normalize_url(
        self,
        url: str,
    ) -> str:

        try:

            parsed = urlparse(
                str(url)
            )

        except Exception:

            return ""

        scheme = (
            parsed.scheme.lower()
        )

        hostname = (
            parsed.hostname or ""
        ).lower()

        hostname = hostname.removeprefix(
            "www."
        )

        if not hostname:
            return ""

        path = (
            parsed.path or ""
        ).rstrip("/")

        # --------------------------------------------------------
        # Remove common tracking parameters.
        #
        # These do not normally identify a unique technical page.
        # --------------------------------------------------------

        tracking_parameters = {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "gclid",
            "fbclid",
            "ref",
        }

        query_items = []

        for key, value in parse_qsl(
            parsed.query,
            keep_blank_values=True,
        ):

            if key.lower() in tracking_parameters:
                continue

            query_items.append(
                (
                    key,
                    value,
                )
            )

        normalized_query = urlencode(
            sorted(
                query_items
            )
        )

        return urlunparse(
            (
                scheme,
                hostname,
                path,
                "",
                normalized_query,
                "",
            )
        )
