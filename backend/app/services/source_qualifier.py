from urllib.parse import urlparse

from app.models.schemas import SearchResult


class SourceQualifier:

    # --------------------------------------------------
    # Highest-confidence sources.
    #
    # These are primary / official technical sources,
    # official documentation, standards bodies,
    # manufacturers, and established technical
    # organizations.
    # --------------------------------------------------

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

        # Major semiconductor / hardware vendors
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
        "cloud.google.com",
        "aws.amazon.com",
        "azure.microsoft.com",

        # Open-source project documentation
        "kubernetes.io",
        "docs.python.org",
        "docs.kernel.org",
        "ietf.org",
        "datatracker.ietf.org",

        # Standards / technical organizations
        "bluetooth.com",
        "3gpp.org",
        "ieee.org",

        # Official GitHub repositories
        "github.com",
    }

    # --------------------------------------------------
    # Tier 2:
    # Established technical publications / educational
    # resources. Useful, but below primary documentation.
    # --------------------------------------------------

    TIER_2_DOMAINS = {
        "punchthrough.com",
        "freecodecamp.org",
        "medium.com",
        "hackernoon.com",
        "electronics.stackexchange.com",
        "stackoverflow.com",
        "riptutorial.com",
    }

    # --------------------------------------------------
    # Tier 3:
    # Generic blogs / aggregators / content farms.
    #
    # These should not normally be used for strong
    # evidence when better sources are available.
    # --------------------------------------------------

    TIER_3_DOMAINS = {
        "codezup.com",
        "stormotion.io",
        "itsectr.com",
        "novelbits.io",
        "actorsfit.in",
        "programcreek.com",
        "javatips.net",
        "52im.net",
        "emanual.github.io",
        "codestudy.net",
        "nilhcem.com",
    }

    # --------------------------------------------------
    # Explicitly excluded domains.
    #
    # These are not acceptable evidence sources for the
    # ClaimLens workflow.
    # --------------------------------------------------

    EXCLUDED_DOMAINS = {
        # Patent databases / patent aggregators
        "patents.google.com",
        "patents.justia.com",
        "patentscope.wipo.int",
        "worldwide.espacenet.com",
        "espacenet.com",
        "ppubs.uspto.gov",
        "patents.uspto.gov",

        # Social / video platforms
        "youtube.com",
        "youtu.be",
        "tiktok.com",
        "instagram.com",
        "facebook.com",
        "x.com",
        "twitter.com",

        # Generic Q&A / low-verifiability sources
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
        minimum_tier:

        1 = only Tier 1 sources
        2 = Tier 1 + Tier 2
        3 = Tier 1 + Tier 2 + Tier 3
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

        return (
            self.quality_tier(
                search_result
            )
            <= self.minimum_tier
        )

    def quality_tier(
        self,
        search_result: SearchResult,
    ) -> int | None:

        domain = self._domain(
            search_result.url
        )

        if not domain:
            return None

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

        # Unknown domains are deliberately conservative.
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
            parsed.hostname
            or ""
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
