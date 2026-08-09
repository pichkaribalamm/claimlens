from app.models.schemas import (
    Claim,
    ClaimElement,
    TargetScope,
    SearchQuery,
)


def test_claim_creation():
    claim = Claim(
        claim_number="1",
        text="A device comprising a processor."
    )

    assert claim.claim_number == "1"
    assert claim.text == "A device comprising a processor."


def test_claim_element_creation():
    element = ClaimElement(
        id="1.1",
        claim_number="1",
        text="a processor configured to execute instructions"
    )

    assert element.id == "1.1"


def test_target_scope():
    target = TargetScope(
        company="Samsung",
        product="Galaxy S26 Ultra"
    )

    assert target.company == "Samsung"
