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
from app.services.source_qualifier import SourceQualifier


# ============================================================
# TEST CLAIM
# ============================================================

claim = Claim(
    claim_number="1",
    text=(
        "A system comprising a Bluetooth Low Energy device "
        "having a GATT characteristic, wherein the GATT "
        "characteristic is configured to store a characteristic "
        "value and permit a connected device to write the "
        "characteristic value to the GATT characteristic."
    ),
)


# ============================================================
# TARGET
# ============================================================

target = TargetScope(
    company="Android",
    product="BluetoothGatt",
    technology="Bluetooth Low Energy GATT",
)


# ============================================================
# CLAIM PARSER
# ============================================================

print("\n=== CLAIM PARSER ===")

parser = ClaimParser()

parsed_claim = parser.parse(
    claim
)

print(
    f"Elements found: "
    f"{len(parsed_claim.elements)}"
)

for element in parsed_claim.elements:

    print(
        f"- {element.id}: "
        f"{element.text}"
    )

claim_elements = (
    parsed_claim.elements
)


# ============================================================
# TECHNOLOGY PROFILER
# ============================================================

print("\n=== TECHNOLOGY PROFILER ===")

profiler = TechnologyProfiler()

technology_profiles = (
    profiler.profile_batch(
        claim_elements,
        target,
    )
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


# ============================================================
# SEARCH PLANNER
# ============================================================

print("\n=== SEARCH PLANNER ===")

planner = SearchPlanner()

search_plans = (
    planner.plan_batch(
        claim_elements,
        target,
        technology_profiles,
    )
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


# ============================================================
# SEARCH SERVICE
# ============================================================

print("\n=== SEARCH SERVICE ===")

search_service = SearchService()

search_results_by_element = {}


for search_plan in search_plans:

    element_results = []

    print(
        f"\nSearching all planned queries "
        f"for element "
        f"{search_plan.claim_element_id}"
    )

    for query in search_plan.queries:

        print(
            f"\nQuery: "
            f"{query.query}"
        )

        print(
            f"Priority: "
            f"{query.priority}"
        )

        try:

            results = (
                search_service.search(
                    query
                )
            )

            print(
                f"Results: "
                f"{len(results)}"
            )

            element_results.extend(
                results
            )

        except Exception as exc:

            print(
                f"Search failed for query: "
                f"{query.query}"
            )

            print(
                f"Reason: {exc}"
            )

    # --------------------------------------------------------
    # Deduplicate search results.
    # --------------------------------------------------------

    unique_results = []

    seen_urls = set()

    for result in element_results:

        url = str(
            result.url
        ).strip()

        if not url:
            continue

        if url in seen_urls:
            continue

        seen_urls.add(
            url
        )

        unique_results.append(
            result
        )

    search_results_by_element[
        search_plan.claim_element_id
    ] = unique_results

    print(
        f"\nUnique search results for element "
        f"{search_plan.claim_element_id}: "
        f"{len(unique_results)}"
    )


total_search_results = sum(
    len(results)
    for results in (
        search_results_by_element.values()
    )
)

print(
    f"\nTotal unique search results collected: "
    f"{total_search_results}"
)


# ============================================================
# SOURCE QUALIFICATION
# ============================================================

print("\n=== SOURCE QUALIFICATION ===")

qualifier = SourceQualifier(
    minimum_tier=2
)

qualified_results_by_element = {}


for element in claim_elements:

    search_results = (
        search_results_by_element.get(
            element.id,
            [],
        )
    )

    qualified_results = []

    rejected_count = 0

    for search_result in search_results:

        tier = qualifier.quality_tier(
            search_result
        )

        label = qualifier.quality_label(
            search_result
        )

        if qualifier.qualify(
            search_result
        ):

            qualified_results.append(
                search_result
            )

            print(
                f"\nQUALIFIED [{label}] "
                f"{search_result.title}"
            )

            print(
                f"URL: "
                f"{search_result.url}"
            )

        else:

            rejected_count += 1

            print(
                f"\nREJECTED [{label}] "
                f"{search_result.title}"
            )

            print(
                f"URL: "
                f"{search_result.url}"
            )

    qualified_results_by_element[
        element.id
    ] = qualified_results

    print(
        f"\nClaim element {element.id}: "
        f"{len(qualified_results)} "
        f"qualified / "
        f"{rejected_count} rejected"
    )


total_qualified_results = sum(
    len(results)
    for results in (
        qualified_results_by_element.values()
    )
)

print(
    f"\nTotal qualified sources: "
    f"{total_qualified_results}"
)


# ============================================================
# PAGE FETCH + CONTENT REDUCTION
# ============================================================

print(
    "\n=== PAGE FETCH + CONTENT REDUCTION ==="
)

fetcher = PageFetcher()

reducer = PageContentReducer(
    window_size=450,
    max_chars=5000,
    max_passages=6,
)

sources_by_element = {}


for element in claim_elements:

    technology_profile = (
        profiles_by_id[
            element.id
        ]
    )

    search_results = (
        qualified_results_by_element.get(
            element.id,
            [],
        )
    )

    sources_for_extraction = []

    print(
        f"\nProcessing sources for claim "
        f"element {element.id}"
    )

    for search_result in search_results:

        try:

            page_content = fetcher.fetch(
                search_result
            )

            reduced_content = (
                reducer.reduce(
                    element,
                    page_content,
                    technology_profile,
                )
            )

            if not reduced_content:

                print(
                    f"\nSkipping source: "
                    f"{search_result.title}"
                )

                print(
                    f"URL: "
                    f"{search_result.url}"
                )

                print(
                    "Reason: "
                    "No relevant page content found."
                )

                continue

            sources_for_extraction.append(
                (
                    search_result,
                    reduced_content,
                )
            )

            print(
                f"\nSource prepared: "
                f"{search_result.title}"
            )

            print(
                f"URL: "
                f"{search_result.url}"
            )

            print(
                f"Original page content: "
                f"{len(page_content)} chars"
            )

            print(
                f"Reduced content: "
                f"{len(reduced_content)} chars"
            )

        except Exception as exc:

            print(
                f"\nSkipping source: "
                f"{search_result.title}"
            )

            print(
                f"URL: "
                f"{search_result.url}"
            )

            print(
                f"Reason: {exc}"
            )

    sources_by_element[
        element.id
    ] = sources_for_extraction

    print(
        f"\nClaim element {element.id}: "
        f"{len(sources_for_extraction)} "
        f"sources prepared for extraction"
    )


# ============================================================
# BATCH EVIDENCE EXTRACTION
# ============================================================

print(
    "\n=== BATCH EVIDENCE EXTRACTION ==="
)

extractor = EvidenceExtractor()

potential_evidence_by_element = {}


for element in claim_elements:

    sources_for_extraction = (
        sources_by_element.get(
            element.id,
            [],
        )
    )

    if not sources_for_extraction:

        potential_evidence_by_element[
            element.id
        ] = []

        print(
            f"\nClaim element {element.id}: "
            f"No sources prepared for extraction"
        )

        continue

    extraction_results = (
        extractor.extract_batch(
            element,
            sources_for_extraction,
        )
    )

    potential_evidence = []

    for (
        source,
        evidence_list,
    ) in zip(
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
                f"{source.title}"
            )

            for evidence in evidence_list:

                print(
                    "\n--- EXTRACTED EVIDENCE ---"
                )

                print(
                    f"Source: "
                    f"{evidence.source_title}"
                )

                print(
                    f"URL: "
                    f"{evidence.url}"
                )

                print(
                    f"Evidence type: "
                    f"{evidence.evidence_type}"
                )

                print(
                    f"Relevance: "
                    f"{evidence.relevance}"
                )

                print(
                    f"Excerpt length: "
                    f"{len(evidence.excerpt)} chars"
                )

                print(
                    f"Excerpt:\n"
                    f"{evidence.excerpt}"
                )

                print(
                    "--- END EVIDENCE ---"
                )

        else:

            print(
                f"\nNo evidence found: "
                f"{source.title}"
            )

    potential_evidence_by_element[
        element.id
    ] = potential_evidence

    print(
        f"\nClaim element {element.id} "
        f"potential evidence findings: "
        f"{len(potential_evidence)}"
    )


total_potential_evidence = sum(
    len(evidence)
    for evidence in (
        potential_evidence_by_element.values()
    )
)

print(
    f"\nTotal potential evidence findings: "
    f"{total_potential_evidence}"
)


# ============================================================
# BATCH EVIDENCE VERIFICATION
# ============================================================

print(
    "\n=== BATCH EVIDENCE VERIFICATION ==="
)

verifier = EvidenceVerifier()

verified_evidence_by_element = {}


for element in claim_elements:

    potential_evidence = (
        potential_evidence_by_element.get(
            element.id,
            [],
        )
    )

    if not potential_evidence:

        verified_evidence_by_element[
            element.id
        ] = []

        print(
            f"\nClaim element {element.id}: "
            f"No evidence to verify"
        )

        continue

    verification_results = (
        verifier.verify_batch(
            element,
            potential_evidence,
        )
    )

    verified_evidence = []

    for (
        evidence,
        verification,
    ) in zip(
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

        print(
            f"Reasoning: "
            f"{verification.reasoning}"
        )

        if verification.evidence_supported:

            verified_evidence.append(
                VerifiedEvidence(
                    evidence=evidence,
                    verification=verification,
                )
            )

    verified_evidence_by_element[
        element.id
    ] = verified_evidence

    print(
        f"\nClaim element {element.id} "
        f"verified evidence: "
        f"{len(verified_evidence)}"
    )


total_verified_evidence = sum(
    len(evidence)
    for evidence in (
        verified_evidence_by_element.values()
    )
)

print(
    f"\nTotal verified evidence: "
    f"{total_verified_evidence}"
)


# ============================================================
# CLAIM MAPPING
# ============================================================

print("\n=== CLAIM MAPPING ===")

mapper = ClaimMapper()

element_mappings = []


for element in claim_elements:

    verified_evidence = (
        verified_evidence_by_element.get(
            element.id,
            [],
        )
    )

    mapping = mapper.map(
        element,
        verified_evidence,
    )

    element_mappings.append(
        mapping
    )

    print(
        f"\nClaim element: "
        f"{mapping.claim_element_id}"
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


# ============================================================
# CLAIM ANALYSIS
# ============================================================

print("\n=== CLAIM ANALYSIS ===")

analyzer = ClaimAnalyzer()

analysis = analyzer.analyze(
    claim,
    element_mappings,
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


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n=== FINAL SUMMARY ===")

print(
    f"Claim: "
    f"{claim.claim_number}"
)

print(
    f"Claim elements: "
    f"{len(claim_elements)}"
)

print(
    f"Search results: "
    f"{total_search_results}"
)

print(
    f"Qualified sources: "
    f"{total_qualified_results}"
)

print(
    f"Potential evidence: "
    f"{total_potential_evidence}"
)

print(
    f"Verified evidence: "
    f"{total_verified_evidence}"
)

print(
    f"Coverage: "
    f"{analysis.coverage_status}"
)

print(
    f"Confidence: "
    f"{analysis.confidence}"
)
