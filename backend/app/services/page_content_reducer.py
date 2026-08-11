import re

from app.models.schemas import (
    ClaimElement,
    TechnologyProfile,
)


class PageContentReducer:

    def __init__(
        self,
        window_size: int = 600,
        max_chars: int = 12000,
    ):
        self.window_size = window_size
        self.max_chars = max_chars

    def reduce(
        self,
        claim_element: ClaimElement,
        page_content: str,
        technology_profile: TechnologyProfile | None = None,
    ) -> str:

        if not page_content:
            return ""

        terms = self._extract_terms(
            claim_element,
            technology_profile,
        )

        if not terms:
            return ""

        lower_content = page_content.lower()

        windows = []

        for term in terms:

            for match in re.finditer(
                re.escape(term),
                lower_content,
            ):
                start = max(
                    0,
                    match.start() - self.window_size,
                )

                end = min(
                    len(page_content),
                    match.end() + self.window_size,
                )

                windows.append(
                    (start, end)
                )

        if not windows:
            return ""

        merged_windows = self._merge_windows(
            windows
        )

        selected = []

        total_chars = 0

        for start, end in merged_windows:

            window = page_content[start:end]

            if total_chars + len(window) > self.max_chars:
                remaining = (
                    self.max_chars - total_chars
                )

                if remaining <= 0:
                    break

                window = window[:remaining]

            selected.append(window)

            total_chars += len(window)

            if total_chars >= self.max_chars:
                break

        return "\n\n--- RELEVANT PASSAGE ---\n\n".join(
            selected
        )

    def _extract_terms(
        self,
        claim_element: ClaimElement,
        technology_profile: TechnologyProfile | None = None,
    ) -> list[str]:

        texts = [
            claim_element.text,
        ]

        if technology_profile:

            texts.append(
                technology_profile.core_concept
            )

            texts.extend(
                technology_profile.technical_concepts
            )

            texts.extend(
                technology_profile.alternative_terminology
            )

            texts.extend(
                technology_profile.likely_components
            )

        terms = []

        for text in texts:

            words = re.findall(
                r"\b[a-zA-Z][a-zA-Z0-9-]{2,}\b",
                text.lower(),
            )

            for word in words:

                if word in self._stop_words():
                    continue

                if word not in terms:
                    terms.append(word)

        return terms

    def _stop_words(self) -> set[str]:

        return {
            "the",
            "and",
            "configured",
            "comprising",
            "wherein",
            "thereof",
            "that",
            "with",
            "from",
            "into",
            "for",
            "having",
            "said",
        }

    def _merge_windows(
        self,
        windows: list[tuple[int, int]],
    ) -> list[tuple[int, int]]:

        windows.sort()

        merged = []

        for start, end in windows:

            if not merged:
                merged.append(
                    (start, end)
                )
                continue

            previous_start, previous_end = (
                merged[-1]
            )

            if start <= previous_end:
                merged[-1] = (
                    previous_start,
                    max(
                        previous_end,
                        end,
                    ),
                )
            else:
                merged.append(
                    (start, end)
                )

        return merged
