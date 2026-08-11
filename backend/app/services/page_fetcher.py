import time

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.models.schemas import SearchResult


class PageFetcher:

    def __init__(
        self,
        connect_timeout: int = 10,
        read_timeout: int = 25,
        max_retries: int = 2,
    ):
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.max_retries = max_retries

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,"
                "image/avif,image/webp,"
                "*/*;q=0.8"
            ),
            "Accept-Language": (
                "en-US,en;q=0.9"
            ),
            "Accept-Encoding": (
                "gzip, deflate"
            ),
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        self.session = requests.Session()

        retry_strategy = Retry(
            total=max_retries,
            connect=max_retries,
            read=max_retries,
            status=max_retries,
            backoff_factor=1,
            status_forcelist={
                429,
                500,
                502,
                503,
                504,
            },
            allowed_methods={
                "GET",
            },
            respect_retry_after_header=True,
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy
        )

        self.session.mount(
            "http://",
            adapter,
        )

        self.session.mount(
            "https://",
            adapter,
        )

    # ============================================================
    # FETCH
    # ============================================================

    def fetch(
        self,
        search_result: SearchResult,
    ) -> str:

        url = str(
            search_result.url
        )

        try:

            response = self.session.get(
                url,
                headers=self.headers,
                timeout=(
                    self.connect_timeout,
                    self.read_timeout,
                ),
                allow_redirects=True,
            )

        except requests.exceptions.ConnectTimeout as exc:

            raise RuntimeError(
                f"Connection timed out while fetching: {url}"
            ) from exc

        except requests.exceptions.ReadTimeout as exc:

            raise RuntimeError(
                f"Read timed out while fetching: {url}"
            ) from exc

        except requests.exceptions.Timeout as exc:

            raise RuntimeError(
                f"Request timed out while fetching: {url}"
            ) from exc

        except requests.exceptions.ConnectionError as exc:

            raise RuntimeError(
                f"Connection failed while fetching: {url}"
            ) from exc

        except requests.exceptions.RequestException as exc:

            raise RuntimeError(
                f"Request failed while fetching {url}: {exc}"
            ) from exc

        # --------------------------------------------------------
        # HTTP status handling.
        # --------------------------------------------------------

        if response.status_code == 403:

            raise RuntimeError(
                f"HTTP 403 Forbidden while fetching: {url}"
            )

        if response.status_code == 401:

            raise RuntimeError(
                f"HTTP 401 Unauthorized while fetching: {url}"
            )

        if response.status_code == 404:

            raise RuntimeError(
                f"HTTP 404 Not Found while fetching: {url}"
            )

        if response.status_code == 429:

            raise RuntimeError(
                f"HTTP 429 Too Many Requests while fetching: {url}"
            )

        if response.status_code >= 400:

            raise RuntimeError(
                f"HTTP {response.status_code} "
                f"while fetching: {url}"
            )

        # --------------------------------------------------------
        # Basic content-type protection.
        #
        # ClaimLens expects HTML/text pages. Do not attempt to
        # feed binary files or unrelated content into BeautifulSoup.
        # --------------------------------------------------------

        content_type = (
            response.headers
            .get(
                "Content-Type",
                "",
            )
            .lower()
        )

        if (
            content_type
            and not any(
                content_type.startswith(
                    allowed
                )
                for allowed in (
                    "text/html",
                    "application/xhtml+xml",
                    "text/plain",
                    "application/xml",
                )
            )
        ):

            raise RuntimeError(
                f"Unsupported content type "
                f"'{content_type}' while fetching: {url}"
            )

        if not response.text.strip():

            raise RuntimeError(
                f"Empty page returned while fetching: {url}"
            )

        # --------------------------------------------------------
        # Parse HTML.
        # --------------------------------------------------------

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        # --------------------------------------------------------
        # Remove elements that do not contain useful technical
        # page content.
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # Remove common navigation / presentation elements.
        # --------------------------------------------------------

        for element in soup(
            [
                "nav",
                "footer",
                "header",
                "aside",
            ]
        ):

            element.decompose()

        # --------------------------------------------------------
        # Prefer the primary content area.
        # --------------------------------------------------------

        content_root = self._find_content_root(
            soup
        )

        # --------------------------------------------------------
        # Preserve structural boundaries.
        # --------------------------------------------------------

        text = content_root.get_text(
            separator="\n",
            strip=True,
        )

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

    # ============================================================
    # CONTENT ROOT
    # ============================================================

    def _find_content_root(
        self,
        soup: BeautifulSoup,
    ):
        """
        Prefer the page's primary content container.

        Fall back to the body/document when no sufficiently
        strong content container can be identified.
        """

        # --------------------------------------------------------
        # Strong semantic content containers.
        # --------------------------------------------------------

        selectors = [
            "main",
            "article",
            '[role="main"]',
        ]

        for selector in selectors:

            element = soup.select_one(
                selector
            )

            if element is None:
                continue

            text = element.get_text(
                separator=" ",
                strip=True,
            )

            if len(text) >= 200:
                return element

        # --------------------------------------------------------
        # Common article/content class or ID patterns.
        # --------------------------------------------------------

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

            candidates.sort(
                key=lambda item: item[0]
            )

            return candidates[0][1]

        # --------------------------------------------------------
        # Final fallback.
        # --------------------------------------------------------

        if soup.body is not None:
            return soup.body

        return soup
