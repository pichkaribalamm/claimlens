import requests
from bs4 import BeautifulSoup

from app.models.schemas import SearchResult


class PageFetcher:

    def __init__(self):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0 Safari/537.36"
            )
        }

    def fetch(
        self,
        search_result: SearchResult,
    ) -> str:

        response = requests.get(
            str(search_result.url),
            headers=self.headers,
            timeout=15
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for element in soup(
            ["script", "style", "noscript", "svg"]
        ):
            element.decompose()

        text = soup.get_text(
            separator=" ",
            strip=True
        )

        return text
