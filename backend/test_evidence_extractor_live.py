from app.agents.evidence_extractor import EvidenceExtractor
from app.models.schemas import ClaimElement, SearchResult
from app.services.page_fetcher import PageFetcher


claim_element = ClaimElement(
    id="1.2",
    claim_number="1",
    text="an AI image signal processor (ISP) associated with the front camera"
)


search_result = SearchResult(
    title="Samsung Galaxy S26 Ultra",
    url="https://www.samsung.com/in/smartphones/galaxy-s26-ultra/",
    snippet="The Galaxy S26 Ultra uses a customized processor.",
    source="Samsung"
)


fetcher = PageFetcher()

page_content = fetcher.fetch(search_result)

extractor = EvidenceExtractor()

evidence = extractor.extract(
    claim_element,
    search_result,
    page_content,
)


print("\n=== EVIDENCE FINDINGS ===")

for i, finding in enumerate(evidence, start=1):
    print(f"\n{i}. CLAIM ELEMENT: {finding.claim_element_id}")
    print(f"Source: {finding.source_title}")
    print(f"URL: {finding.url}")
    print(f"Excerpt: {finding.excerpt}")
    print(f"Evidence Type: {finding.evidence_type}")
    print(f"Relevance: {finding.relevance}")
