from app.agents.evidence_verifier import EvidenceVerifier
from app.models.schemas import ClaimElement, Evidence


def test_evidence_verifier():

    element = ClaimElement(
        id="1.2",
        claim_number="1",
        text="an AI image signal processor (ISP) associated with the front camera"
    )

    evidence = Evidence(
        claim_element_id="1.2",
        source_title="Samsung Galaxy S26 Ultra",
        url="https://www.samsung.com/in/smartphones/galaxy-s26-ultra/",
        excerpt=(
            "Galaxy S26 Ultra's front camera now features "
            "an AI image signal processor (ISP)"
        ),
        evidence_type="direct",
        relevance=(
            "The source explicitly confirms that the front camera "
            "features an AI image signal processor (ISP)."
        )
    )

    verifier = EvidenceVerifier()

    result = verifier.verify(
        element,
        evidence
    )

    assert result.claim_element_id == "1.2"
    assert result.evidence_supported is False
    assert result.confidence == 0.0
    assert result.reasoning == (
        "Verification not yet implemented."
    )
