import json
import os
import re
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
from app.services.page_content_reducer import PageContentReducer


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

    if schema_name == "EvidenceExtractionBatchResult":

        source_pattern = re.compile(
            r"SOURCE INDEX:\s*(\d+)\s*"
            r"TITLE:\s*(.*?)\s*"
            r"URL:\s*(.*?)\s*"
            r"RELEVANT PAGE CONTENT:",
            re.DOTALL,
        )

        sources = source_pattern.findall(prompt)

        results = []

        for index, title, url in sources:

            index = int(index)
            title = title.strip()
            url = url.strip()

            results.append(
                {
                    "source_index": index,
                    "evidence": [
                        {
                            "claim_element_id": "1.1",
                            "source_title": title,
                            "url": url,
                            "excerpt": (
                                "The processor receives image data "
                                "from the camera system."
                            ),
                            "evidence_type": "direct",
                            "relevance": (
                                "The source explicitly describes "
                                "a processor receiving image data "
                                "from the camera system."
                            ),
                        }
                    ],
                }
            )

        return json.dumps(
            {
                "results": results,
            }
        )

    if schema_name == "EvidenceVerificationBatchResult":

        evidence_indexes = [
            int(index)
            for index in re.findall(
                r"EVIDENCE INDEX:\s*(\d+)",
                prompt,
            )
        ]

        results = []

        for index in evidence_indexes:

            results.append(
                {
                    "evidence_index": index,
                    "evidence_supported": False,
                    "confidence": 0.90,
                    "reasoning": (
                        "The available excerpt identifies a processor "
                        "receiving image data, but the excerpt does "
                        "not establish all limitations necessary to "
                        "support the complete claim element."
                    ),
                }
            )

        return json.dumps(
            {
                "results": results,
            }
        )

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

    raise ValueError(
        f"Unexpected response schema: {schema_name}"
    )


with patch(
    "app.services.gemini_service.GeminiService.generate",
    side_effect=mock_gemini_generate,
):

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

    print(
        f"Elements found: "
        f"{len(parsed_claim.elements)}"
    )

    for element in parsed_claim.elements:
        print(
            f"- {element.id}: "
            f"{element.text}"
        )

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

    print(
        "\n=== PAGE FETCH + CONTENT REDUCTION ==="
    )

    fetcher = PageFetcher()
    reducer = PageContentReducer()
    extractor = EvidenceExtractor()

    sources_for_extraction = []

    for search_result in all_search_results[:5]:

        try:

            page_content = fetcher.fetch(
                search_result
            )

            reduced_content = reducer.reduce(
                element,
                page_content,
                technology_profile,
            )

            if not reduced_content:

                print(
                    f"\nSkipping source: "
                    f"{search_result.url}"
                )

                print(
                    "Reason: No relevant page content found."
                )

                continue

            sources_for_extraction.append(
                (
                    search_result,
                    reduced_content,
                )
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
        f"\nSources prepared for extraction: "
        f"{len(sources_for_extraction)}"
    )

    print(
        "\n=== BATCH EVIDENCE EXTRACTION ==="
    )

    extraction_results = extractor.extract_batch(
        element,
        sources_for_extraction,
    )

    potential_evidence = []

    for search_result, evidence_list in zip(
        (
            source
            for source, _ in sources_for_extraction
        ),
        extraction_results,
    ):

        if evidence_list:

            potential_evidence.extend(
                evidence_list
            )

            print(
                f"\nEvidence found: "
                f"{search_result.title}"
            )

        else:

            print(
                f"\nNo evidence found: "
                f"{search_result.title}"
            )

    print(
        f"\nPotential evidence findings: "
        f"{len(potential_evidence)}"
    )

    print("\n=== BATCH EVIDENCE VERIFICATION ===")

    verifier = EvidenceVerifier()

    verified_evidence = []

    verification_results = verifier.verify_batch(
        element,
        potential_evidence,
    )

    for evidence, verification in zip(
        potential_evidence,
        verification_results,
    ):

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
