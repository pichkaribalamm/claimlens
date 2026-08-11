import re

from app.models.schemas import (
    ClaimElement,
    TechnologyProfile,
)


class PageContentReducer:

    def __init__(
        self,
        window_size: int = 220,
        max_chars: int = 4500,
        max_passages: int = 8,
        max_passage_chars: int = 650,
    ):
        self.window_size = window_size
        self.max_chars = max_chars
        self.max_passages = max_passages
        self.max_passage_chars = max_passage_chars

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
        # 3. Rank windows by technical relevance.
        # --------------------------------------------------

        windows.sort(
            key=lambda item: (
                -item[0],
                item[1],
            )
        )

        selected_passages = []

        selected_ranges = []

        total_chars = 0

        # --------------------------------------------------
        # 4. Convert windows into concise passages.
        #
        # The reducer should not pass large arbitrary chunks
        # to the evidence extractor.
        # --------------------------------------------------

        for score, start, end, window in windows:

            if len(selected_passages) >= self.max_passages:
                break

            if self._overlaps_selected_range(
                start,
                end,
                selected_ranges,
            ):
                continue

            passage = self._trim_to_sentence_boundary(
                window
            )

            passage = self._center_relevant_content(
                passage,
                phrases,
                terms,
            )

            passage = passage.strip()

            if not passage:
                continue

            if len(passage) > self.max_passage_chars:

                passage = self._truncate_passage(
                    passage,
                    phrases,
                    terms,
                )

            passage = passage.strip()

            if not passage:
                continue

            remaining_chars = (
                self.max_chars
                - total_chars
            )

            if remaining_chars <= 0:
                break

            if len(passage) > remaining_chars:
                passage = passage[:remaining_chars].rstrip()

            if not passage:
                break

            selected_passages.append(
                passage
            )

            total_chars += len(passage)

            selected_ranges.append(
                (
                    start,
                    end,
                )
            )

            if total_chars >= self.max_chars:
                break

        if not selected_passages:
            return ""

        # --------------------------------------------------
        # 5. Restore document order.
        #
        # The selected passages are currently ranked by score.
        # We sort using their original positions.
        # --------------------------------------------------

        passage_positions = []

        for passage in selected_passages:

            position = normalized_content.find(
                passage
            )

            passage_positions.append(
                (
                    position if position >= 0 else len(
                        normalized_content
                    ),
                    passage,
                )
            )

        passage_positions.sort(
            key=lambda item: item[0]
        )

        passages = [
            passage
            for _, passage in passage_positions
        ]

        return (
            "\n\n"
            "--- RELEVANT PASSAGE ---"
            "\n\n"
            .join(passages)
        )

    # ========================================================
    # CONTENT NORMALIZATION
    # ========================================================

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

    # ========================================================
    # PHRASE EXTRACTION
    # ========================================================

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

    # ========================================================
    # TERM EXTRACTION
    # ========================================================

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

    # ========================================================
    # WINDOW SCORING
    # ========================================================

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

        # --------------------------------------------------
        # Reward technical density.
        #
        # A window containing several relevant terms is
        # preferable to one containing a single isolated
        # generic term.
        # --------------------------------------------------

        if len(matched_terms) >= 3:
            score += 3

        if len(matched_terms) >= 5:
            score += 3

        return score

    # ========================================================
    # SENTENCE BOUNDARY HANDLING
    # ========================================================

    def _trim_to_sentence_boundary(
        self,
        text: str,
    ) -> str:

        text = text.strip()

        if not text:
            return ""

        if len(text) <= self.max_passage_chars:
            return text

        # --------------------------------------------------
        # Prefer complete sentences.
        # --------------------------------------------------

        sentences = re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        if not sentences:
            return text

        selected = []

        total = 0

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:
                continue

            if (
                total + len(sentence) + 1
                > self.max_passage_chars
            ):
                break

            selected.append(
                sentence
            )

            total += (
                len(sentence) + 1
            )

        if selected:
            return " ".join(
                selected
            )

        return text

    # ========================================================
    # CENTER RELEVANT CONTENT
    # ========================================================

    def _center_relevant_content(
        self,
        passage: str,
        phrases: list[str],
        terms: list[str],
    ) -> str:

        if len(passage) <= self.max_passage_chars:
            return passage

        lower_passage = passage.lower()

        best_position = None

        best_score = -1

        # Prefer a longer exact phrase as the center.
        for phrase in phrases:

            position = lower_passage.find(
                phrase
            )

            if position < 0:
                continue

            phrase_score = len(
                phrase.split()
            )

            if phrase_score > best_score:

                best_score = phrase_score
                best_position = position

        # Fall back to the densest technical term.
        if best_position is None:

            for term in terms:

                position = lower_passage.find(
                    term
                )

                if position < 0:
                    continue

                best_position = position
                break

        if best_position is None:
            return passage

        half_window = (
            self.max_passage_chars // 2
        )

        start = max(
            0,
            best_position - half_window,
        )

        end = min(
            len(passage),
            start + self.max_passage_chars,
        )

        return passage[start:end]

    # ========================================================
    # PASSAGE TRUNCATION
    # ========================================================

    def _truncate_passage(
        self,
        passage: str,
        phrases: list[str],
        terms: list[str],
    ) -> str:

        passage = self._center_relevant_content(
            passage,
            phrases,
            terms,
        )

        if len(passage) <= self.max_passage_chars:
            return passage

        return passage[
            :self.max_passage_chars
        ].rstrip()

    # ========================================================
    # OVERLAP CHECKING
    # ========================================================

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

    # ========================================================
    # STOP WORDS
    # ========================================================

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
            "configured",
            "using",
            "based",
            "response",
            "within",
        }

    # ========================================================
    # STOP PHRASES
    # ========================================================

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
