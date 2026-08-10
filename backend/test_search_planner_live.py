from app.agents.technology_profiler import TechnologyProfiler
from app.agents.search_planner import SearchPlanner
from app.models.schemas import ClaimElement, TargetScope


element = ClaimElement(
    id="1.2",
    claim_number="1",
    text="a processor configured to receive image data"
)

target = TargetScope(
    company="Samsung",
    product="Galaxy S26 Ultra"
)

print("\n=== TECHNOLOGY PROFILER ===")

profiler = TechnologyProfiler()

technology_profile = profiler.profile(
    element,
    target
)

print("\nCORE CONCEPT:")
print(technology_profile.core_concept)

print("\nTECHNICAL CONCEPTS:")
for concept in technology_profile.technical_concepts:
    print(f"- {concept}")

print("\nALTERNATIVE TERMINOLOGY:")
for term in technology_profile.alternative_terminology:
    print(f"- {term}")

print("\nLIKELY COMPONENTS:")
for component in technology_profile.likely_components:
    print(f"- {component}")


print("\n=== SEARCH PLANNER ===")

planner = SearchPlanner()

search_plan = planner.plan(
    element,
    target,
    technology_profile
)

print("\nSEARCH STRATEGY:")
print(search_plan.search_strategy)

print("\nPREFERRED SOURCES:")
for source in search_plan.preferred_sources:
    print(f"- {source}")

print("\nSEARCH QUERIES:")

for i, query in enumerate(search_plan.queries, start=1):
    print(f"\n{i}. {query.query}")
    print(f"   Priority: {query.priority}")
    print(f"   Rationale: {query.rationale}")
