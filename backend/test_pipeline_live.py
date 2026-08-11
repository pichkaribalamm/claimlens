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
        "A method of routing network traffic through a "
        "specialized network edge system for a communication "
        "network, the method comprising: "
        "in an edge system controller within the communication "
        "network: identifying criteria indicating whether "
        "certain network traffic should be handled by the "
        "specialized network edge system; "
        "receiving, from a first network edge system for the "
        "communication network, first information about first "
        "network traffic entering the communication network "
        "through the first network edge system from outside "
        "the communication network; and "
        "in response to determining, based on the first "
        "information, that the first network traffic satisfies "
        "the criteria, routing the first network traffic "
        "through the specialized network edge system."
    ),
)


# ============================================================
# TARGET
# ============================================================

target = TargetScope(
    company="Nokia",
    product="Cloud",
    technology=(
        "edge networking, traffic routing, "
        "edge controller"
    ),
)


# ============================================================
# CLAIM PARSER
# ============================================================

print("\n" + "=" * 70)
print("CLAIM PARSER")
print("=" * 70)

parser = ClaimParser()

parsed_claim = parser.parse(
    claim
)

claim_elements = parsed_claim.elements

print(
    f"\nElements found: "
    f"{len(claim_elements)}"
)

for element in claim_elements:

    print(
        f"\n[{element.id}] "
        f"{element.text}"
    )


# ============================================================
# TECHNOLOGY PROFILER
# ============================================================

print("\n" + "=" * 70)
print("TECHNOLOGY PROFILER")
print("=" * 70)

profiler = TechnologyProfiler()

technology_profiles = profiler.profile_batch(
    claim_elements,
    target,
)

print(
    f"\nProfiles generated: "
    f"{len(technology_profiles)}"
)

profiles_by_id = {
    profile.claim_element_id: profile
    for profile in technology_profiles
}

for profile in technology_profiles:

    print(
        f"\n[{profile.claim_element_id}] "
        f"{profile.core_concept}"
    )


# ============================================================
# SEARCH PLANNER
# ============================================================

print("\n" + "=" * 70)
print("SEARCH PLANNER")
print("=" * 70)

planner = SearchPlanner()

search_plans = planner.plan_batch(
    claim_elements,
    target,
    technology_profiles,
)

print(
    f"\nSearch plans generated: "
    f"{len(search_plans)}"
)

for search_plan in search_plans:

    print(
        f"\n--- Element "
        f"{search_plan.claim_element_id} ---"
    )

    print(
        f"Queries: "
        f"{len(search_plan.queries)}"
    )

    for query in search_plan.queries:

        print(
            f"[{query.priority}] "
            f"{query.query}"
        )


# ============================================================
# SEARCH SERVICE
# ============================================================

print("\n" + "=" * 70)
print("SEARCH SERVICE")
print("=" * 70)

search_service = SearchService()

search_results_by_element = {}


for search_plan in search_plans:

    element_results = []

    print(
        f"\n--- Element "
        f"{search_plan.claim_element_id} ---"
    )

    for query in search_plan.queries:

        print(
            f"\nQuery: {query.query}"
        )

        try:

            results = search_service.search(
                query
            )

            print(
                f"Results returned: "
                f"{len(results)}"
            )

            element_results.extend(
                results
            )

        except Exception as exc:

            print(
                f"SEARCH FAILED"
            )

            print(
                f"Reason: {exc}"
            )

    # --------------------------------------------------------
    # Deduplicate URLs.
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
        f"\nUnique search results: "
        f"{len(unique_results)}"
    )


total_search_results = sum(
    len(results)
    for results in search_results_by_element.values()
)

print(
    f"\nTOTAL UNIQUE SEARCH RESULTS: "
    f"{total_search_results}"
)


# ============================================================
# SOURCE QUALIFICATION
# ============================================================

print("\n" + "=" * 70)
print("SOURCE QUALIFICATION")
print("=" * 70)

qualifier = SourceQualifier(
    minimum_tier=2
)

qualified_results_by_element = {}

qualification_stats = {
    "total": 0,
    "qualified": 0,
    "rejected": 0,
}


for element in claim_elements:

    search_results = (
        search_results_by_element.get(
            element.id,
            [],
        )
    )

    qualified_results = []

    print(
        f"\n--- Element "
        f"{element.id} ---"
    )

    for result in search_results:

        qualification_stats["total"] += 1

        try:

            qualified = qualifier.qualify(
                result
            )

            tier = qualifier.quality_tier(
                result
            )

            label = qualifier.quality_label(
                result
            )

            if qualified:

                qualification_stats[
                    "qualified"
                ] += 1

                qualified_results.append(
                    result
                )

            else:

                qualification_stats[
                    "rejected"
                ] += 1

            print(
                f"{'KEEP' if qualified else 'REJECT'} "
                f"| {label} "
                f"| {result.title}"
            )

            print(
                f"  {result.url}"
            )

        except Exception as exc:

            qualification_stats[
                "rejected"
            ] += 1

            print(
                f"QUALIFICATION ERROR "
                f"| {result.url}"
            )

            print(
                f"  Reason: {exc}"
            )

    qualified_results_by_element[
        element.id
    ] = qualified_results

    print(
        f"\nQualified for element "
        f"{element.id}: "
        f"{len(qualified_results)}"
    )


print(
    f"\nQUALIFICATION SUMMARY"
)

print(
    f"Search results: "
    f"{qualification_stats['total']}"
)

print(
    f"Qualified: "
    f"{qualification_stats['qualified']}"
)

print(
    f"Rejected: "
    f"{qualification_stats['rejected']}"
)


# ============================================================
# PAGE FETCH + CONTENT REDUCTION
# ============================================================

print("\n" + "=" * 70)
print("PAGE FETCH + CONTENT REDUCTION")
print("=" * 70)

fetcher = PageFetcher()

reducer = PageContentReducer()

sources_by_element = {}

fetch_stats = {
    "attempted": 0,
    "fetched": 0,
    "failed": 0,
    "reduced": 0,
    "empty_reduction": 0,
}


for element in claim_elements:

    technology_profile = profiles_by_id[
        element.id
    ]

    search_results = (
        qualified_results_by_element.get(
            element.id,
            [],
        )
    )

    sources_for_extraction = []

    print(
        f"\n--- Element "
        f"{element.id} ---"
    )

    for search_result in search_results:

        fetch_stats[
            "attempted"
        ] += 1

        print(
            f"\nFETCHING:"
        )

        print(
            f"{search_result.title}"
        )

        print(
            f"{search_result.url}"
        )

        try:

            page_content = fetcher.fetch(
                search_result
            )

            fetch_stats[
                "fetched"
            ] += 1

            print(
                f"  Fetch: SUCCESS"
            )

            print(
                f"  Page length: "
                f"{len(page_content)}"
            )

            if not page_content:

                fetch_stats[
                    "failed"
                ] += 1

                print(
                    f"  Result: EMPTY PAGE"
                )

                continue

            reduced_content = reducer.reduce(
                element,
                page_content,
                technology_profile,
            )

            if not reduced_content:

                fetch_stats[
                    "empty_reduction"
                ] += 1

                print(
                    f"  Reduction: EMPTY"
                )

                print(
                    f"  Result: SOURCE DROPPED "
                    f"BEFORE EXTRACTION"
                )

                continue

            fetch_stats[
                "reduced"
            ] += 1

            sources_for_extraction.append(
                (
                    search_result,
                    reduced_content,
                )
            )

            print(
                f"  Reduction: SUCCESS"
            )

            print(
                f"  Reduced length: "
                f"{len(reduced_content)}"
            )

            # ------------------------------------------------
            # Show a short preview only.
            #
            # Do NOT dump the entire reducer output.
            # ------------------------------------------------

            preview = (
                reduced_content
                .replace("\n", " ")
                .strip()
            )

            if len(preview) > 300:

                preview = (
                    preview[:300]
                    + "..."
                )

            print(
                f"  Preview: "
                f"{preview}"
            )

        except Exception as exc:

            fetch_stats[
                "failed"
            ] += 1

            print(
                f"  Fetch/Reduction: FAILED"
            )

            print(
                f"  Reason: {exc}"
            )

    sources_by_element[
        element.id
    ] = sources_for_extraction

    print(
        f"\nSources prepared for extraction: "
        f"{len(sources_for_extraction)}"
    )


print(
    f"\nFETCH / REDUCTION SUMMARY"
)

print(
    f"Fetch attempts: "
    f"{fetch_stats['attempted']}"
)

print(
    f"Successful fetches: "
    f"{fetch_stats['fetched']}"
)

print(
    f"Fetch failures: "
    f"{fetch_stats['failed']}"
)

print(
    f"Successful reductions: "
    f"{fetch_stats['reduced']}"
)

print(
    f"Empty reductions: "
    f"{fetch_stats['empty_reduction']}"
)


# ============================================================
# BATCH EVIDENCE EXTRACTION
# ============================================================

print("\n" + "=" * 70)
print("BATCH EVIDENCE EXTRACTION")
print("=" * 70)

extractor = EvidenceExtractor()

potential_evidence_by_element = {}

extraction_stats = {
    "sources_submitted": 0,
    "sources_with_evidence": 0,
    "sources_without_evidence": 0,
    "evidence_items": 0,
}


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
            f"\nElement {element.id}: "
            f"No sources prepared."
        )

        continue

    extraction_stats[
        "sources_submitted"
    ] += len(
        sources_for_extraction
    )

    try:

        extraction_results = (
            extractor.extract_batch(
                element,
                sources_for_extraction,
            )
        )

    except Exception as exc:

        print(
            f"\nEXTRACTION FAILED "
            f"FOR ELEMENT {element.id}"
        )

        print(
            f"Reason: {exc}"
        )

        potential_evidence_by_element[
            element.id
        ] = []

        continue

    potential_evidence = []

    for (
        search_result,
        evidence_list,
    ) in zip(
        (
            source
            for source, _
            in sources_for_extraction
        ),
        extraction_results,
    ):

        if evidence_list:

            extraction_stats[
                "sources_with_evidence"
            ] += 1

            extraction_stats[
                "evidence_items"
            ] += len(
                evidence_list
            )

            potential_evidence.extend(
                evidence_list
            )

            print(
                f"\nEVIDENCE FOUND"
            )

            print(
                f"Source: "
                f"{search_result.title}"
            )

            for index, evidence in enumerate(
                evidence_list,
                start=1,
            ):

                print(
                    f"\n  Evidence {index}"
                )

                print(
                    f"  Type: "
                    f"{evidence.evidence_type}"
                )

                print(
                    f"  Relevance: "
                    f"{evidence.relevance}"
                )

                print(
                    f"  Excerpt: "
                    f"{evidence.excerpt}"
                )

        else:

            extraction_stats[
                "sources_without_evidence"
            ] += 1

            print(
                f"\nNO EVIDENCE"
            )

            print(
                f"Source: "
                f"{search_result.title}"
            )

    potential_evidence_by_element[
        element.id
    ] = potential_evidence

    print(
        f"\nElement {element.id}: "
        f"{len(potential_evidence)} "
        f"potential evidence items"
    )


print(
    f"\nEXTRACTION SUMMARY"
)

print(
    f"Sources submitted: "
    f"{extraction_stats['sources_submitted']}"
)

print(
    f"Sources with evidence: "
    f"{extraction_stats['sources_with_evidence']}"
)

print(
    f"Sources without evidence: "
    f"{extraction_stats['sources_without_evidence']}"
)

print(
    f"Total evidence items: "
    f"{extraction_stats['evidence_items']}"
)


# ============================================================
# BATCH EVIDENCE VERIFICATION
# ============================================================

print("\n" + "=" * 70)
print("BATCH EVIDENCE VERIFICATION")
print("=" * 70)

verifier = EvidenceVerifier()

verified_evidence_by_element = {}

verification_stats = {
    "submitted": 0,
    "direct": 0,
    "supportive": 0,
    "inferential": 0,
    "contextual": 0,
    "unsupported": 0,
}


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
            f"\nElement {element.id}: "
            f"No evidence to verify."
        )

        continue

    verification_stats[
        "submitted"
    ] += len(
        potential_evidence
    )

    try:

        verification_results = (
            verifier.verify_batch(
                element,
                potential_evidence,
            )
        )

    except Exception as exc:

        print(
            f"\nVERIFICATION FAILED "
            f"FOR ELEMENT {element.id}"
        )

        print(
            f"Reason: {exc}"
        )

        verified_evidence_by_element[
            element.id
        ] = []

        continue

    verified_evidence = []

    for evidence, verification in zip(
        potential_evidence,
        verification_results,
    ):

        support_level = (
            verification.support_level
        )

        if support_level in verification_stats:

            verification_stats[
                support_level
            ] += 1

        print(
            f"\nEVIDENCE VERIFICATION"
        )

        print(
            f"Source: "
            f"{evidence.source_title}"
        )

        print(
            f"Support level: "
            f"{support_level}"
        )

        print(
            f"Evidence supported: "
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
        f"\nElement {element.id}: "
        f"{len(verified_evidence)} "
        f"verified evidence items"
    )


print(
    f"\nVERIFICATION SUMMARY"
)

print(
    f"Evidence submitted: "
    f"{verification_stats['submitted']}"
)

print(
    f"Direct: "
    f"{verification_stats['direct']}"
)

print(
    f"Supportive: "
    f"{verification_stats['supportive']}"
)

print(
    f"Inferential: "
    f"{verification_stats['inferential']}"
)

print(
    f"Contextual: "
    f"{verification_stats['contextual']}"
)

print(
    f"Unsupported: "
    f"{verification_stats['unsupported']}"
)

total_verified = (
    verification_stats["direct"]
    + verification_stats["supportive"]
    + verification_stats["inferential"]
)

print(
    f"Retained for mapping: "
    f"{total_verified}"
)


# ============================================================
# CLAIM MAPPING
# ============================================================

print("\n" + "=" * 70)
print("CLAIM MAPPING")
print("=" * 70)

mapper = ClaimMapper()

element_mappings = []

mapping_stats = {
    "supported": 0,
    "unsupported": 0,
}


for element in claim_elements:

    verified_evidence = (
        verified_evidence_by_element.get(
            element.id,
            [],
        )
    )

    print(
        f"\n--- Element {element.id} ---"
    )

    print(
        f"Verified evidence available: "
        f"{len(verified_evidence)}"
    )

    try:

        mapping = mapper.map(
            element,
            verified_evidence,
        )

    except Exception as exc:

        print(
            f"MAPPING FAILED"
        )

        print(
            f"Reason: {exc}"
        )

        raise

    element_mappings.append(
        mapping
    )

    if mapping.supported:

        mapping_stats[
            "supported"
        ] += 1

    else:

        mapping_stats[
            "unsupported"
        ] += 1

    print(
        f"Supported: "
        f"{mapping.supported}"
    )

    print(
        f"Support level: "
        f"{mapping.support_level}"
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
        f"Evidence combinations: "
        f"{len(mapping.evidence_combinations)}"
    )

    print(
        f"Reasoning:"
    )

    print(
        mapping.reasoning
    )


# ============================================================
# CLAIM ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("CLAIM ANALYSIS")
print("=" * 70)

analyzer = ClaimAnalyzer()

analysis = analyzer.analyze(
    claim,
    element_mappings,
)

print(
    f"\nClaim: "
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
    f"\nReasoning:"
)

print(
    analysis.reasoning
)


# ============================================================
# FINAL PIPELINE SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("FINAL PIPELINE SUMMARY")
print("=" * 70)

print(
    f"\nClaim: "
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
    f"{qualification_stats['qualified']}"
)

print(
    f"Successful fetches: "
    f"{fetch_stats['fetched']}"
)

print(
    f"Successful reductions: "
    f"{fetch_stats['reduced']}"
)

print(
    f"Potential evidence: "
    f"{extraction_stats['evidence_items']}"
)

print(
    f"Verified evidence: "
    f"{total_verified}"
)

print(
    f"Supported elements: "
    f"{mapping_stats['supported']}"
)

print(
    f"Unsupported elements: "
    f"{mapping_stats['unsupported']}"
)

print(
    f"FINAL COVERAGE: "
    f"{analysis.coverage_status}"
)

print(
    f"FINAL CONFIDENCE: "
    f"{analysis.confidence}"
)

print("\n" + "=" * 70)
print("PIPELINE COMPLETE")
print("=" * 70)
