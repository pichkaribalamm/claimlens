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


claim_elements = parsed_claim.elements


print("\n=== TECHNOLOGY PROFILER ===")


profiler = TechnologyProfiler()


technology_profiles = profiler.profile_batch(
    claim_elements,
    target,
)


print(
    f"Profiles generated: "
    f"{len(technology_profiles)}"
)


for profile in technology_profiles:

    print(
        f"- {profile.claim_element_id}: "
        f"{profile.core_concept}"
    )


profiles_by_id = {
    profile.claim_element_id: profile
    for profile in technology_profiles
}


print("\n=== SEARCH PLANNER ===")


planner = SearchPlanner()


search_plans = planner.plan_batch(
    claim_elements,
    target,
    technology_profiles,
)


print(
    f"Search plans generated: "
    f"{len(search_plans)}"
)


for search_plan in search_plans:

    print(
        f"\nClaim element: "
        f"{search_plan.claim_element_id}"
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


for search_plan in search_plans:

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


element = claim_elements[0]


technology_profile = profiles_by_id[
    element.id
]


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
