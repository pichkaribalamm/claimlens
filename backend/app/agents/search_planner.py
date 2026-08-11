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

Your task is to create a high-recall but technically focused
web search plan for ONE claim element and a specified target.

The objective is to discover PUBLIC TECHNICAL EVIDENCE showing
how a real product, system, component, or implementation works.

The search is NOT intended to find patents.


============================================================
CORE SEARCH PRINCIPLE
============================================================

Do not simply search the claim wording repeatedly.

Translate the claim into multiple search approaches that could
lead to the same real-world technical implementation.

A strong search plan should bridge:

PATENT LANGUAGE
        ↓
TECHNICAL CONCEPT
        ↓
INDUSTRY TERMINOLOGY
        ↓
PRODUCT / IMPLEMENTATION TERMINOLOGY
        ↓
PUBLIC TECHNICAL EVIDENCE


============================================================
SEARCH STRATEGIES
============================================================

Use multiple complementary strategies.

------------------------------------------------------------
PRIORITY 1 — CLAIM-SUBSTANCE SEARCH
------------------------------------------------------------

At least one query MUST have priority 1.

The priority-1 query should remain close to the actual technical
substance of the claim element.

Search for the:

- technical relationship;
- operation;
- condition;
- structure;
- input/output;
- causal relationship;
- functional behavior.

Do NOT merely search generic nouns.

For example, if the claim describes:

"routing traffic through a specialized network edge system
in response to determining that traffic satisfies criteria"

a good priority-1 search might focus on:

"traffic routing based on classification through network edge"

rather than:

"network edge system"


------------------------------------------------------------
PRIORITY 2 — INDUSTRY TERMINOLOGY SEARCH
------------------------------------------------------------

At least one query MUST have priority 2.

Use terminology from:

- alternative terminology;
- technical concepts;
- industry vocabulary;
- engineering terminology;
- functional equivalents.

The purpose is to catch sources that describe the same
functionality without using patent terminology.

Do NOT simply repeat the priority-1 query with one word changed.

The priority-2 query should represent a genuinely different
terminology path.


------------------------------------------------------------
PRIORITY 3 — TARGET / PRODUCT IMPLEMENTATION SEARCH
------------------------------------------------------------

Where target information is available, use the:

- company;
- product;
- platform;
- technology;

together with a technically meaningful concept from the claim.

The purpose is to find evidence specifically connected to the
target.

This is an investigative search.

It does NOT mean that the target is known to implement the
feature.


------------------------------------------------------------
PRIORITY 4 — COMPONENT / ARCHITECTURE SEARCH
------------------------------------------------------------

Where useful, search for likely components, subsystems,
architectures, or implementation locations from the technology
profile.

Examples:

- controller;
- gateway;
- routing module;
- battery management system;
- contactor;
- protocol layer;
- communication subsystem.

Use these only when they provide a plausible route to finding
the claimed functionality.

Do not turn a generic component into an assumed target fact.


------------------------------------------------------------
PRIORITY 5 — DISTINCTIVE COMBINATION SEARCH
------------------------------------------------------------

Where useful, combine two or more distinctive technical
concepts from the claim.

The purpose is to search for the technical fingerprint of the
claim rather than generic individual concepts.

For example:

"traffic classification" + "specialized edge routing"

is more useful than:

"network traffic"

alone.


============================================================
IMPORTANT: SEARCH DIVERSITY
============================================================

Queries must be meaningfully different.

Do NOT produce:

1. "Bluetooth GATT characteristic value"
2. "GATT characteristic value Bluetooth"
3. "Bluetooth characteristic value GATT"

These are effectively the same search.

Instead produce different discovery paths, such as:

1. claim relationship;
2. industry terminology;
3. target/product implementation;
4. component architecture;
5. distinctive technical combination.


============================================================
TARGET INFORMATION
============================================================

Use target information when available.

Company:
{target.company}

Product:
{target.product}

Technology:
{target.technology}

If a target field is missing, do not invent it.

Do not claim that the target implements anything.

Target-specific queries are investigative only.


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

They must NEVER be presented as established target facts.

For example:

Hypothesis:
"The functionality may reside in a network edge controller."

Acceptable search:

"[target] network edge controller traffic routing"

Not acceptable reasoning:

"The target uses a network edge controller."


============================================================
SOURCE DISCOVERY
============================================================

Searches should be designed to find:

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
- implementation guides.

Do not optimize queries for patent databases.


============================================================
SITE-RESTRICTED SEARCHES
============================================================

Where the target or technology has a clearly relevant
authoritative domain, a site-restricted query may be useful.

Examples:

site:developer.android.com

site:learn.microsoft.com

site:cisco.com

Use site restrictions only when they are genuinely relevant.

Do not invent domains.


============================================================
QUERY CONSTRUCTION
============================================================

Queries should generally contain technically meaningful terms.

Avoid:

- extremely generic terms;
- long copies of the entire claim;
- unnecessary legal language;
- excessive quotation marks;
- assumed implementation details;
- unsupported company-specific terminology.

Use quotation marks selectively for distinctive technical
phrases.

Prefer concise technical searches that search engines can
actually retrieve useful pages for.


============================================================
PATENTS
============================================================

Do NOT intentionally search for patents.

Do NOT include patent databases as preferred sources.

The objective is real-world technical evidence.

Patent results will also be filtered by the search service.


============================================================
QUERY PRIORITY
============================================================

Priority meaning:

1 = strongest / most directly connected

2 = terminology / concept expansion

3 = target or product implementation investigation

4 = component / architecture investigation

5 = broader or highly exploratory technical path


Priority is a ranking of investigative value.

It is NOT a confidence score.


============================================================
NUMBER OF QUERIES
============================================================

Generate approximately 3–5 queries.

Do not generate multiple nearly identical queries.

For a simple claim element, 3 strong queries may be enough.

For a technically complex element, 4–5 complementary queries
may be appropriate.


============================================================
RATIONALE
============================================================

Every query must have a concise rationale explaining:

1. what technical concept the query targets; and
2. why this search path could find real-world evidence.

For target-specific or implementation-hypothesis queries,
explicitly indicate that the search is investigative.


============================================================
FINAL SELF-CHECK
============================================================

Before returning the search plan:

1. Is there at least one priority-1 query?

2. Is there at least one priority-2 query?

3. Are the queries genuinely different?

4. Does at least one query search the actual claim substance?

5. Does at least one query use alternative industry terminology?

6. If target information is available, does at least one query
   investigate the target/product?

7. Are implementation hypotheses used only as investigative
   paths?

8. Did I avoid treating a hypothesis as a fact?

9. Are the searches suitable for finding real-world technical
   documentation?

10. Did I avoid intentionally searching patent databases?

11. Does every query have a clear rationale?


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
                "Technology profiles do not match claim element IDs."
            )

        if len(technology_profiles) != len(
            claim_elements
        ):
            raise ValueError(
                "Technology profiles do not match claim element IDs."
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

Create targeted web search plans for MULTIPLE claim elements.

Produce exactly one independent search plan for every claim
element provided.

The objective is to discover PUBLIC TECHNICAL EVIDENCE showing
how a real product, system, component, or implementation works.

Do NOT optimize for finding patents.


============================================================
CORE SEARCH PRINCIPLE
============================================================

Do not simply repeat claim language.

Translate each claim element through multiple discovery paths:

PATENT LANGUAGE
        ↓
TECHNICAL CONCEPT
        ↓
INDUSTRY TERMINOLOGY
        ↓
PRODUCT / IMPLEMENTATION TERMINOLOGY
        ↓
PUBLIC TECHNICAL EVIDENCE


============================================================
SEARCH STRATEGIES
============================================================

Each claim element should use several complementary strategies.


------------------------------------------------------------
PRIORITY 1 — CLAIM-SUBSTANCE
------------------------------------------------------------

Every claim element MUST have at least one priority-1 query.

Search the actual technical:

- relationship;
- action;
- structure;
- condition;
- operation;
- causal relationship;
- functional behavior.

Keep the query close to the technical substance.


------------------------------------------------------------
PRIORITY 2 — INDUSTRY TERMINOLOGY
------------------------------------------------------------

Every claim element MUST have at least one priority-2 query.

Use:

- alternative terminology;
- technical concepts;
- engineering terminology;
- industry vocabulary;
- functional equivalents.

The query must provide a genuinely different terminology path
from the priority-1 query.


------------------------------------------------------------
PRIORITY 3 — TARGET / PRODUCT
------------------------------------------------------------

Where target information is available, use priority-3 searches
to investigate:

- company;
- product;
- platform;
- technology;

combined with meaningful technical concepts from the claim.

These are investigative searches only.

Do NOT assume that the target implements the claim.


------------------------------------------------------------
PRIORITY 4 — COMPONENT / ARCHITECTURE
------------------------------------------------------------

Where useful, investigate likely:

- components;
- subsystems;
- architectures;
- modules;
- protocols;
- implementation locations.

These come from the technology profile.

Do not treat them as confirmed target characteristics.


------------------------------------------------------------
PRIORITY 5 — DISTINCTIVE TECHNICAL COMBINATION
------------------------------------------------------------

Where useful, combine multiple distinctive concepts from the
claim element to search for its technical fingerprint.

Avoid generic searches.


============================================================
SEARCH DIVERSITY
============================================================

Do not generate several versions of the same query.

Bad:

"BLE GATT characteristic value"

"GATT characteristic value BLE"

"Bluetooth GATT characteristic value"

Good:

1. claim relationship search;

2. alternative industry terminology search;

3. target/product implementation search;

4. component/architecture search;

5. distinctive technical combination search.


============================================================
TARGET
============================================================

Company:
{target.company}

Product:
{target.product}

Technology:
{target.technology}


Use target information when available.

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
- implementation guides.


============================================================
IMPLEMENTATION HYPOTHESES
============================================================

Implementation hypotheses may be used as exploratory search paths.

They are NOT established facts.

If a hypothesis is used, the query rationale should identify
it as an investigative possibility.


============================================================
PATENTS
============================================================

Do not intentionally search for patents.

Do not include patent databases as preferred sources.

The goal is real-world product and technical evidence.


============================================================
QUERY RULES
============================================================

Each claim element should generally receive 3–5 queries.

Queries must be:

- technically meaningful;
- concise;
- complementary;
- useful for web search;
- grounded in the claim or technology profile.

Avoid:

- generic searches;
- complete claim copies;
- excessive legal language;
- excessive quotation marks;
- unsupported assumptions;
- repetitive queries.


============================================================
RATIONALE
============================================================

Every query requires a concise rationale.

Explain:

1. what technical concept it searches; and
2. why that search could discover relevant public technical
   evidence.

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

5. Use priority 3–5 for implementation-oriented searches.

6. Do not create priority-1 or priority-2 searches whose main
   basis is an unconfirmed implementation hypothesis.

7. Do not omit claim elements.

8. Do not create plans for unknown IDs.

9. Queries must be meaningfully different.

10. Return only the requested structured output.


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
        # Mandatory direct search.
        # --------------------------------------------------------

        if 1 not in priorities:

            raise ValueError(
                f"Search plan for claim element "
                f"{claim_element_id} must contain "
                "at least one priority-1 query."
            )

        # --------------------------------------------------------
        # Mandatory terminology/concept expansion.
        # --------------------------------------------------------

        if 2 not in priorities:

            raise ValueError(
                f"Search plan for claim element "
                f"{claim_element_id} must contain "
                "at least one priority-2 query."
            )

        # --------------------------------------------------------
        # Validate priority range explicitly even though the
        # Pydantic schema also constrains it.
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
