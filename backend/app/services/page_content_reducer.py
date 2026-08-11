import re

from app.models.schemas import (
    ClaimElement,
    TechnologyProfile,
)


class PageContentReducer:

    def __init__(
        self,
        max_chars: int = 5000,
        max_passages: int = 10,
        max_passage_chars: int = 500,
    ):
        self.max_chars = max_chars
        self.max_passages = max_passages
        self.max_passage_chars = max_passage_chars

    # ============================================================
    # MAIN REDUCTION
    # ============================================================

    def reduce(
        self,
        claim_element: ClaimElement,
        page_content: str,
        technology_profile: TechnologyProfile | None = None,
    ) -> str:

        if not page_content:
            return ""

        normalized_content = self._normalize_content(
            page_content
        )

        if not normalized_content:
            return ""

        sentences = self._split_sentences(
            normalized_content
        )

        if not sentences:
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

        scored_sentences = []

        for index, sentence in enumerate(
            sentences
        ):

            score = self._score_sentence(
                sentence=sentence,
                phrases=phrases,
                terms=terms,
            )

            if score <= 0:
                continue

            scored_sentences.append(
                (
                    score,
                    index,
                    sentence,
                )
            )

        if not scored_sentences:
            return ""

        # Highest scoring sentences first.
        scored_sentences.sort(
            key=lambda item: (
                -item[0],
                item[1],
            )
        )

        candidate_passages = []

        for (
            score,
            index,
            sentence,
        ) in scored_sentences:

            passage_indexes = (
                self._build_passage_indexes(
                    index=index,
                    sentences=sentences,
                    phrases=phrases,
                    terms=terms,
                )
            )

            if not passage_indexes:
                continue

            passage = " ".join(
                sentences[position]
                for position in passage_indexes
            ).strip()

            if not passage:
                continue

            if len(passage) > self.max_passage_chars:
                passage = self._trim_passage(
                    passage=passage,
                    phrases=phrases,
                    terms=terms,
                    max_chars=self.max_passage_chars,
                )

            passage = passage.strip()

            if not passage:
                continue

            passage_score = self._score_passage(
                passage=passage,
                phrases=phrases,
                terms=terms,
            )

            candidate_passages.append(
                (
                    passage_score,
                    passage_indexes[0],
                    passage_indexes[-1],
                    passage,
                )
            )

        if not candidate_passages:
            return ""

        # Highest-value passages first.
        candidate_passages.sort(
            key=lambda item: (
                -item[0],
                item[1],
            )
        )

        selected_passages = []
        selected_ranges = []

        total_chars = 0

        for (
            score,
            start_index,
            end_index,
            passage,
        ) in candidate_passages:

            if len(selected_passages) >= (
                self.max_passages
            ):
                break

            if self._overlaps_selected_range(
                start_index,
                end_index,
                selected_ranges,
            ):
                continue

            separator_chars = (
                2
                if selected_passages
                else 0
            )

            remaining_chars = (
                self.max_chars
                - total_chars
                - separator_chars
            )

            if remaining_chars <= 0:
                break

            if len(passage) > remaining_chars:

                passage = self._trim_passage(
                    passage=passage,
                    phrases=phrases,
                    terms=terms,
                    max_chars=remaining_chars,
                )

            passage = passage.strip()

            if not passage:
                continue

            if len(passage) > remaining_chars:
                continue

            selected_passages.append(
                (
                    start_index,
                    end_index,
                    passage,
                )
            )

            selected_ranges.append(
                (
                    start_index,
                    end_index,
                )
            )

            total_chars += (
                len(passage)
                + separator_chars
            )

            if total_chars >= self.max_chars:
                break

        if not selected_passages:
            return ""

        # Restore original document order.
        selected_passages.sort(
            key=lambda item: item[0]
        )

        passages = [
            passage
            for _, _, passage
            in selected_passages
        ]

        return (
            "\n\n"
            "--- RELEVANT PASSAGE ---"
            "\n\n"
            .join(passages)
        )

    # ============================================================
    # CONTENT NORMALIZATION
    # ============================================================

    def _normalize_content(
        self,
        content: str,
    ) -> str:

        # Preserve wording while removing excessive whitespace.
        #
        # Do not rewrite punctuation or wording because the
        # evidence extractor must later be able to copy exact
        # source wording.

        content = content.replace(
            "\r\n",
            "\n",
        )

        content = re.sub(
            r"[ \t]+",
            " ",
            content,
        )

        content = re.sub(
            r"\n+",
            "\n",
            content,
        )

        return content.strip()

    # ============================================================
    # SENTENCE SEGMENTATION
    # ============================================================

    def _split_sentences(
        self,
        content: str,
    ) -> list[str]:

        if not content:
            return []

        blocks = re.split(
            r"\n+",
            content,
        )

        sentences = []

        for block in blocks:

            block = block.strip()

            if not block:
                continue

            # Split ordinary sentence boundaries.
            #
            # This remains deterministic and dependency-free.

            parts = re.split(
                r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])",
                block,
            )

            for part in parts:

                part = part.strip()

                if not part:
                    continue

                sentences.append(
                    part
                )

        return sentences

    # ============================================================
    # PHRASE EXTRACTION
    # ============================================================

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

            max_phrase_size = min(
                6,
                len(words),
            )

            for size in range(
                max_phrase_size,
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

                    if len(phrase) < 5:
                        continue

                    if (
                        phrase
                        in self._stop_phrases()
                    ):
                        continue

                    if phrase not in phrases:
                        phrases.append(
                            phrase
                        )

        # Longer phrases are more discriminative.
        phrases.sort(
            key=lambda phrase: (
                -len(phrase.split()),
                -len(phrase),
            )
        )

        return phrases

    # ============================================================
    # TERM EXTRACTION
    # ============================================================

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

                if (
                    word
                    in self._stop_words()
                ):
                    continue

                if word not in terms:
                    terms.append(
                        word
                    )

        return terms

    # ============================================================
    # SENTENCE SCORING
    # ============================================================

    def _score_sentence(
        self,
        sentence: str,
        phrases: list[str],
        terms: list[str],
    ) -> int:

        lower_sentence = (
            sentence.lower()
        )

        score = 0

        # --------------------------------------------------------
        # Exact multi-word technical phrases.
        # --------------------------------------------------------

        for phrase in phrases:

            if phrase not in lower_sentence:
                continue

            word_count = len(
                phrase.split()
            )

            if word_count >= 5:
                score += 12

            elif word_count == 4:
                score += 10

            elif word_count == 3:
                score += 8

            else:
                score += 5

        # --------------------------------------------------------
        # Individual technical terms.
        # --------------------------------------------------------

        matched_terms = set()

        for term in terms:

            if re.search(
                rf"\b{re.escape(term)}\b",
                lower_sentence,
            ):

                matched_terms.add(
                    term
                )

        score += min(
            len(matched_terms) * 2,
            14,
        )

        # --------------------------------------------------------
        # Technical density.
        # --------------------------------------------------------

        if len(matched_terms) >= 3:
            score += 4

        if len(matched_terms) >= 5:
            score += 4

        # --------------------------------------------------------
        # Technical relationship language.
        #
        # These are deliberately weighted because a sentence
        # describing an actual operation or relationship is more
        # useful than one merely mentioning a component.
        # --------------------------------------------------------

        relationship_terms = {
            "configured to",
            "adapted to",
            "responsive to",
            "in response to",
            "based on",
            "receives",
            "receive",
            "transmits",
            "transmit",
            "sends",
            "send",
            "routes",
            "route",
            "stores",
            "store",
            "writes",
            "write",
            "reads",
            "read",
            "controls",
            "control",
            "connects",
            "connect",
            "communicates",
            "communication",
            "determines",
            "determine",
            "identifies",
            "identify",
            "selects",
            "select",
            "generates",
            "generate",
            "processes",
            "process",
            "classifies",
            "classify",
            "redirects",
            "redirect",
            "forwards",
            "forward",
            "steers",
            "steer",
        }

        relationship_matches = sum(
            1
            for term in relationship_terms
            if term in lower_sentence
        )

        score += min(
            relationship_matches * 4,
            12,
        )

        # --------------------------------------------------------
        # Conditional / causal language.
        #
        # Especially valuable for claims containing relationships
        # such as "in response to", "based on", "when", etc.
        # --------------------------------------------------------

        conditional_terms = {
            "if",
            "when",
            "in response",
            "based on",
            "according to",
            "depending on",
            "upon determining",
            "after determining",
        }

        conditional_matches = sum(
            1
            for term in conditional_terms
            if term in lower_sentence
        )

        score += min(
            conditional_matches * 4,
            8,
        )

        # --------------------------------------------------------
        # Penalize extremely generic sentences.
        # --------------------------------------------------------

        generic_phrases = {
            "learn more",
            "contact us",
            "our products",
            "our company",
            "welcome to",
            "privacy policy",
            "terms of use",
            "copyright",
        }

        if any(
            phrase in lower_sentence
            for phrase in generic_phrases
        ):
            score -= 10

        return max(
            score,
            0,
        )

    # ============================================================
    # PASSAGE SCORING
    # ============================================================

    def _score_passage(
        self,
        passage: str,
        phrases: list[str],
        terms: list[str],
    ) -> int:

        score = self._score_sentence(
            passage,
            phrases,
            terms,
        )

        lower_passage = (
            passage.lower()
        )

        matched_terms = {
            term
            for term in terms
            if re.search(
                rf"\b{re.escape(term)}\b",
                lower_passage,
            )
        }

        score += min(
            len(matched_terms),
            8,
        )

        return score

    # ============================================================
    # PASSAGE CONSTRUCTION
    # ============================================================

    def _build_passage_indexes(
        self,
        index: int,
        sentences: list[str],
        phrases: list[str],
        terms: list[str],
    ) -> list[int]:

        if index < 0:
            return []

        if index >= len(sentences):
            return []

        indexes = [
            index
        ]

        current_length = len(
            sentences[index]
        )

        # --------------------------------------------------------
        # Add ONE neighboring sentence when it provides meaningful
        # technical context or completes a relationship.
        # --------------------------------------------------------

        neighbors = []

        if index + 1 < len(sentences):
            neighbors.append(
                index + 1
            )

        if index - 1 >= 0:
            neighbors.append(
                index - 1
            )

        best_neighbor = None
        best_neighbor_score = 0

        for neighbor_index in neighbors:

            neighbor = sentences[
                neighbor_index
            ]

            neighbor_score = self._score_sentence(
                sentence=neighbor,
                phrases=phrases,
                terms=terms,
            )

            lower_neighbor = (
                neighbor.lower()
            )

            # Strongly prefer explicit technical relationships.
            if any(
                relationship in lower_neighbor
                for relationship in (
                    "based on",
                    "in response to",
                    "configured to",
                    "responsive to",
                    "determines",
                    "identifies",
                    "selects",
                    "routes",
                    "forwards",
                    "redirects",
                    "steers",
                    "using",
                )
            ):
                neighbor_score += 5

            if (
                neighbor_score
                > best_neighbor_score
            ):
                best_neighbor_score = (
                    neighbor_score
                )
                best_neighbor = (
                    neighbor_index
                )

        # Only add a neighbor when it provides meaningful
        # technical value.
        if (
            best_neighbor is not None
            and best_neighbor_score >= 7
        ):

            proposed_length = (
                current_length
                + 1
                + len(
                    sentences[
                        best_neighbor
                    ]
                )
            )

            if (
                proposed_length
                <= self.max_passage_chars
            ):

                indexes.append(
                    best_neighbor
                )

        # --------------------------------------------------------
        # IMPORTANT:
        #
        # Do NOT automatically add a third sentence.
        #
        # The previous reducer occasionally expanded passages to
        # three sentences based on surrounding scores. That can
        # turn a useful evidence-bearing sentence into a large
        # paragraph.
        #
        # We still allow 2-sentence passages when context genuinely
        # helps, while keeping the normal evidence unit compact.
        # --------------------------------------------------------

        indexes.sort()

        return indexes

    # ============================================================
    # PASSAGE TRIMMING
    # ============================================================

    def _trim_passage(
        self,
        passage: str,
        phrases: list[str],
        terms: list[str],
        max_chars: int | None = None,
    ) -> str:

        limit = (
            max_chars
            if max_chars is not None
            else self.max_passage_chars
        )

        if len(passage) <= limit:
            return passage

        sentences = self._split_sentences(
            passage
        )

        if not sentences:
            return passage[
                :limit
            ].rstrip()

        # Prefer complete sentences.
        #
        # Never intentionally cut an evidence-bearing sentence
        # in the middle when a shorter complete sentence is
        # available.

        selected = []
        total = 0

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:
                continue

            additional = len(
                sentence
            )

            if selected:
                additional += 1

            if (
                total + additional
                > limit
            ):
                break

            selected.append(
                sentence
            )

            total += additional

        if selected:
            return " ".join(
                selected
            ).strip()

        # Last resort for a single extremely long sentence.
        return passage[
            :limit
        ].rstrip()

    # ============================================================
    # OVERLAP CHECKING
    # ============================================================

    def _overlaps_selected_range(
        self,
        start: int,
        end: int,
        selected_ranges: list[
            tuple[int, int]
        ],
    ) -> bool:

        for (
            selected_start,
            selected_end,
        ) in selected_ranges:

            if (
                start <= selected_end
                and end >= selected_start
            ):
                return True

        return False

    # ============================================================
    # STOP WORDS
    # ============================================================

    def _stop_words(
        self,
    ) -> set[str]:

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
            "using",
            "based",
            "response",
            "within",
            "through",
            "such",
            "each",
            "other",
            "one",
            "more",
            "than",
            "onto",
            "upon",
            "where",
            "which",
            "whose",
            "their",
            "there",
            "then",
            "when",
            "being",
            "also",
            "may",
            "can",
            "include",
            "including",
            "comprises",
            "comprise",
        }

    # ============================================================
    # STOP PHRASES
    # ============================================================

    def _stop_phrases(
        self,
    ) -> set[str]:

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
            "the component",
            "claim element",
            "a system",
            "a device",
            "a method",
            "configured to",
            "in response",
            "based on",
        }
