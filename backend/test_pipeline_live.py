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


# ==========================================================
# CLAIM
# ==========================================================

claim = Claim(
    claim_number="1",
    text=(
        "An Access Point (AP) operating in a Wireless Local "
        "Area Network (WLAN), wherein the AP is to initiate "
        "an uplink (UL) multi-user (MU) simultaneous "
        "transmission, the access point comprising a set of "
        "one or more processors and a memory device, with "
        "instructions causing the AP to generate a first "
        "trigger frame that initiates the UL MU simultaneous "
        "transmission, where the trigger frame includes "
        "common and STA-specific attribute fields, the common "
        "attributes field includes a cascade trigger subfield "
        "indicating whether a second trigger frame is "
        "scheduled, and the AP transmits the first trigger "
        "frame through a wireless medium."
    ),
)


# ==========================================================
# TARGET
# ==========================================================

target = TargetScope(
    company="Qualcomm",
    product="FastConnect 6900",
    technology="Wi-Fi 6E, MU-MIMO, OFDMA",
)


# ==========================================================
# CLAIM PARSER
# ==========================================================

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


# ==========================================================
# TECHNOLOGY PROFILER
# ==========================================================

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


# ==========================================================
# SEARCH PLANNER
# ==========================================================

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


# ==========================================================
# SEARCH SERVICE
# ==========================================================

print("\n=== SEARCH SERVICE ===")

search_service = SearchService()

search_results_by_element = {}

total_unique_results = 0

for search_plan in search_plans:

    element_results = []

    seen_urls = set()

    print(
        f"\nSearching all planned queries "
        f"for element "
        f"{search_plan.claim_element_id}"
    )

    for query in search_plan.queries:

        try:

            results = search_service.search(
                query
            )

        except Exception as exc:

            print(
                f"\nQuery failed: "
                f"{query.query}"
            )

            print(
                f"Reason: {exc}"
            )

            continue

        print(
            f"\nQuery: "
            f"{query.query}"
        )

        print(
            f"Priority: "
            f"{query.priority}"
        )

        print(
            f"Eligible results returned: "
            f"{len(results)}"
        )

        for result in results:

            normalized_url = (
                str(result.url)
                .lower()
                .rstrip("/")
            )

            if normalized_url in seen_urls:
                continue

            seen_urls.add(
                normalized_url
            )

            element_results.append(
                result
            )

    search_results_by_element[
        search_plan.claim_element_id
    ] = element_results

    print(
        f"\nUnique eligible search results "
        f"for element "
        f"{search_plan.claim_element_id}: "
        f"{len(element_results)}"
    )

    total_unique_results += (
        len(element_results)
    )


print(
    f"\nTotal unique eligible search results "
    f"collected: "
    f"{total_unique_results}"
)


# ==========================================================
# PAGE FETCH + CONTENT REDUCTION
# ==========================================================

print(
    "\n=== PAGE FETCH + CONTENT REDUCTION ==="
)

fetcher = PageFetcher()
reducer = PageContentReducer()

sources_by_element = {}

for element in claim_elements:

    technology_profile = (
        profiles_by_id[
            element.id
        ]
    )

    search_results = (
        search_results_by_element.get(
            element.id,
            [],
        )
    )

    sources_for_extraction = []

    for search_result in search_results[:5]:

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

        except Exception as exc:

            print(
                f"\nSkipping source: "
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


# ==========================================================
# BATCH EVIDENCE EXTRACTION
# ==========================================================

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
        search_result,
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
                f"{search_result.title}"
            )

        else:

            print(
                f"\nNo evidence found: "
                f"{search_result.title}"
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


# ==========================================================
# BATCH EVIDENCE VERIFICATION
# ==========================================================

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


# ==========================================================
# CLAIM MAPPING
# ==========================================================

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


# ==========================================================
# CLAIM ANALYSIS
# ==========================================================

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
