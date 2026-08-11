import re

from app.models.schemas import (
    ClaimElement,
    TechnologyProfile,
)


class PageContentReducer:

    def __init__(
        self,
        window_size: int = 450,
        max_chars: int = 5000,
        max_passages: int = 6,
    ):
        self.window_size = window_size
        self.max_chars = max_chars
        self.max_passages = max_passages

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

        normalized_content = self._normalize_content(
            page_content
        )

        if not normalized_content:
            return ""

        windows = []

        # --------------------------------------------------
        # 1. Search exact multi-word technical phrases.
        # --------------------------------------------------

        for phrase in phrases:

            for match in re.finditer(
                re.escape(phrase),
                normalized_content,
            ):

                start = max(
                    0,
                    match.start() - self.window_size,
                )

                end = min(
                    len(normalized_content),
                    match.end() + self.window_size,
                )

                window = normalized_content[start:end]

                score = self._score_window(
                    window,
                    phrases,
                    terms,
                )

                if score > 0:

                    windows.append(
                        (
                            score,
                            start,
                            end,
                            window,
                        )
                    )

        # --------------------------------------------------
        # 2. Search individual technical terms.
        # --------------------------------------------------

        for term in terms:

            for match in re.finditer(
                rf"\b{re.escape(term)}\b",
                normalized_content,
            ):

                start = max(
                    0,
                    match.start() - self.window_size,
                )

                end = min(
                    len(normalized_content),
                    match.end() + self.window_size,
                )

                window = normalized_content[start:end]

                score = self._score_window(
                    window,
                    phrases,
                    terms,
                )

                if score > 0:

                    windows.append(
                        (
                            score,
                            start,
                            end,
                            window,
                        )
                    )

        if not windows:
            return ""

        # --------------------------------------------------
        # 3. Rank windows.
        # --------------------------------------------------

        windows.sort(
            key=lambda item: (
                -item[0],
                item[1],
            )
        )

        selected_ranges = []

        for score, start, end, window in windows:

            if self._overlaps_selected_range(
                start,
                end,
                selected_ranges,
            ):
                continue

            selected_ranges.append(
                (
                    start,
                    end,
                )
            )

            if (
                len(selected_ranges)
                >= self.max_passages
            ):
                break

        if not selected_ranges:
            return ""

        # --------------------------------------------------
        # 4. Restore document order.
        # --------------------------------------------------

        selected_ranges.sort()

        passages = []

        total_chars = 0

        for start, end in selected_ranges:

            passage = normalized_content[
                start:end
            ].strip()

            if not passage:
                continue

            # --------------------------------------------------
            # Avoid adding a passage that would exceed the
            # total character budget.
            # --------------------------------------------------

            remaining = (
                self.max_chars
                - total_chars
            )

            if remaining <= 0:
                break

            if len(passage) > remaining:

                passage = passage[
                    :remaining
                ].rstrip()

            if not passage:
                break

            passages.append(
                passage
            )

            total_chars += len(passage)

            if total_chars >= self.max_chars:
                break

        if not passages:
            return ""

        return (
            "\n\n"
            "--- RELEVANT PASSAGE ---"
            "\n\n"
            .join(passages)
        )

    def _normalize_content(
        self,
        content: str,
    ) -> str:

        content = re.sub(
            r"\s+",
            " ",
            content,
        )

        return content.strip()

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

            if not text:
                continue

            normalized = re.sub(
                r"\s+",
                " ",
                text.lower(),
            ).strip()

            if not normalized:
                continue

            words = normalized.split()

            # Prefer longer phrases because they carry
            # more technical meaning.
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

                    if len(phrase) < 4:
                        continue

                    if phrase in self._stop_phrases():
                        continue

                    if phrase not in phrases:
                        phrases.append(
                            phrase
                        )

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

            if not text:
                continue

            words = re.findall(
                r"\b[a-zA-Z][a-zA-Z0-9-]{2,}\b",
                text.lower(),
            )

            for word in words:

                if word in self._stop_words():
                    continue

                if word not in terms:
                    terms.append(
                        word
                    )

        return terms

    def _score_window(
        self,
        window: str,
        phrases: list[str],
        terms: list[str],
    ) -> int:

        lower_window = window.lower()

        score = 0

        # --------------------------------------------------
        # Exact technical phrases.
        #
        # Longer phrases receive more weight.
        # --------------------------------------------------

        for phrase in phrases:

            if phrase in lower_window:

                word_count = len(
                    phrase.split()
                )

                if word_count >= 4:
                    score += 8
                elif word_count == 3:
                    score += 6
                elif word_count == 2:
                    score += 4
                else:
                    score += 2

        # --------------------------------------------------
        # Individual technical terms.
        # --------------------------------------------------

        matched_terms = set()

        for term in terms:

            if re.search(
                rf"\b{re.escape(term)}\b",
                lower_window,
            ):

                matched_terms.add(
                    term
                )

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

        for (
            selected_start,
            selected_end,
        ) in selected_ranges:

            if (
                start < selected_end
                and end > selected_start
            ):
                return True

        return False

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
            "third",
            "method",
            "system",
            "device",
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
            "a system",
            "a device",
        }
