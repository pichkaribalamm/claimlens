from app.agents.claim_parser import ClaimParser
from app.models.schemas import Claim


claim = Claim(
    claim_number="1",
    text=(
        "A device comprising a processor configured to "
        "receive image data, a memory coupled to the "
        "processor, and a display configured to present "
        "processed image data."
    ),
)

parser = ClaimParser()

result = parser.parse(claim)

for element in result.elements:
    print(f"{element.id}: {element.text}")
