from app.models.schemas import SearchResult
from app.services.page_fetcher import PageFetcher


search_result = SearchResult(
    title="Samsung Galaxy S26 Ultra",
    url="https://www.samsung.com/in/smartphones/galaxy-s26-ultra/",
    snippet="The Galaxy S26 Ultra uses a customized processor.",
    source="Samsung"
)

fetcher = PageFetcher()

text = fetcher.fetch(search_result)

print("\n=== PAGE CONTENT ===")
print(text[:5000])
