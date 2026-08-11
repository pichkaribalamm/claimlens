import requests
from bs4 import BeautifulSoup

from app.models.schemas import SearchResult


class PageFetcher:

    def __init__(
        self,
        connect_timeout: int = 10,
        read_timeout: int = 25,
    ):
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": (
                "en-US,en;q=0.9"
            ),
            "Connection": "keep-alive",
        }

    def fetch(
        self,
        search_result: SearchResult,
    ) -> str:

        url = str(
            search_result.url
        )

        try:

            response = requests.get(
                url,
                headers=self.headers,
                timeout=(
                    self.connect_timeout,
                    self.read_timeout,
                ),
                allow_redirects=True,
            )

            response.raise_for_status()

        except requests.exceptions.Timeout as exc:

            raise RuntimeError(
                f"Page fetch timed out: {url}"
            ) from exc

        except requests.exceptions.HTTPError as exc:

            status_code = (
                exc.response.status_code
                if exc.response is not None
                else "unknown"
            )

            raise RuntimeError(
                f"HTTP {status_code} while fetching: {url}"
            ) from exc

        except requests.exceptions.RequestException as exc:

            raise RuntimeError(
                f"Request failed while fetching {url}: {exc}"
            ) from exc

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        # --------------------------------------------------
        # Remove elements that do not contain useful page
        # content.
        # --------------------------------------------------

        for element in soup(
            [
                "script",
                "style",
                "noscript",
                "svg",
                "canvas",
                "iframe",
                "template",
            ]
        ):
            element.decompose()

        # --------------------------------------------------
        # Remove common navigation / presentation elements.
        #
        # These frequently introduce large amounts of
        # irrelevant text into search-result pages.
        # --------------------------------------------------

        for element in soup(
            [
                "nav",
                "footer",
                "header",
                "aside",
            ]
        ):
            element.decompose()

        # --------------------------------------------------
        # Prefer the main article/content area when the page
        # exposes one.
        # --------------------------------------------------

        content_root = self._find_content_root(
            soup
        )

        # --------------------------------------------------
        # Preserve structural boundaries.
        #
        # The previous implementation used:
        #
        #     get_text(separator=" ")
        #
        # which flattened the entire page.
        #
        # Keeping newlines between block elements gives the
        # reducer useful paragraph / heading boundaries.
        # --------------------------------------------------

        text = content_root.get_text(
            separator="\n",
            strip=True,
        )

        # --------------------------------------------------
        # Normalize excessive whitespace while preserving
        # paragraph boundaries.
        # --------------------------------------------------

        lines = []

        for line in text.splitlines():

            line = " ".join(
                line.split()
            ).strip()

            if not line:
                continue

            lines.append(
                line
            )

        if not lines:
            return ""

        return "\n".join(
            lines
        )

    def _find_content_root(
        self,
        soup: BeautifulSoup,
    ):
        """
        Prefer the page's primary content container when
        one can be identified.

        Fall back to the complete document body.
        """

        # --------------------------------------------------
        # Strong semantic content containers.
        # --------------------------------------------------

        selectors = [
            "main",
            "article",
            '[role="main"]',
        ]

        for selector in selectors:

            element = soup.select_one(
                selector
            )

            if element is not None:

                text = element.get_text(
                    separator=" ",
                    strip=True,
                )

                if len(text) >= 200:
                    return element

        # --------------------------------------------------
        # Common article/content class or id patterns.
        # --------------------------------------------------

        candidates = []

        for element in soup.find_all(
            [
                "div",
                "section",
            ]
        ):

            identifier = " ".join(
                [
                    str(
                        element.get(
                            "id",
                            "",
                        )
                    ),
                    " ".join(
                        element.get(
                            "class",
                            [],
                        )
                    ),
                ]
            ).lower()

            if not identifier:
                continue

            if not any(
                marker in identifier
                for marker in (
                    "article",
                    "content",
                    "main",
                    "post",
                    "body",
                )
            ):
                continue

            text_length = len(
                element.get_text(
                    separator=" ",
                    strip=True,
                )
            )

            if text_length < 200:
                continue

            candidates.append(
                (
                    text_length,
                    element,
                )
            )

        if candidates:

            # Prefer the smallest sufficiently large content
            # container rather than the entire page.
            candidates.sort(
                key=lambda item: item[0]
            )

            return candidates[0][1]

        # --------------------------------------------------
        # Final fallback.
        # --------------------------------------------------

        if soup.body is not None:
            return soup.body

        return soup
