from app.models.schemas import SearchResult
from app.services.source_qualifier import SourceQualifier


def make_result(url: str) -> SearchResult:
    return SearchResult(
        title="Test source",
        url=url,
        snippet="Test snippet",
        source=None,
    )


def test_qualifier_accepts_official_android_source():

    qualifier = SourceQualifier()

    result = qualifier.qualify(
        make_result(
            "https://developer.android.com/reference/android/bluetooth/BluetoothGatt"
        )
    )

    assert result is not None
    assert result.source_type == "official"
    assert result.source_quality == "tier_1"


def test_qualifier_accepts_standards_source():

    qualifier = SourceQualifier()

    result = qualifier.qualify(
        make_result(
            "https://www.bluetooth.com/specifications/specs/"
        )
    )

    assert result is not None
    assert result.source_type == "standards"
    assert result.source_quality == "tier_2"


def test_qualifier_accepts_government_source():

    qualifier = SourceQualifier()

    result = qualifier.qualify(
        make_result(
            "https://www.nist.gov/publications/example"
        )
    )

    assert result is not None
    assert result.source_type == "government"
    assert result.source_quality == "tier_2"


def test_qualifier_accepts_technical_publication():

    qualifier = SourceQualifier()

    result = qualifier.qualify(
        make_result(
            "https://www.eetimes.com/example-technical-article/"
        )
    )

    assert result is not None
    assert result.source_type == "technical_publication"
    assert result.source_quality == "tier_3"


def test_qualifier_rejects_google_patent():

    qualifier = SourceQualifier()

    result = qualifier.qualify(
        make_result(
            "https://patents.google.com/patent/US9221343B2/en"
        )
    )

    assert result is None


def test_qualifier_rejects_justia_patent():

    qualifier = SourceQualifier()

    result = qualifier.qualify(
        make_result(
            "https://patents.justia.com/patent/9221343"
        )
    )

    assert result is None


def test_qualifier_rejects_patent_path():

    qualifier = SourceQualifier()

    result = qualifier.qualify(
        make_result(
            "https://example.com/patent/US1234567"
        )
    )

    assert result is None


def test_qualifier_rejects_youtube():

    qualifier = SourceQualifier()

    result = qualifier.qualify(
        make_result(
            "https://www.youtube.com/watch?v=example"
        )
    )

    assert result is None


def test_qualifier_rejects_reddit():

    qualifier = SourceQualifier()

    result = qualifier.qualify(
        make_result(
            "https://www.reddit.com/r/bluetooth/example"
        )
    )

    assert result is None


def test_qualifier_rejects_wikipedia():

    qualifier = SourceQualifier()

    result = qualifier.qualify(
        make_result(
            "https://en.wikipedia.org/wiki/Bluetooth"
        )
    )

    assert result is None


def test_qualifier_rejects_unknown_domain():

    qualifier = SourceQualifier()

    result = qualifier.qualify(
        make_result(
            "https://random-example-site.com/article"
        )
    )

    assert result is None


def test_qualifier_accepts_official_github_repository():

    qualifier = SourceQualifier()

    result = qualifier.qualify(
        make_result(
            "https://github.com/android/platform_frameworks_base"
        )
    )

    assert result is not None
    assert result.source_type == "official"
    assert result.source_quality == "tier_1"


def test_qualifier_rejects_unrecognized_github_repository():

    qualifier = SourceQualifier()

    result = qualifier.qualify(
        make_result(
            "https://github.com/random-user/random-project"
        )
    )

    assert result is None


def test_qualifier_preserves_search_result_fields():

    qualifier = SourceQualifier()

    original = SearchResult(
        title="Android BluetoothGatt Documentation",
        url="https://developer.android.com/reference/android/bluetooth/BluetoothGatt",
        snippet="Bluetooth GATT API documentation",
        source=None,
    )

    result = qualifier.qualify(original)

    assert result is not None
    assert result.title == original.title
    assert str(result.url) == str(original.url)
    assert result.snippet == original.snippet
    assert result.source_type == "official"
    assert result.source_quality == "tier_1"


def test_qualifier_classifies_nokia_as_official():

    qualifier = SourceQualifier()

    result = qualifier.qualify(
        make_result(
            "https://www.nokia.com/networks/"
        )
    )

    assert result is not None
    assert result.source_type == "official"
    assert result.source_quality == "tier_1"


def test_qualifier_classifies_lges_as_official():

    qualifier = SourceQualifier()

    result = qualifier.qualify(
        make_result(
            "https://www.lgensol.com/en/product/ess"
        )
    )

    assert result is not None
    assert result.source_type == "official"
    assert result.source_quality == "tier_1"


def test_qualifier_classifies_chevrolet_as_official():

    qualifier = SourceQualifier()

    result = qualifier.qualify(
        make_result(
            "https://www.chevrolet.com/electric"
        )
    )

    assert result is not None
    assert result.source_type == "official"
    assert result.source_quality == "tier_1"
