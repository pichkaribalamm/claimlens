from urllib.parse import urlparse

from app.models.schemas import SearchResult


class SourceQualifier:

    # ============================================================
    # TIER 1
    #
    # Primary / official technical sources.
    # ============================================================

    TIER_1_DOMAINS = {
        # Android / Google
        "developer.android.com",
        "source.android.com",

        # Microsoft
        "learn.microsoft.com",

        # Apple
        "developer.apple.com",

        # IBM
        "ibm.com",
        "developer.ibm.com",

        # Semiconductor / hardware
        "microchip.com",
        "developerhelp.microchip.com",
        "ti.com",
        "software-dl.ti.com",
        "nordicsemi.com",
        "devzone.nordicsemi.com",
        "silabs.com",
        "docs.silabs.com",
        "nxp.com",
        "community.nxp.com",
        "qualcomm.com",
        "intel.com",
        "amd.com",
        "arm.com",

        # Networking / infrastructure
        "cisco.com",
        "juniper.net",
        "nokia.com",
        "ericsson.com",

        # Cloud / infrastructure
        "cloud.google.com",
        "aws.amazon.com",
        "azure.microsoft.com",

        # Technical standards / organizations
        "ietf.org",
        "datatracker.ietf.org",
        "bluetooth.com",
        "3gpp.org",
        "ieee.org",

        # Open-source technical documentation
        "kubernetes.io",
        "docs.python.org",
        "docs.kernel.org",

        # Official repositories
        "github.com",
    }

    # ============================================================
    # TIER 2
    #
    # Established technical resources.
    # ============================================================

    TIER_2_DOMAINS = {
        "punchthrough.com",
        "freecodecamp.org",
        "electronics.stackexchange.com",
        "stackoverflow.com",
    }

    # ============================================================
    # TIER 3
    #
    # Generic technical blogs / secondary sources.
    # ============================================================

    TIER_3_DOMAINS = {
        "medium.com",
        "hackernoon.com",
        "codezup.com",
        "stormotion.io",
        "itsectr.com",
        "novelbits.io",
        "actorsfit.in",
        "programcreek.com",
        "javatips.net",
        "emanual.github.io",
        "codestudy.net",
        "nilhcem.com",
    }

    # ============================================================
    # EXPLICITLY EXCLUDED
    #
    # These should never become evidence sources.
    # ============================================================

    EXCLUDED_DOMAINS = {
        # Patent sources
        "patents.google.com",
        "patents.justia.com",
        "patentscope.wipo.int",
        "worldwide.espacenet.com",
        "espacenet.com",
        "ppubs.uspto.gov",
        "patents.uspto.gov",

        # Social / video
        "youtube.com",
        "youtu.be",
        "tiktok.com",
        "instagram.com",
        "facebook.com",
        "x.com",
        "twitter.com",

        # Generic Q&A
        "quora.com",

        # Search engines
        "google.com",
        "bing.com",
        "duckduckgo.com",
        "search.yahoo.com",
    }

    # ============================================================
    # EXCLUDED URL / PATH MARKERS
    #
    # These provide a second layer of patent filtering.
    #
    # A patent page can appear on a non-obvious domain, so we
    # should not rely only on the hostname.
    # ============================================================

    EXCLUDED_PATH_MARKERS = {
        "/patent/",
        "/patents/",
        "/patent-search/",
        "/patentnumber/",
        "/patent-number/",
        "/patentscope/",
        "/publication/",
        "/publications/",
    }

    # ============================================================
    # SOURCE TYPE LABELS
    # ============================================================

    SOURCE_TYPE_OFFICIAL = "official"
    SOURCE_TYPE_TECHNICAL = "technical"
    SOURCE_TYPE_SECONDARY = "secondary"
    SOURCE_TYPE_UNKNOWN = "unknown"
    SOURCE_TYPE_EXCLUDED = "excluded"

    def __init__(
        self,
        minimum_tier: int = 2,
        allow_unknown: bool = False,
    ):
        """
        minimum_tier controls which known source tiers qualify.

        1 -> Tier 1 only
        2 -> Tier 1 + Tier 2
        3 -> Tier 1 + Tier 2 + Tier 3

        allow_unknown controls whether domains that are not
        explicitly classified may pass qualification.

        Default is False because source quality should remain
        deterministic unless explicitly configured otherwise.
        """

        if minimum_tier not in {
            1,
            2,
            3,
        }:
            raise ValueError(
                "minimum_tier must be 1, 2, or 3."
            )

        self.minimum_tier = minimum_tier
        self.allow_unknown = allow_unknown

    # ============================================================
    # QUALIFICATION
    # ============================================================

    def qualify(
        self,
        search_result: SearchResult,
    ) -> bool:
        """
        Determine whether a source may proceed to evidence
        extraction.

        Patent and explicitly excluded sources are always rejected.

        Known sources are accepted according to minimum_tier.

        Unknown sources are rejected by default unless
        allow_unknown=True.
        """

        source_type = self.source_type(
            search_result
        )

        # --------------------------------------------------------
        # Hard exclusions always win.
        # --------------------------------------------------------

        if source_type == self.SOURCE_TYPE_EXCLUDED:
            return False

        tier = self.quality_tier(
            search_result
        )

        # --------------------------------------------------------
        # Known source.
        # --------------------------------------------------------

        if tier is not None:

            return (
                tier <= self.minimum_tier
            )

        # --------------------------------------------------------
        # Unknown source.
        # --------------------------------------------------------

        return self.allow_unknown

    # ============================================================
    # QUALITY TIER
    # ============================================================

    def quality_tier(
        self,
        search_result: SearchResult,
    ) -> int | None:

        domain = self._domain(
            search_result.url
        )

        if not domain:
            return None

        # --------------------------------------------------------
        # Explicit exclusions always win.
        # --------------------------------------------------------

        if self._is_excluded(
            search_result
        ):
            return None

        # --------------------------------------------------------
        # Known tiers.
        # --------------------------------------------------------

        if self._matches_domain(
            domain,
            self.TIER_1_DOMAINS,
        ):
            return 1

        if self._matches_domain(
            domain,
            self.TIER_2_DOMAINS,
        ):
            return 2

        if self._matches_domain(
            domain,
            self.TIER_3_DOMAINS,
        ):
            return 3

        # Unknown domain.
        return None

    # ============================================================
    # QUALITY LABEL
    # ============================================================

    def quality_label(
        self,
        search_result: SearchResult,
    ) -> str:

        tier = self.quality_tier(
            search_result
        )

        if tier == 1:
            return "TIER_1"

        if tier == 2:
            return "TIER_2"

        if tier == 3:
            return "TIER_3"

        if self.source_type(
            search_result
        ) == self.SOURCE_TYPE_EXCLUDED:

            return "EXCLUDED"

        return "UNKNOWN"

    # ============================================================
    # SOURCE TYPE
    # ============================================================

    def source_type(
        self,
        search_result: SearchResult,
    ) -> str:

        domain = self._domain(
            search_result.url
        )

        if not domain:
            return self.SOURCE_TYPE_UNKNOWN

        if self._is_excluded(
            search_result
        ):
            return self.SOURCE_TYPE_EXCLUDED

        if self._matches_domain(
            domain,
            self.TIER_1_DOMAINS,
        ):
            return self.SOURCE_TYPE_OFFICIAL

        if self._matches_domain(
            domain,
            self.TIER_2_DOMAINS,
        ):
            return self.SOURCE_TYPE_TECHNICAL

        if self._matches_domain(
            domain,
            self.TIER_3_DOMAINS,
        ):
            return self.SOURCE_TYPE_SECONDARY

        return self.SOURCE_TYPE_UNKNOWN

    # ============================================================
    # APPLY METADATA
    # ============================================================

    def apply_metadata(
        self,
        search_result: SearchResult,
    ) -> SearchResult:
        """
        Populate source qualification metadata on the existing
        SearchResult object.

        This keeps source classification explicit throughout the
        rest of the pipeline.
        """

        search_result.source_type = (
            self.source_type(
                search_result
            )
        )

        search_result.source_quality = (
            self.quality_label(
                search_result
            )
        )

        return search_result

    # ============================================================
    # EXCLUSION CHECK
    # ============================================================

    def _is_excluded(
        self,
        search_result: SearchResult,
    ) -> bool:

        domain = self._domain(
            search_result.url
        )

        if not domain:
            return True

        # --------------------------------------------------------
        # Domain-level exclusion.
        # --------------------------------------------------------

        if self._matches_domain(
            domain,
            self.EXCLUDED_DOMAINS,
        ):
            return True

        # --------------------------------------------------------
        # URL path exclusion.
        #
        # This provides an additional patent filter.
        # --------------------------------------------------------

        try:
            parsed = urlparse(
                str(search_result.url)
            )

        except Exception:
            return True

        path = (
            parsed.path or ""
        ).lower()

        for marker in self.EXCLUDED_PATH_MARKERS:

            if marker in path:
                return True

        # --------------------------------------------------------
        # Common patent URL indicators.
        # --------------------------------------------------------

        query = (
            parsed.query or ""
        ).lower()

        combined = (
            path + "?" + query
        )

        patent_markers = {
            "patent",
            "patentnumber",
            "publicationnumber",
            "patentid",
            "patent_id",
        }

        for marker in patent_markers:

            if marker in combined:
                return True

        return False

    # ============================================================
    # DOMAIN EXTRACTION
    # ============================================================

    def _domain(
        self,
        url: str,
    ) -> str:

        try:

            parsed = urlparse(
                str(url)
            )

        except Exception:
            return ""

        hostname = (
            parsed.hostname or ""
        ).lower()

        return hostname.removeprefix(
            "www."
        )

    # ============================================================
    # DOMAIN MATCHING
    # ============================================================

    def _matches_domain(
        self,
        domain: str,
        allowed_domains: set[str],
    ) -> bool:

        for allowed_domain in allowed_domains:

            if domain == allowed_domain:
                return True

            if domain.endswith(
                "." + allowed_domain
            ):
                return True

        return False
