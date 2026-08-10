import os
from unittest.mock import patch

os.environ["CLAIMLENS_USE_MOCK_GEMINI"] = "true"

from app.agents.claim_analyzer import ClaimAnalyzer
from app.agents.claim_mapper import ClaimMapper
from app.agents.claim_parser import ClaimParser
from app.agents.evidence_extractor import EvidenceExtractor
from app.agents.evidence_verifier import EvidenceVerifier
from app.agents.search_planner import SearchPlanner
from app.agents.technology_profiler import TechnologyProfiler
from app.models.schemas import (
    Claim,
    TargetScope,
    VerifiedEvidence,
)
from app.services.search_service import SearchService
from app.services.page_fetcher import PageFetcher


def mock_gemini_generate(prompt, response_schema):

    schema_name = response_schema.__name__

    if schema_name == "ClaimParseResult":
        return """
        {
            "elements": [
                {
                    "id": "1.1",
                    "claim_number": "1",
                    "text": "a processor configured to receive image data"
                }
            ]
        }
        """

    if schema_name == "TechnologyProfile":
        return """
        {
            "claim_element_id": "1.1",
            "target": {
                "company": "Samsung",
                "product": "Galaxy S26 Ultra",
                "technology": null
            },
            "core_concept": "Processor receiving image data",
            "technical_concepts": [
                "image data ingestion",
                "camera interface",
                "image signal processing"
            ],
            "alternative_terminology": [
                "image signal processor",
                "ISP",
                "camera interface controller"
            ],
            "likely_components": [
                "processor",
                "image signal processor",
                "camera interface controller"
            ],
            "implementation_hypotheses": [
                "The target may use a processor or ISP to receive image data from a camera subsystem."
            ]
        }
        """

    if schema_name == "SearchPlan":
        return """
        {
            "claim_element_id": "1.1",
            "queries": [
                {
                    "query": "Samsung Galaxy S26 Ultra processor image data camera ISP",
                    "rationale": "Find product-specific evidence concerning image data processing.",
                    "priority": 1
                },
                {
                    "query": "Samsung Galaxy S26 Ultra image signal processor camera",
                    "rationale": "Find evidence concerning the target's image signal processing architecture.",
                    "priority": 2
                }
            ],
            "preferred_sources": [
                "samsung.com",
                "qualcomm.com"
            ],
            "search_strategy": "Search authoritative product and processor sources for evidence concerning image data processing."
        }
        """

    if schema_name == "EvidenceVerificationResult":
        return """
        {
            "claim_element_id": "1.1",
            "evidence_supported": false,
            "confidence": 0.90,
            "reasoning": "The available excerpt does not explicitly establish that a processor is configured to receive image data."
        }
        """

    if schema_name == "ClaimElementMapping":
        return """
        {
            "claim_element_id": "1.1",
            "supported": false,
            "confidence": 0.0,
            "evidence": [],
            "reasoning": "No verified evidence supports this claim element."
        }
        """

    if schema_name == "Evidence":
        return """
        {
            "claim_element_id": "1.1",
            "source_title": "Mock Source",
            "url": "https://example.com",
            "excerpt": "Mock evidence excerpt.",
            "evidence_type": "direct",
            "relevance": "Mock evidence."
        }
        """

    raise ValueError(
        f"Unexpected response schema: {schema_name}"
    )


claim = Claim(
    claim_number="1",
    text=(
        "A device comprising a processor configured to receive "
        "image data."
    ),
)

target = TargetScope(
    company="Samsung",
    product="Galaxy S26 Ultra",
)


print("\n=== CLAIM PARSER ===")

parser = ClaimParser()

parsed_claim = parser.parse(claim)

print(f"Elements found: {len(parsed_claim.elements)}")

for element in parsed_claim.elements:
    print(f"- {element.id}: {element.text}")

element = parsed_claim.elements[0]


print("\n=== TECHNOLOGY PROFILER ===")

profiler = TechnologyProfiler()

technology_profile = profiler.profile(
    element,
    target,
)

print(
    f"Core concept: "
    f"{technology_profile.core_concept}"
)


print("\n=== SEARCH PLANNER ===")

planner = SearchPlanner()

search_plan = planner.plan(
    element,
    target,
    technology_profile,
)

print(
    f"Queries generated: "
    f"{len(search_plan.queries)}"
)

for query in search_plan.queries:
    print(
        f"- [{query.priority}] "
        f"{query.query}"
    )


print("\n=== SEARCH SERVICE ===")

search_service = SearchService()

all_search_results = []

for query in search_plan.queries[:2]:

    results = search_service.search(query)

    print(
        f"\nQuery: {query.query}"
        f"\nResults: {len(results)}"
    )

    all_search_results.extend(results)


print(
    f"\nTotal search results collected: "
    f"{len(all_search_results)}"
)


print("\n=== PAGE FETCH + EVIDENCE EXTRACTION ===")

fetcher = PageFetcher()
extractor = EvidenceExtractor()

potential_evidence = []

for search_result in all_search_results[:5]:

    try:

        page_content = fetcher.fetch(
            search_result
        )

        evidence = extractor.extract(
            element,
            search_result,
            page_content,
        )

        if evidence:

            potential_evidence.extend(
                evidence
            )

            print(
                f"\nEvidence found: "
                f"{search_result.title}"
            )

    except Exception as exc:

        print(
            f"\nSkipping source: "
            f"{search_result.url}"
        )

        print(
            f"Reason: {exc}"
        )


print(
    f"\nPotential evidence findings: "
    f"{len(potential_evidence)}"
)


print("\n=== EVIDENCE VERIFICATION ===")

verifier = EvidenceVerifier()

verified_evidence = []

for evidence in potential_evidence:

    verification = verifier.verify(
        element,
        evidence,
    )

    print(
        f"\nSource: "
        f"{evidence.source_title}"
    )

    print(
        f"Supported: "
        f"{verification.evidence_supported}"
    )

    print(
        f"Confidence: "
        f"{verification.confidence}"
    )

    if verification.evidence_supported:

        verified_evidence.append(
            VerifiedEvidence(
                evidence=evidence,
                verification=verification,
            )
        )


print(
    f"\nVerified evidence: "
    f"{len(verified_evidence)}"
)


print("\n=== CLAIM MAPPING ===")

mapper = ClaimMapper()

mapping = mapper.map(
    element,
    verified_evidence,
)


print(
    f"Supported: "
    f"{mapping.supported}"
)

print(
    f"Confidence: "
    f"{mapping.confidence}"
)

print(
    f"Evidence count: "
    f"{len(mapping.evidence)}"
)

print(
    f"Reasoning: "
    f"{mapping.reasoning}"
)


print("\n=== CLAIM ANALYSIS ===")

analyzer = ClaimAnalyzer()

analysis = analyzer.analyze(
    claim,
    [mapping],
)


print(
    f"Claim: "
    f"{analysis.claim_number}"
)

print(
    f"Coverage status: "
    f"{analysis.coverage_status}"
)

print(
    f"Confidence: "
    f"{analysis.confidence}"
)

print(
    f"Reasoning: "
    f"{analysis.reasoning}"
)
