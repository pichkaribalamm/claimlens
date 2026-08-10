from app.services.search_service import SearchService
from app.models.schemas import SearchQuery


query = SearchQuery(
    query="Samsung Galaxy S26 Ultra image processor",
    rationale="Test web search retrieval.",
    priority=1
)

service = SearchService()

results = service.search(query)

print("\n=== SEARCH RESULTS ===")

for i, result in enumerate(results, start=1):
    print(f"\n{i}. {result.title}")
    print(f"URL: {result.url}")
    print(f"Snippet: {result.snippet}")
