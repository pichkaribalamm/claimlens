from unittest.mock import patch

from app.models.schemas import SearchResult
from app.services.page_fetcher import PageFetcher


def test_page_fetcher():

    search_result = SearchResult(
        title="Samsung Galaxy S26 Ultra",
        url="https://www.samsung.com/in/smartphones/galaxy-s26-ultra/",
        snippet="The Galaxy S26 Ultra uses a customized processor.",
        source="Samsung"
    )

    fake_html = """
    <html>
        <head>
            <title>Samsung Galaxy S26 Ultra</title>
            <style>
                .hidden { display: none; }
            </style>
        </head>
        <body>
            <h1>Samsung Galaxy S26 Ultra</h1>
            <p>The device uses a customized processor.</p>

            <script>
                console.log("This should not appear");
            </script>

            <p>The camera system includes advanced image processing.</p>
        </body>
    </html>
    """

    with patch(
        "app.services.page_fetcher.requests.get"
    ) as mock_get:

        mock_response = mock_get.return_value

        mock_response.text = fake_html

        mock_response.raise_for_status.return_value = None

        fetcher = PageFetcher()

        result = fetcher.fetch(search_result)

    assert "Samsung Galaxy S26 Ultra" in result
    assert "The device uses a customized processor." in result
    assert "The camera system includes advanced image processing." in result

    assert "console.log" not in result
    assert ".hidden" not in result

    mock_get.assert_called_once_with(
        str(search_result.url),
        headers=fetcher.headers,
        timeout=15
    )
