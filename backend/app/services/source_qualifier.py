from urllib.parse import urlparse

from app.models.schemas import SearchResult


class SourceQualifier:

    # ============================================================
    # TIER 1
    # Primary / official technical sources
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
    # Generic technical blogs / secondary sources.
    #
    # These are deliberately excluded when minimum_tier=2.
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
    }

    def __init__(
        self,
        minimum_tier: int = 2,
    ):
        """
        minimum_tier controls which source tiers are accepted.

        1 -> Tier 1 only
        2 -> Tier 1 + Tier 2
        3 -> Tier 1 + Tier 2 + Tier 3
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

    def qualify(
        self,
        search_result: SearchResult,
    ) -> bool:

        tier = self.quality_tier(
            search_result
        )

        # None means:
        # - explicitly excluded, OR
        # - unknown domain
        #
        # Either way, do not qualify it.
        if tier is None:
            return False

        return tier <= self.minimum_tier

    def quality_tier(
        self,
        search_result: SearchResult,
    ) -> int | None:

        domain = self._domain(
            search_result.url
        )

        if not domain:
            return None

        # Explicit exclusions always win.
        if self._matches_domain(
            domain,
            self.EXCLUDED_DOMAINS,
        ):
            return None

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

        # Unknown domains are deliberately rejected.
        return None

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

        return "UNQUALIFIED"

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
