from app.agents.technology_profiler import TechnologyProfiler
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

profiler = TechnologyProfiler()

result = profiler.profile(element, target)

print("\nCLAIM ELEMENT:")
print(result.claim_element_id)

print("\nCORE CONCEPT:")
print(result.core_concept)

print("\nTECHNICAL CONCEPTS:")
for concept in result.technical_concepts:
    print(f"- {concept}")

print("\nALTERNATIVE TERMINOLOGY:")
for term in result.alternative_terminology:
    print(f"- {term}")

print("\nLIKELY COMPONENTS:")
for component in result.likely_components:
    print(f"- {component}")
