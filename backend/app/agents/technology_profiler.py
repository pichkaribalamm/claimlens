from app.models.schemas import (
    ClaimElement,
    TargetScope,
    TechnologyProfile,
    TechnologyProfileBatchResult,
)
from app.services.gemini_service import GeminiService


class TechnologyProfiler:

    def __init__(self):
        self.llm = GeminiService()

    # ============================================================
    # SINGLE ELEMENT PROFILE
    # ============================================================

    def profile(
        self,
        claim_element: ClaimElement,
        target: TargetScope,
    ) -> TechnologyProfile:

        prompt = f"""
You are a technical research assistant supporting patent
evidence discovery.

Your task is to transform ONE patent claim element into a
technical research profile that can be used to discover
real-world public technical evidence.

The purpose of this profile is SEARCH EXPANSION.

It should help a downstream search planner find technical
documentation, product documentation, engineering material,
standards, manuals, implementation descriptions, and other
public evidence that may describe the claimed functionality
using different terminology.


============================================================
CORE OBJECTIVE
============================================================

Analyze the claim element from a technical research perspective.

Identify:

1. What the claim element technically requires.

2. The core technical concept.

3. Related technical concepts.

4. Alternative terminology that a real-world technical source
   might use instead of the claim's terminology.

5. Components or subsystems commonly associated with the
   functionality.

6. Plausible implementation locations or mechanisms that could
   later be investigated in the target.

Do NOT determine whether the target actually implements the
claim.


============================================================
CLAIM FIDELITY
============================================================

Stay grounded in the actual claim element.

Do NOT:

- add claim limitations;
- invent components;
- assume a particular implementation;
- assume a particular company uses a particular technology;
- convert a hypothesis into a fact;
- perform infringement analysis.


============================================================
CORE CONCEPT
============================================================

The core concept should be a concise technical description of
what the claim element is fundamentally doing.

It should describe the technical substance rather than merely
repeat the claim.

Bad:

"Network traffic"

Better:

"Criteria-based routing of selected network traffic through a
specialized network edge system"


Bad:

"Battery"

Better:

"Secondary electrical isolation of a battery from an electrical
bus following failure of a primary contactor"


The core concept should remain faithful to the claim.


============================================================
TECHNICAL CONCEPTS
============================================================

Identify related technical concepts that could help discover
the same functionality in real-world technical material.

These may include:

- related mechanisms;
- subsystem concepts;
- functional concepts;
- implementation concepts;
- industry terminology;
- relevant protocol concepts;
- relevant architecture concepts;
- relevant electrical/mechanical/software concepts.

Prefer technically meaningful concepts over generic nouns.


============================================================
ALTERNATIVE TERMINOLOGY
============================================================

This is especially important.

Generate terminology that real-world technical sources might
use to describe the same or closely related concept.

Consider:

- engineering terminology;
- manufacturer terminology;
- product documentation terminology;
- industry terminology;
- abbreviations;
- acronyms;
- equivalent component names;
- equivalent functional terms;
- implementation terminology;
- common terminology versus patent-style terminology;
- older or alternative terminology where technically relevant.

For example, if the claim uses one term for a component or
function, a technical manual may use a different term for the
same concept.

Include those alternatives.

Do NOT invent company-specific terminology.

Do NOT claim that a particular manufacturer uses a term unless
that fact is actually present in the claim context.

The terminology is for search expansion, not factual attribution.


============================================================
LIKELY COMPONENTS
============================================================

Identify generic components, subsystems, software modules,
protocol entities, or architectural components that are
commonly associated with implementing the claimed functionality.

These are research targets, NOT assertions about the target.

For example, depending on the claim, these could include:

- controllers;
- switches;
- sensors;
- gateways;
- network interfaces;
- processors;
- memory;
- communication modules;
- power electronics;
- contactors;
- protection circuits;
- routing modules;
- protocol layers.

Only include components that have a technically reasonable
relationship to the claim element.


============================================================
IMPLEMENTATION HYPOTHESES
============================================================

Generate plausible hypotheses about where or how the claimed
functionality might be implemented in a real product or system.

These hypotheses are NOT facts.

Good examples:

- "The functionality may be implemented in the network edge
  controller responsible for traffic classification and routing."

- "The behavior may be implemented through a battery management
  controller interacting with high-voltage isolation hardware."

Bad:

- "The target uses this controller."

- "The target definitely implements this feature."

- "Company X uses this architecture."

The purpose of hypotheses is to guide subsequent search.


============================================================
TARGET CONTEXT
============================================================

Use the target scope to make the profile useful for research.

However, target information must NOT cause you to invent facts.

The target scope is:

Company:
{target.company}

Product:
{target.product}

Technology:
{target.technology}


The target scope may help identify terminology or likely
technical areas to investigate, but you must not assume that
the target contains a component or implementation unless the
claim element itself establishes it.


============================================================
SEARCH EXPANSION PRIORITY
============================================================

Prioritize terminology that is likely to appear in:

- official product documentation;
- developer documentation;
- engineering manuals;
- technical specifications;
- system architecture documentation;
- standards;
- technical support documentation;
- manufacturer documentation;
- product datasheets;
- technical white papers;
- implementation guides;
- reputable technical resources.

Do not optimize terminology for patent searching.

The goal is to find evidence of REAL-WORLD TECHNICAL
IMPLEMENTATION.


============================================================
IMPORTANT DISTINCTION
============================================================

A patent may describe the claimed concept using terminology
that is not how a product manufacturer describes the same
technology.

Therefore, do not simply restate the claim.

Translate the claim into the vocabulary that engineers and
technical documentation are likely to use.


============================================================
DO NOT SEARCH
============================================================

Do not search the web.

Do not cite sources.

Do not claim that evidence exists.

Do not determine whether the target practices the claim.


============================================================
OUTPUT QUALITY
============================================================

The resulting profile should be:

- technically specific;
- useful for search expansion;
- faithful to the claim;
- broad enough to capture terminology variation;
- conservative about target-specific facts.

Avoid generic filler.

Every item should have a plausible reason for being useful in
technical evidence discovery.


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
            response_schema=TechnologyProfile,
        )

        return TechnologyProfile.model_validate_json(
            result
        )

    # ============================================================
    # BATCH PROFILE
    # ============================================================

    def profile_batch(
        self,
        claim_elements: list[ClaimElement],
        target: TargetScope,
    ) -> list[TechnologyProfile]:

        if not claim_elements:
            return []

        element_sections = []

        for element in claim_elements:

            element_sections.append(
                (
                    f"CLAIM ELEMENT ID:\n"
                    f"{element.id}\n\n"
                    f"CLAIM ELEMENT TEXT:\n"
                    f"{element.text}"
                )
            )

        prompt = f"""
You are a technical research assistant supporting patent
evidence discovery.

Your task is to transform multiple patent claim elements into
technical research profiles for discovering real-world public
technical evidence.

The purpose of the profiles is SEARCH EXPANSION.

Produce exactly one profile for every claim element provided.


============================================================
CORE OBJECTIVE
============================================================

For each claim element identify:

1. The core technical concept.

2. Related technical concepts.

3. Alternative terminology that real-world technical sources
   may use for the same or closely related concept.

4. Generic components or subsystems commonly associated with
   implementing the claimed functionality.

5. Plausible implementation hypotheses that can guide later
   investigation.

Do NOT determine whether the target actually practices the
claim.


============================================================
CLAIM FIDELITY
============================================================

Remain grounded in the corresponding claim element.

Do NOT:

- add claim limitations;
- invent components;
- assume a particular implementation;
- assume a company uses a particular technology;
- convert hypotheses into facts;
- perform infringement analysis.


============================================================
CORE CONCEPT
============================================================

Describe the fundamental technical concept represented by the
claim element.

Do not merely repeat generic nouns from the claim.

The description should capture the actual technical function,
relationship, mechanism, or architecture.


============================================================
TECHNICAL CONCEPTS
============================================================

Identify related technical concepts useful for finding public
technical evidence.

Consider:

- mechanisms;
- functions;
- subsystem concepts;
- architecture concepts;
- implementation concepts;
- engineering terminology;
- industry terminology;
- protocol or system concepts where applicable.


============================================================
ALTERNATIVE TERMINOLOGY
============================================================

This field is a major SEARCH EXPANSION mechanism.

Identify terminology that real-world technical sources may use
instead of the claim terminology.

Consider:

- engineering terminology;
- manufacturer terminology;
- product documentation terminology;
- industry terminology;
- abbreviations;
- acronyms;
- equivalent component names;
- equivalent functional descriptions;
- implementation terminology;
- alternative technical phrases;
- older/newer terminology when technically relevant.

Do NOT invent company-specific terminology.

Do NOT claim that a company uses a particular term.

These terms are search candidates, not factual assertions.


============================================================
LIKELY COMPONENTS
============================================================

Identify generic components, subsystems, modules, or architectural
entities that could reasonably implement the claimed functionality.

These are investigation targets only.

Do NOT state or imply that these components are present in the
target.


============================================================
IMPLEMENTATION HYPOTHESES
============================================================

Identify plausible ways or locations in which the claimed
functionality might be implemented in a real product.

These are hypotheses only.

Use language such as:

- "may be implemented by..."
- "could be handled by..."
- "may reside in..."
- "could involve..."

Do NOT state:

- "the target uses..."
- "the product contains..."
- "Company X implements..."


============================================================
TARGET CONTEXT
============================================================

Use the target scope to make the research profile relevant.

Target:

Company:
{target.company}

Product:
{target.product}

Technology:
{target.technology}

Target context must NOT be used to invent facts.


============================================================
REAL-WORLD EVIDENCE ORIENTATION
============================================================

Optimize the profile for finding evidence in:

- official product documentation;
- developer documentation;
- engineering manuals;
- technical specifications;
- manufacturer documentation;
- product datasheets;
- system architecture material;
- standards;
- technical support documentation;
- implementation guides;
- reputable technical resources.

Do not optimize for patent terminology.

The objective is to discover evidence of actual technical
implementation.


============================================================
TECHNICAL TERMINOLOGY TRANSLATION
============================================================

A patent may describe a technology differently from the way a
manufacturer or engineer describes it.

Therefore:

Do not simply repeat the claim.

Translate the technical concept into terminology that could
reasonably appear in real-world technical documentation.


============================================================
NO WEB SEARCH
============================================================

Do not search the web.

Do not cite sources.

Do not determine whether the target practices any claim element.

Do not claim that evidence exists.


============================================================
BATCH OUTPUT REQUIREMENTS
============================================================

1. Analyze every claim element independently.

2. Preserve every claim element ID exactly.

3. Return exactly one technology profile for every input claim
   element.

4. Do not omit an element.

5. Do not create profiles for IDs that were not provided.

6. Do not combine two claim elements into one profile.

7. Keep every profile grounded in its corresponding element.

8. Return only the requested structured output.


============================================================
TARGET SCOPE
============================================================

Company:
{target.company}

Product:
{target.product}

Technology:
{target.technology}


============================================================
CLAIM ELEMENTS
============================================================

{chr(10).join(element_sections)}


Return only the requested structured output.
"""

        result = self.llm.generate(
            prompt=prompt,
            response_schema=TechnologyProfileBatchResult,
        )

        parsed = (
            TechnologyProfileBatchResult
            .model_validate_json(result)
        )

        expected_ids = [
            element.id
            for element in claim_elements
        ]

        expected_id_set = set(
            expected_ids
        )

        actual_ids = [
            profile.claim_element_id
            for profile in parsed.results
        ]

        actual_id_set = set(
            actual_ids
        )

        if actual_id_set != expected_id_set:

            raise ValueError(
                "Technology profile batch returned "
                "invalid claim element IDs."
            )

        if len(actual_ids) != len(
            expected_ids
        ):

            raise ValueError(
                "Technology profile batch returned "
                "duplicate claim element IDs."
            )

        profiles_by_id = {
            profile.claim_element_id: profile
            for profile in parsed.results
        }

        return [
            profiles_by_id[element.id]
            for element in claim_elements
        ]
