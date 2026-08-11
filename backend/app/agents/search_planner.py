from app.models.schemas import (
    ClaimElement,
    TargetScope,
    TechnologyProfile,
    SearchPlan,
    SearchPlanBatchResult,
)
from app.services.gemini_service import GeminiService


class SearchPlanner:

    def __init__(self):
        self.llm = GeminiService()

    # ============================================================
    # SINGLE ELEMENT
    # ============================================================

    def plan(
        self,
        claim_element: ClaimElement,
        target: TargetScope,
        technology_profile: TechnologyProfile,
    ) -> SearchPlan:

        prompt = f"""
You are a search strategy specialist supporting real-world
technical evidence discovery for patent claim analysis.

Your task is to create a HIGH-RECALL, technically focused web
search plan for ONE patent claim element and a specified target.

The objective is to discover PUBLIC TECHNICAL EVIDENCE showing
how a real product, system, component, protocol, architecture,
or implementation works.

The search is NOT intended to find patents.

The most important objective is NOT merely to find pages that
mention the same technology.

The objective is to find evidence for the ACTUAL TECHNICAL
LIMITATIONS and RELATIONSHIPS contained in the claim element.


============================================================
CORE SEARCH PHILOSOPHY
============================================================

Do not simply search the claim wording repeatedly.

Translate the claim element into multiple technical discovery
paths.

Use this progression:

PATENT LANGUAGE
        ↓
TECHNICAL LIMITATIONS
        ↓
TECHNICAL RELATIONSHIPS
        ↓
INDUSTRY TERMINOLOGY
        ↓
PRODUCT / IMPLEMENTATION TERMINOLOGY
        ↓
PUBLIC TECHNICAL EVIDENCE


============================================================
STEP 1 — DECOMPOSE THE ELEMENT INTERNALLY
============================================================

Before generating queries, identify the meaningful technical
parts of the claim element.

Look for:

- components;
- structures;
- operations;
- inputs;
- outputs;
- conditions;
- decisions;
- relationships;
- causal relationships;
- sequencing;
- functional interactions;
- configuration;
- data flow;
- control flow.

Do NOT create separate SearchPlan objects for these pieces.

Instead, use the pieces to create complementary searches
within this one SearchPlan.


============================================================
SEARCH COVERAGE REQUIREMENT
============================================================

The generated queries should collectively cover:

1. the CORE technical concept;

2. the most DISTINCTIVE technical limitation;

3. the most important TECHNICAL RELATIONSHIP;

4. relevant INDUSTRY TERMINOLOGY;

5. a TARGET / PRODUCT implementation path when useful.

Do NOT allow every query to focus on the broad technology.

The distinctive limitations and relationships are usually more
valuable than generic technology references.


============================================================
PRIORITY 1 — DISTINCTIVE CLAIM LIMITATION
============================================================

At least one query MUST have priority 1.

Priority 1 should target the most technically distinctive
limitation or relationship in the claim element.

Prefer:

- unusual operations;
- specific conditions;
- specific data relationships;
- specific control behavior;
- specific routing behavior;
- specific interactions;
- distinctive functional combinations.

Do NOT make priority 1 merely a generic technology search.

BAD:

"network edge system"

BETTER:

"traffic classification criteria routing specialized network edge"

The query should maximize the chance of finding evidence for the
actual distinguishing feature.


============================================================
PRIORITY 2 — TECHNICAL RELATIONSHIP / FUNCTION
============================================================

At least one query MUST have priority 2.

Focus on an important relationship or functional behavior.

Examples:

- receiving X and using X to determine Y;
- determining whether X satisfies criteria;
- routing X in response to Y;
- writing X to Y;
- controlling X based on Y;
- selecting X based on Z;
- communicating X between components.

The goal is to find documentation that describes HOW the system
behaves rather than merely WHAT components exist.


============================================================
PRIORITY 3 — INDUSTRY TERMINOLOGY
============================================================

Use priority 3 for terminology expansion.

Use:

- alternative terminology;
- engineering terminology;
- industry vocabulary;
- functional equivalents;
- implementation terminology.

The query should provide a genuinely different terminology path.

Do NOT simply reorder the same words.


============================================================
PRIORITY 4 — TARGET / PRODUCT IMPLEMENTATION
============================================================

Where target information is available, use a target/product
search.

Combine:

- company;
- product;
- platform;
- technology;

with a meaningful technical limitation or relationship.

The purpose is to locate target-specific technical evidence.

This is INVESTIGATIVE ONLY.

Do not assume the target implements the feature.


============================================================
PRIORITY 5 — COMPONENT / ARCHITECTURE
============================================================

Where useful, search for likely implementation locations,
components, subsystems, protocols, or architecture.

Examples:

- controller;
- gateway;
- routing module;
- protocol layer;
- communication subsystem;
- service;
- API;
- hardware component.

Only use these when they provide a plausible path toward the
actual claimed functionality.

Do NOT turn a component hypothesis into an assumed target fact.


============================================================
PRIORITY 5 — DISTINCTIVE COMBINATION
============================================================

Where useful, create a search using two or more distinctive
technical concepts together.

The purpose is to find the technical fingerprint of the claim
rather than generic technology pages.

For example:

"traffic classification" + "specialized edge routing"

is more useful than:

"network traffic"


============================================================
SEARCH DIVERSITY
============================================================

Queries MUST represent meaningfully different discovery paths.

BAD:

1. "Bluetooth GATT characteristic value"
2. "GATT characteristic value Bluetooth"
3. "Bluetooth characteristic value GATT"

These are effectively the same search.

GOOD:

1. distinctive claim limitation;
2. technical relationship;
3. industry terminology;
4. target/product implementation;
5. architecture or distinctive combination.

Do not generate multiple queries that would likely return the
same pages.


============================================================
TARGET INFORMATION
============================================================

Company:
{target.company}

Product:
{target.product}

Technology:
{target.technology}

Use target information when available.

If a target field is missing, do not invent it.

Target-specific queries are investigative only.

Never state or assume that the target implements the claimed
feature merely because it is being searched.


============================================================
TECHNOLOGY PROFILE
============================================================

Core concept:
{technology_profile.core_concept}

Technical concepts:
{technology_profile.technical_concepts}

Alternative terminology:
{technology_profile.alternative_terminology}

Likely components:
{technology_profile.likely_components}

Implementation hypotheses:
{technology_profile.implementation_hypotheses}


============================================================
IMPLEMENTATION HYPOTHESES
============================================================

Implementation hypotheses may be used to generate exploratory
queries.

They are NOT established facts.

Example:

Hypothesis:
"The functionality may reside in a network edge controller."

Acceptable:

"[target] network edge controller traffic classification"

Not acceptable:

"The target uses a network edge controller."


============================================================
SOURCE DISCOVERY
============================================================

Design queries to discover:

- official manufacturer documentation;
- product documentation;
- developer documentation;
- technical specifications;
- engineering manuals;
- component documentation;
- standards;
- regulatory filings;
- technical support documentation;
- reputable technical publications;
- product architecture documentation;
- implementation guides;
- API documentation;
- configuration documentation.

Prefer sources that can describe actual implementation behavior.


============================================================
SITE-RESTRICTED SEARCHES
============================================================

Where a clearly authoritative domain is relevant, a site-restricted
query may be useful.

Examples:

site:developer.android.com

site:learn.microsoft.com

site:cisco.com

Only use site restrictions when genuinely relevant.

Do not invent domains.


============================================================
QUERY CONSTRUCTION
============================================================

Queries should generally be concise and technically meaningful.

Prefer:

- distinctive technical phrases;
- technical relationships;
- functional behavior;
- implementation terminology;
- product terminology;
- component relationships.

Avoid:

- generic nouns;
- complete copies of the claim;
- excessive legal language;
- excessive quotation marks;
- unsupported implementation assumptions;
- extremely long queries;
- repeated queries with minor word changes.

Use quotation marks selectively for distinctive phrases.


============================================================
PATENTS
============================================================

Do NOT intentionally search for patents.

Do NOT include patent databases as preferred sources.

The objective is public real-world technical evidence.

Patent results will also be filtered by the search service.


============================================================
NUMBER OF QUERIES
============================================================

Generate approximately 4–6 queries.

For a simple claim element:

3–4 strong queries may be sufficient.

For a complex claim element:

5–6 complementary queries are preferred.

Do NOT generate additional queries merely to reach the number.

Every query must have a distinct investigative purpose.


============================================================
QUERY PRIORITY
============================================================

Priority meaning:

1 = most distinctive claim limitation

2 = important technical relationship / function

3 = terminology / concept expansion

4 = target / product implementation

5 = architecture / component / exploratory combination

Priority is an investigative ranking.

It is NOT a confidence score.


============================================================
RATIONALE
============================================================

Every query must have a concise rationale explaining:

1. what technical limitation, relationship, or concept the query
   targets; and

2. why this search path could find real-world technical evidence.

For target-specific or implementation-hypothesis searches,
explicitly identify the search as investigative.


============================================================
IMPORTANT SEARCH PRINCIPLE
============================================================

Do NOT spend all queries searching for the broad technology.

For example, if the element is:

"receiving traffic information and, in response to determining
that the traffic satisfies criteria, routing the traffic through
a specialized network edge system"

do NOT generate:

- network traffic;
- network edge system;
- traffic routing;
- communication network.

Those searches are too broad.

Instead search for the distinctive relationships:

- traffic information used to determine eligibility;
- traffic classification based on criteria;
- qualifying traffic routed to a specialized edge;
- traffic steering based on classification;
- target implementation of conditional traffic routing.

The goal is to find the technical mechanism behind the claim,
not merely pages discussing the technology.


============================================================
FINAL SELF-CHECK
============================================================

Before returning the search plan, verify:

1. Is there at least one priority-1 query?

2. Does priority 1 target a distinctive claim limitation?

3. Is there at least one priority-2 query?

4. Does priority 2 target an important technical relationship?

5. Does at least one query use alternative industry terminology?

6. If target information is available, does at least one query
   investigate the target/product?

7. Are the queries genuinely different?

8. Do the queries collectively cover the important limitations
   of the claim element?

9. Did I avoid spending all queries on the broad technology?

10. Did I avoid treating implementation hypotheses as facts?

11. Are the queries suitable for finding public technical
    documentation?

12. Did I avoid intentionally searching patent databases?

13. Does every query have a clear rationale?

14. Could each query plausibly retrieve a DIFFERENT class of
    useful evidence?


============================================================
CLAIM ELEMENT
============================================================

ID:
{claim_element.id}

TEXT:
{claim_element.text}


Return only the requested structured output.
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=SearchPlan,
        )

        parsed = SearchPlan.model_validate_json(
            result
        )

        self._validate_plan(
            parsed,
            claim_element.id,
        )

        return parsed

    # ============================================================
    # BATCH
    # ============================================================

    def plan_batch(
        self,
        claim_elements: list[ClaimElement],
        target: TargetScope,
        technology_profiles: list[TechnologyProfile],
    ) -> list[SearchPlan]:

        if not claim_elements:
            return []

        expected_element_ids = {
            element.id
            for element in claim_elements
        }

        profile_ids = {
            profile.claim_element_id
            for profile in technology_profiles
        }

        if profile_ids != expected_element_ids:
            raise ValueError(
                "Technology profiles do not match "
                "claim element IDs."
            )

        if len(technology_profiles) != len(
            claim_elements
        ):
            raise ValueError(
                "Technology profiles do not match "
                "claim element IDs."
            )

        profiles_by_id = {
            profile.claim_element_id: profile
            for profile in technology_profiles
        }

        element_sections = []

        for element in claim_elements:

            profile = profiles_by_id[
                element.id
            ]

            element_sections.append(
                f"""
CLAIM ELEMENT ID:
{element.id}

CLAIM ELEMENT TEXT:
{element.text}

TECHNOLOGY PROFILE:

Core concept:
{profile.core_concept}

Technical concepts:
{profile.technical_concepts}

Alternative terminology:
{profile.alternative_terminology}

Likely components:
{profile.likely_components}

Implementation hypotheses:
{profile.implementation_hypotheses}
""".strip()
            )

        prompt = f"""
You are a search strategy specialist supporting real-world
technical evidence discovery for patent claim analysis.

Create targeted web search plans for MULTIPLE patent claim
elements.

Produce exactly one independent search plan for every claim
element provided.

The objective is to discover PUBLIC TECHNICAL EVIDENCE showing
how a real product, system, component, protocol, architecture,
or implementation works.

Do NOT optimize for finding patents.


============================================================
CORE SEARCH PHILOSOPHY
============================================================

Do not simply repeat claim language.

For EACH claim element:

1. identify its meaningful technical limitations;

2. identify its most distinctive limitation;

3. identify important technical relationships;

4. identify industry terminology;

5. identify target/product implementation paths;

6. create complementary searches covering those paths.

The queries should collectively investigate the technical
mechanism behind the claim element.


============================================================
SEARCH COVERAGE
============================================================

Each claim element should generally contain:

Priority 1:
Most distinctive technical limitation.

Priority 2:
Important technical relationship or function.

Priority 3:
Industry terminology / technical concept expansion.

Priority 4:
Target / product implementation.

Priority 5:
Architecture, component, or distinctive combination where
useful.

Do not generate multiple generic technology searches.


============================================================
PRIORITY 1
============================================================

Every claim element MUST have at least one priority-1 query.

Priority 1 must target a distinctive technical limitation or
functional behavior.

It should NOT merely search the broad technology.


============================================================
PRIORITY 2
============================================================

Every claim element MUST have at least one priority-2 query.

Priority 2 should target an important technical relationship,
such as:

- receiving X and using X to determine Y;
- determining whether X satisfies criteria;
- routing X in response to Y;
- controlling X based on Y;
- selecting X based on Z;
- communicating X between components.


============================================================
PRIORITY 3
============================================================

Use priority 3 for alternative terminology and industry
vocabulary.

The terminology search must provide a genuinely different
discovery path.


============================================================
PRIORITY 4
============================================================

Where target information is available, use priority 4 for
target/product implementation investigation.

These searches are investigative only.

Never assume the target implements the claim.


============================================================
PRIORITY 5
============================================================

Where useful, use priority 5 for:

- architecture;
- components;
- subsystems;
- protocols;
- implementation locations;
- distinctive technical combinations.


============================================================
SEARCH DIVERSITY
============================================================

Do not produce reordered versions of the same search.

Bad:

"BLE GATT characteristic value"

"GATT characteristic value BLE"

"Bluetooth GATT characteristic value"

Good:

1. distinctive limitation;
2. technical relationship;
3. terminology expansion;
4. target implementation;
5. architecture or technical combination.


============================================================
TARGET
============================================================

Company:
{target.company}

Product:
{target.product}

Technology:
{target.technology}

Use only the target information provided.

Never invent missing target information.


============================================================
SOURCE ORIENTATION
============================================================

Design searches to find:

- official manufacturer documentation;
- product documentation;
- developer documentation;
- engineering manuals;
- technical specifications;
- component manufacturer documentation;
- standards;
- regulatory filings;
- technical support documentation;
- reputable technical publications;
- implementation guides;
- API documentation;
- configuration documentation.


============================================================
IMPLEMENTATION HYPOTHESES
============================================================

Implementation hypotheses may be used as exploratory search
paths.

They are NOT established facts.

If used, the query rationale should identify them as
investigative possibilities.


============================================================
PATENTS
============================================================

Do not intentionally search for patents.

Do not include patent databases as preferred sources.

The goal is public technical evidence.


============================================================
QUERY RULES
============================================================

Each claim element should generally receive 4–6 queries.

Queries must be:

- technically meaningful;
- concise;
- complementary;
- suitable for web search;
- grounded in the claim or technology profile.

Avoid:

- generic searches;
- complete claim copies;
- excessive legal language;
- excessive quotation marks;
- unsupported assumptions;
- repetitive searches.


============================================================
RATIONALE
============================================================

Every query requires a concise rationale explaining:

1. what technical limitation or relationship it searches; and

2. why that path could discover relevant public technical evidence.

For target or implementation searches, make clear that the
search is investigative.


============================================================
OUTPUT REQUIREMENTS
============================================================

For EVERY claim element:

1. Return exactly one search plan.

2. Preserve the exact claim element ID.

3. Include at least one priority-1 query.

4. Include at least one priority-2 query.

5. Use priority 3 for terminology expansion.

6. Use priority 4 for target/product investigation where useful.

7. Use priority 5 for architecture/component/combination
   investigation where useful.

8. Do not make generic technology searches the majority of the
   plan.

9. Do not create priority-1 or priority-2 searches whose main
   basis is an unconfirmed implementation hypothesis.

10. Do not omit claim elements.

11. Do not create plans for unknown IDs.

12. Queries must be meaningfully different.

13. Every query must have a rationale.

14. Return only the requested structured output.


============================================================
TARGET
============================================================

Company:
{target.company}

Product:
{target.product}

Technology:
{target.technology}


============================================================
CLAIM ELEMENTS AND TECHNOLOGY PROFILES
============================================================

{chr(10).join(element_sections)}


Return only the requested structured output.
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=SearchPlanBatchResult,
        )

        parsed = (
            SearchPlanBatchResult
            .model_validate_json(result)
        )

        actual_ids = [
            plan.claim_element_id
            for plan in parsed.results
        ]

        actual_id_set = set(
            actual_ids
        )

        if actual_id_set != expected_element_ids:
            raise ValueError(
                "Search plan batch returned "
                "invalid claim element IDs."
            )

        if len(actual_ids) != len(
            expected_element_ids
        ):
            raise ValueError(
                "Search plan batch returned "
                "duplicate claim element IDs."
            )

        for plan in parsed.results:

            self._validate_plan(
                plan,
                plan.claim_element_id,
            )

        plans_by_id = {
            plan.claim_element_id: plan
            for plan in parsed.results
        }

        return [
            plans_by_id[element.id]
            for element in claim_elements
        ]

    # ============================================================
    # VALIDATION
    # ============================================================

    def _validate_plan(
        self,
        plan: SearchPlan,
        claim_element_id: str,
    ) -> None:

        if (
            plan.claim_element_id
            != claim_element_id
        ):
            raise ValueError(
                f"Search plan returned invalid "
                f"claim element ID: "
                f"{plan.claim_element_id}"
            )

        if not plan.queries:
            raise ValueError(
                f"Search plan for claim element "
                f"{claim_element_id} contains no queries."
            )

        priorities = [
            query.priority
            for query in plan.queries
        ]

        # --------------------------------------------------------
        # Mandatory distinctive limitation search.
        # --------------------------------------------------------

        if 1 not in priorities:
            raise ValueError(
                f"Search plan for claim element "
                f"{claim_element_id} must contain "
                "at least one priority-1 query."
            )

        # --------------------------------------------------------
        # Mandatory relationship/function search.
        # --------------------------------------------------------

        if 2 not in priorities:
            raise ValueError(
                f"Search plan for claim element "
                f"{claim_element_id} must contain "
                "at least one priority-2 query."
            )

        # --------------------------------------------------------
        # Validate individual queries.
        # --------------------------------------------------------

        for query in plan.queries:

            if query.priority < 1:
                raise ValueError(
                    f"Invalid search priority "
                    f"{query.priority} for claim element "
                    f"{claim_element_id}."
                )

            if query.priority > 5:
                raise ValueError(
                    f"Invalid search priority "
                    f"{query.priority} for claim element "
                    f"{claim_element_id}."
                )

            if not query.query.strip():
                raise ValueError(
                    f"Empty search query for claim element "
                    f"{claim_element_id}."
                )

            if not query.rationale.strip():
                raise ValueError(
                    f"Search query has no rationale for "
                    f"claim element {claim_element_id}."
                )

        # --------------------------------------------------------
        # Query count guard.
        #
        # We do not require exactly 4–6 because a simple element
        # can legitimately need fewer searches.
        # --------------------------------------------------------

        if len(plan.queries) > 6:
            raise ValueError(
                f"Search plan for claim element "
                f"{claim_element_id} contains too many queries."
            )
