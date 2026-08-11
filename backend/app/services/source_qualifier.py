from urllib.parse import urlparse

from app.models.schemas import SearchResult


class SourceQualifier:

    # --------------------------------------------------------
    # Source classifications
    # --------------------------------------------------------

    OFFICIAL = "official"
    STANDARDS = "standards"
    GOVERNMENT = "government"
    TECHNICAL_PUBLICATION = "technical_publication"

    # These are explicitly excluded from the evidence pipeline.
    REJECTED = "rejected"

    # Anything not positively classified is rejected.
    UNKNOWN = "unknown"

    # --------------------------------------------------------
    # Patent domains
    # --------------------------------------------------------

    PATENT_DOMAINS = {
        "patents.google.com",
        "patents.justia.com",
        "patentscope.wipo.int",
        "worldwide.espacenet.com",
        "espacenet.com",
        "ppubs.uspto.gov",
        "patents.uspto.gov",
    }

    PATENT_PATH_MARKERS = {
        "/patent/",
        "/patents/",
        "/patent-search/",
        "/patent-search",
        "/patentnumber/",
    }

    # --------------------------------------------------------
    # Explicitly rejected domains
    # --------------------------------------------------------

    REJECTED_DOMAINS = {
        # Social / community
        "youtube.com",
        "youtu.be",
        "reddit.com",
        "x.com",
        "twitter.com",
        "facebook.com",
        "instagram.com",
        "tiktok.com",

        # Forums / Q&A
        "stackoverflow.com",
        "stackexchange.com",
        "superuser.com",
        "serverfault.com",

        # General-purpose / user-generated reference sites
        "wikipedia.org",
        "quora.com",

        # Academic/social publication platforms where source
        # quality and access are inconsistent for this pipeline.
        "researchgate.net",
        "academia.edu",

        # Presentation / document-sharing platforms
        "slideshare.net",
        "speakerdeck.com",

        # Generic developer tutorial/content platforms
        "geeksforgeeks.org",
        "tutorialspoint.com",
        "w3schools.com",
    }

    # --------------------------------------------------------
    # Standards organizations
    # --------------------------------------------------------

    STANDARDS_DOMAINS = {
        "ietf.org",
        "www.ietf.org",
        "bluetooth.com",
        "www.bluetooth.com",
        "3gpp.org",
        "www.3gpp.org",
        "ieee.org",
        "www.ieee.org",
        "iso.org",
        "www.iso.org",
        "etsi.org",
        "www.etsi.org",
        "oasis-open.org",
        "www.oasis-open.org",
        "w3.org",
        "www.w3.org",
    }

    # --------------------------------------------------------
    # Government / regulatory sources
    # --------------------------------------------------------

    GOVERNMENT_DOMAIN_SUFFIXES = {
        ".gov",
        ".gov.uk",
        ".gov.in",
        ".gov.au",
        ".gov.ca",
        ".gouv.fr",
        ".go.jp",
        ".go.kr",
    }

    # --------------------------------------------------------
    # Reputable technical publications
    #
    # This is deliberately conservative.
    # --------------------------------------------------------

    TECHNICAL_PUBLICATION_DOMAINS = {
        "arstechnica.com",
        "theregister.com",
        "techcrunch.com",
        "computerworld.com",
        "computerweekly.com",
        "zdnet.com",
        "networkworld.com",
        "lightreading.com",
        "fierce-network.com",
        "fierceelectronics.com",
        "tomshardware.com",
        "anandtech.com",
        "servethehome.com",
        "eejournal.com",
        "eetimes.com",
        "electronicsweekly.com",
        "semiconductorengineering.com",
        "sdxcentral.com",
    }

    # --------------------------------------------------------
    # Official source patterns
    #
    # These are domains where the organization itself is the
    # technical source.
    # --------------------------------------------------------

    OFFICIAL_DOMAINS = {
        # Android / Google
        "developer.android.com",
        "source.android.com",
        "android.googlesource.com",
        "developers.google.com",

        # Apple
        "developer.apple.com",
        "support.apple.com",

        # Microsoft
        "learn.microsoft.com",
        "developer.microsoft.com",

        # AWS
        "docs.aws.amazon.com",
        "aws.amazon.com",

        # Microsoft Azure
        "azure.microsoft.com",

        # Google Cloud
        "cloud.google.com",

        # IBM
        "ibm.com",

        # Cisco
        "cisco.com",
        "developer.cisco.com",

        # Nokia
        "nokia.com",
        "www.nokia.com",
        "docs.nokia.com",

        # Samsung
        "samsung.com",
        "developer.samsung.com",

        # Qualcomm
        "qualcomm.com",
        "developer.qualcomm.com",

        # Intel
        "intel.com",
        "developer.intel.com",

        # AMD
        "amd.com",

        # NVIDIA
        "nvidia.com",
        "developer.nvidia.com",

        # ARM
        "arm.com",
        "developer.arm.com",

        # STMicroelectronics
        "st.com",

        # Texas Instruments
        "ti.com",

        # NXP
        "nxp.com",

        # Nordic Semiconductor
        "nordicsemi.com",
        "devzone.nordicsemi.com",

        # Infineon
        "infineon.com",

        # Renesas
        "renesas.com",

        # Bosch
        "bosch.com",

        # LG
        "lg.com",

        # LG Energy Solution
        "lgensol.com",

        # General Motors
        "gm.com",

        # Chevrolet
        "chevrolet.com",

        # Toyota
        "toyota.com",

        # Volkswagen
        "volkswagen.com",

        # Mercedes-Benz
        "mercedes-benz.com",

        # Tesla
        "tesla.com",
    }

    # --------------------------------------------------------
    # Official source repositories
    #
    # GitHub itself is NOT globally trusted.
    # Only explicitly recognized organizations/repositories
    # should be treated as official.
    # --------------------------------------------------------

    OFFICIAL_REPOSITORY_HOSTS = {
        "android.googlesource.com",
    }

    OFFICIAL_GITHUB_ORGANIZATIONS = {
        "android",
        "google",
        "microsoft",
        "apple",
        "nvidia",
        "intel",
        "qualcomm",
        "arm",
        "nokia",
        "cisco",
        "aws",
        "kubernetes",
        "linux",
    }

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------

    def qualify(
        self,
        search_result: SearchResult,
    ) -> SearchResult | None:

        url = str(search_result.url)

        source_type = self.classify_url(url)

        if source_type in {
            self.REJECTED,
            self.UNKNOWN,
        }:
            return None

        quality = self._quality_for_source_type(
            source_type
        )

        return search_result.model_copy(
            update={
                "source_type": source_type,
                "source_quality": quality,
            }
        )

    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    def classify_url(
        self,
        url: str,
    ) -> str:

        parsed = self._parse_url(url)

        if parsed is None:
            return self.REJECTED

        hostname = (
            parsed.hostname or ""
        ).lower()

        hostname = hostname.removeprefix(
            "www."
        )

        path = (
            parsed.path or ""
        ).lower()

        # --------------------------------------------
        # Hard patent exclusion
        # --------------------------------------------

        if self._is_patent(
            hostname,
            path,
        ):
            return self.REJECTED

        # --------------------------------------------
        # Explicit rejection
        # --------------------------------------------

        if self._matches_domain_set(
            hostname,
            self.REJECTED_DOMAINS,
        ):
            return self.REJECTED

        # --------------------------------------------
        # Official / first-party
        # --------------------------------------------

        if self._matches_domain_set(
            hostname,
            self.OFFICIAL_DOMAINS,
        ):
            return self.OFFICIAL

        # --------------------------------------------
        # Standards
        # --------------------------------------------

        if self._matches_domain_set(
            hostname,
            self.STANDARDS_DOMAINS,
        ):
            return self.STANDARDS

        # --------------------------------------------
        # Government / regulatory
        # --------------------------------------------

        if self._is_government_domain(
            hostname
        ):
            return self.GOVERNMENT

        # --------------------------------------------
        # Official GitHub repositories
        # --------------------------------------------

        if self._is_official_github_repository(
            hostname,
            path,
        ):
            return self.OFFICIAL

        # --------------------------------------------
        # Reputable technical publications
        # --------------------------------------------

        if self._matches_domain_set(
            hostname,
            self.TECHNICAL_PUBLICATION_DOMAINS,
        ):
            return self.TECHNICAL_PUBLICATION

        # --------------------------------------------
        # Everything else is not admitted.
        # --------------------------------------------

        return self.UNKNOWN

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------

    def _parse_url(self, url: str):

        try:
            parsed = urlparse(
                str(url)
            )
        except Exception:
            return None

        if not parsed.hostname:
            return None

        return parsed

    def _is_patent(
        self,
        hostname: str,
        path: str,
    ) -> bool:

        if hostname in self.PATENT_DOMAINS:
            return True

        for marker in self.PATENT_PATH_MARKERS:

            if marker in path:
                return True

        return False

    def _matches_domain_set(
        self,
        hostname: str,
        domains: set[str],
    ) -> bool:

        normalized_domains = {
            domain.removeprefix("www.").lower()
            for domain in domains
        }

        if hostname in normalized_domains:
            return True

        for domain in normalized_domains:

            if hostname.endswith(
                "." + domain
            ):
                return True

        return False

    def _is_government_domain(
        self,
        hostname: str,
    ) -> bool:

        for suffix in self.GOVERNMENT_DOMAIN_SUFFIXES:

            if hostname.endswith(suffix):
                return True

        return False

    def _is_official_github_repository(
        self,
        hostname: str,
        path: str,
    ) -> bool:

        if hostname != "github.com":
            return False

        parts = [
            part
            for part in path.split("/")
            if part
        ]

        if not parts:
            return False

        organization = (
            parts[0].lower()
        )

        return (
            organization
            in self.OFFICIAL_GITHUB_ORGANIZATIONS
        )

    def _quality_for_source_type(
        self,
        source_type: str,
    ) -> str:

        if source_type == self.OFFICIAL:
            return "tier_1"

        if source_type in {
            self.STANDARDS,
            self.GOVERNMENT,
        }:
            return "tier_2"

        if source_type == self.TECHNICAL_PUBLICATION:
            return "tier_3"

        return "rejected"
