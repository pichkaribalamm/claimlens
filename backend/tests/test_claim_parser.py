from unittest.mock import patch

from app.agents.claim_parser import ClaimParser
from app.models.schemas import Claim


def test_claim_parser():

    claim = Claim(
        claim_number="1",
        text=(
            "A device comprising a processor configured to "
            "receive image data."
        ),
    )

    fake_gemini_response = """
    {
        "elements": [
            {
                "id": "1.1",
                "claim_number": "1",
                "text": "a processor configured to receive image data"
            }
        ]
    }
    """

    with patch(
        "app.agents.claim_parser.GeminiService"
    ) as mock_gemini:

        mock_gemini.return_value.generate.return_value = (
            fake_gemini_response
        )

        parser = ClaimParser()

        result = parser.parse(claim)

    assert len(result.elements) == 1
    assert result.elements[0].id == "1.1"
    assert result.elements[0].claim_number == "1"
    assert result.elements[0].text == (
        "a processor configured to receive image data"
    )

    mock_gemini.return_value.generate.assert_called_once()
