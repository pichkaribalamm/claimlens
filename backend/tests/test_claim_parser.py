from app.models.schemas import ClaimParseResult


def test_claim_parse_result():

    result = ClaimParseResult(
        elements=[
            {
                "id": "1.1",
                "claim_number": "1",
                "text": "a processor"
            },
            {
                "id": "1.2",
                "claim_number": "1",
                "text": "a memory coupled to the processor"
            }
        ]
    )

    assert len(result.elements) == 2
    assert result.elements[0].id == "1.1"
    assert result.elements[1].claim_number == "1"
