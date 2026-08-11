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

        phrases = self._extract_phrases(
            claim_element,
            technology_profile,
        )

        terms = self._extract_terms(
            claim_element,
            technology_profile,
        )

        if not phrases and not terms:
            return ""

        lower_content = page_content.lower()

        windows = []

        # --------------------------------------------------
        # 1. Prefer exact multi-word technical phrases.
        # --------------------------------------------------

        for phrase in phrases:

            for match in re.finditer(
                re.escape(phrase),
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

                score = self._score_window(
                    page_content[start:end],
                    phrases,
                    terms,
                )

                windows.append(
                    (
                        score,
                        start,
                        end,
                    )
                )

        # --------------------------------------------------
        # 2. Also consider individual technical terms.
        #
        # This preserves support for cases where the page
        # uses alternative terminology such as "ISP".
        # --------------------------------------------------

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

                score = self._score_window(
                    page_content[start:end],
                    phrases,
                    terms,
                )

                windows.append(
                    (
                        score,
                        start,
                        end,
                    )
                )

        if not windows:
            return ""

        # --------------------------------------------------
        # 3. Rank windows by technical relevance.
        # --------------------------------------------------

        windows.sort(
            key=lambda item: (
                -item[0],
                item[1],
            )
        )

        selected_ranges = []

        for score, start, end in windows:

            if score <= 0:
                continue

            if self._overlaps_selected_range(
                start,
                end,
                selected_ranges,
            ):
                continue

            selected_ranges.append(
                (start, end)
            )

            if self._covered_chars(
                selected_ranges
            ) >= self.max_chars:
                break

        if not selected_ranges:
            return ""

        # Restore document order.
        selected_ranges.sort()

        selected = []

        total_chars = 0

        for start, end in selected_ranges:

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

    def _extract_phrases(
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

        phrases = []

        for text in texts:

            normalized = re.sub(
                r"\s+",
                " ",
                text.lower(),
            ).strip()

            if not normalized:
                continue

            words = normalized.split()

            # Keep useful 2-5 word technical phrases.
            for size in range(
                min(5, len(words)),
                1,
                -1,
            ):

                for index in range(
                    len(words) - size + 1
                ):

                    phrase = " ".join(
                        words[
                            index:index + size
                        ]
                    )

                    phrase = re.sub(
                        r"^[^a-z0-9]+|[^a-z0-9]+$",
                        "",
                        phrase,
                    )

                    if not phrase:
                        continue

                    if (
                        len(phrase) < 4
                        or phrase in self._stop_phrases()
                    ):
                        continue

                    if phrase not in phrases:
                        phrases.append(phrase)

        return phrases

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

    def _score_window(
        self,
        window: str,
        phrases: list[str],
        terms: list[str],
    ) -> int:

        lower_window = window.lower()

        score = 0

        # Exact multi-word phrases are much stronger
        # indicators of relevance than isolated words.
        for phrase in phrases:

            if phrase in lower_window:

                word_count = len(
                    phrase.split()
                )

                score += 3 + word_count

        # Individual terms provide fallback support
        # for alternative terminology such as ISP.
        matched_terms = set()

        for term in terms:

            if re.search(
                rf"\b{re.escape(term)}\b",
                lower_window,
            ):
                matched_terms.add(term)

        score += min(
            len(matched_terms),
            8,
        )

        return score

    def _overlaps_selected_range(
        self,
        start: int,
        end: int,
        selected_ranges: list[tuple[int, int]],
    ) -> bool:

        for selected_start, selected_end in selected_ranges:

            if (
                start < selected_end
                and end > selected_start
            ):
                return True

        return False

    def _covered_chars(
        self,
        ranges: list[tuple[int, int]],
    ) -> int:

        return sum(
            end - start
            for start, end in ranges
        )

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
            "this",
            "these",
            "those",
            "whether",
            "certain",
            "first",
            "second",
        }

    def _stop_phrases(self) -> set[str]:

        return {
            "the",
            "and",
            "for",
            "with",
            "from",
            "this",
            "that",
            "the device",
            "the system",
            "the method",
            "claim element",
        }
