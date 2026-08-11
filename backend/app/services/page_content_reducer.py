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
        max_passage_chars: int = 700,
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

        # --------------------------------------------------------
        # Score every sentence.
        # --------------------------------------------------------

        sentence_scores = []

        for index, sentence in enumerate(
            sentences
        ):

            score = self._score_sentence(
                sentence=sentence,
                phrases=phrases,
                terms=terms,
            )

            sentence_scores.append(
                (
                    score,
                    index,
                    sentence,
                )
            )

        # --------------------------------------------------------
        # Candidate anchors.
        #
        # We still need at least one technically relevant sentence
        # to anchor a passage, but we no longer require every
        # sentence in the final passage to independently match
        # claim terminology.
        # --------------------------------------------------------

        anchor_sentences = [
            item
            for item in sentence_scores
            if item[0] >= 4
        ]

        if not anchor_sentences:
            return ""

        # Highest-value anchors first.
        anchor_sentences.sort(
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
        ) in anchor_sentences:

            passage_indexes = (
                self._build_passage_indexes(
                    index=index,
                    sentences=sentences,
                    sentence_scores=sentence_scores,
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

        # --------------------------------------------------------
        # Highest-value passages first.
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # Restore original document order.
        # --------------------------------------------------------

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

            # ----------------------------------------------------
            # Preserve reasonably sized technical sentences.
            # ----------------------------------------------------

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
                5,
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

        matched_phrases = set()

        for phrase in phrases:

            if phrase not in lower_sentence:
                continue

            matched_phrases.add(
                phrase
            )

            word_count = len(
                phrase.split()
            )

            if word_count >= 5:
                score += 10

            elif word_count == 4:
                score += 8

            elif word_count == 3:
                score += 6

            else:
                score += 3

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
            16,
        )

        # --------------------------------------------------------
        # Technical density.
        # --------------------------------------------------------

        if len(matched_terms) >= 3:
            score += 3

        if len(matched_terms) >= 5:
            score += 3

        # --------------------------------------------------------
        # Technical relationship language.
        #
        # This is particularly important for claims where the
        # invention lies in the relationship between components,
        # rather than in the components themselves.
        # --------------------------------------------------------

        relationship_terms = {
            "configured to",
            "adapted to",
            "responsive to",
            "in response to",
            "based on",
            "based upon",
            "receives",
            "receive",
            "received",
            "receiving",
            "from",
            "through",
            "entering",
            "enters",
            "enter",
            "originating",
            "originates",
            "sends",
            "send",
            "sending",
            "transmits",
            "transmit",
            "transmitting",
            "routes",
            "route",
            "routing",
            "routed",
            "stores",
            "store",
            "storing",
            "writes",
            "write",
            "writing",
            "reads",
            "read",
            "reading",
            "controls",
            "control",
            "controlling",
            "connects",
            "connect",
            "connecting",
            "communicates",
            "communicate",
            "communication",
            "determines",
            "determine",
            "determining",
            "identifies",
            "identify",
            "identifying",
            "selects",
            "select",
            "selecting",
            "generates",
            "generate",
            "generating",
            "processes",
            "process",
            "processing",
            "classifies",
            "classify",
            "classifying",
            "redirects",
            "redirect",
            "redirecting",
            "forwards",
            "forward",
            "forwarding",
            "steers",
            "steer",
            "steering",
            "handles",
            "handle",
            "handling",
            "satisfies",
            "satisfy",
            "satisfying",
        }

        relationship_matches = sum(
            1
            for term in relationship_terms
            if re.search(
                rf"\b{re.escape(term)}\b",
                lower_sentence,
            )
        )

        score += min(
            relationship_matches * 4,
            16,
        )

        # --------------------------------------------------------
        # Conditional / causal language.
        # --------------------------------------------------------

        conditional_terms = {
            "if",
            "when",
            "in response",
            "based on",
            "based upon",
            "according to",
            "depending on",
            "upon determining",
            "after determining",
            "once",
            "whenever",
            "provided that",
            "in response to determining",
        }

        conditional_matches = sum(
            1
            for term in conditional_terms
            if term in lower_sentence
        )

        score += min(
            conditional_matches * 5,
            10,
        )

        # --------------------------------------------------------
        # Structural / architectural language.
        #
        # Useful for sources that explain how components interact
        # without using the same terminology as the claim.
        # --------------------------------------------------------

        architecture_terms = {
            "controller",
            "control plane",
            "data plane",
            "edge",
            "network",
            "traffic",
            "packet",
            "flow",
            "ingress",
            "egress",
            "gateway",
            "node",
            "system",
            "service",
            "interface",
            "request",
            "response",
            "information",
            "data",
            "criteria",
            "rule",
            "policy",
            "classification",
            "classifier",
            "decision",
            "destination",
            "source",
        }

        architecture_matches = sum(
            1
            for term in architecture_terms
            if re.search(
                rf"\b{re.escape(term)}\b",
                lower_sentence,
            )
        )

        # Architecture terms are useful, but should not dominate
        # genuine claim-term or relationship matches.
        score += min(
            architecture_matches,
            6,
        )

        # --------------------------------------------------------
        # Penalize extremely generic page material.
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
            "sign up",
            "all rights reserved",
        }

        if any(
            phrase in lower_sentence
            for phrase in generic_phrases
        ):

            score -= 12

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

        sentences = self._split_sentences(
            passage
        )

        if not sentences:
            return 0

        # Score each sentence independently first.
        sentence_scores = [
            self._score_sentence(
                sentence,
                phrases,
                terms,
            )
            for sentence in sentences
        ]

        score = sum(
            sentence_scores
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

        # --------------------------------------------------------
        # Reward passages that contain both technical terminology
        # and relationship language.
        # --------------------------------------------------------

        relationship_markers = (
            "based on",
            "in response",
            "receiving",
            "received from",
            "through",
            "entering",
            "routing",
            "routes",
            "determining",
            "identifying",
            "satisfies",
            "redirecting",
            "forwarding",
            "selecting",
        )

        relationship_count = sum(
            1
            for marker in relationship_markers
            if marker in lower_passage
        )

        if (
            relationship_count >= 1
            and len(matched_terms) >= 2
        ):
            score += 6

        if (
            relationship_count >= 2
            and len(matched_terms) >= 3
        ):
            score += 6

        # --------------------------------------------------------
        # Reward multi-sentence technical chains.
        #
        # This is the key change from the previous reducer.
        # A sequence such as:
        #
        #   receives traffic
        #       ↓
        #   determines criteria
        #       ↓
        #   routes traffic
        #
        # can now survive as one candidate passage.
        # --------------------------------------------------------

        if len(sentences) >= 2:

            if any(
                value >= 5
                for value in sentence_scores
            ):

                score += 3

        if len(sentences) >= 3:

            high_value_sentences = sum(
                1
                for value in sentence_scores
                if value >= 5
            )

            if high_value_sentences >= 2:
                score += 5

        return score

    # ============================================================
    # PASSAGE CONSTRUCTION
    # ============================================================

    def _build_passage_indexes(
        self,
        index: int,
        sentences: list[str],
        sentence_scores: list[
            tuple[int, int, str]
        ],
        phrases: list[str],
        terms: list[str],
    ) -> list[int]:

        if index < 0:
            return []

        if index >= len(sentences):
            return []

        # --------------------------------------------------------
        # Start with the anchor sentence.
        # --------------------------------------------------------

        indexes = [
            index
        ]

        # --------------------------------------------------------
        # Consider up to TWO neighboring sentences on each side.
        #
        # We don't automatically include all of them. We choose
        # the strongest compact window.
        # --------------------------------------------------------

        candidate_windows = []

        # 1 sentence
        candidate_windows.append(
            [index]
        )

        # Anchor + next
        if index + 1 < len(sentences):

            candidate_windows.append(
                [
                    index,
                    index + 1,
                ]
            )

        # Previous + anchor
        if index - 1 >= 0:

            candidate_windows.append(
                [
                    index - 1,
                    index,
                ]
            )

        # Previous + anchor + next
        if (
            index - 1 >= 0
            and index + 1 < len(sentences)
        ):

            candidate_windows.append(
                [
                    index - 1,
                    index,
                    index + 1,
                ]
            )

        # Previous two + anchor
        if index - 2 >= 0:

            candidate_windows.append(
                [
                    index - 2,
                    index - 1,
                    index,
                ]
            )

        # Anchor + next two
        if index + 2 < len(sentences):

            candidate_windows.append(
                [
                    index,
                    index + 1,
                    index + 2,
                ]
            )

        # --------------------------------------------------------
        # Evaluate candidate windows.
        # --------------------------------------------------------

        best_window = [index]
        best_score = self._score_passage(
            sentences[index],
            phrases,
            terms,
        )

        for window in candidate_windows:

            passage = " ".join(
                sentences[position]
                for position in window
            ).strip()

            if not passage:
                continue

            if len(passage) > self.max_passage_chars:
                continue

            window_score = self._score_passage(
                passage,
                phrases,
                terms,
            )

            # ----------------------------------------------------
            # Context bridge bonus.
            #
            # If a neighboring sentence contains few direct
            # keywords but connects two technically strong
            # sentences, keeping it can be valuable.
            # ----------------------------------------------------

            if len(window) == 3:

                middle_index = window[1]

                middle_score = self._score_sentence(
                    sentences[middle_index],
                    phrases,
                    terms,
                )

                outer_scores = [
                    self._score_sentence(
                        sentences[window[0]],
                        phrases,
                        terms,
                    ),
                    self._score_sentence(
                        sentences[window[2]],
                        phrases,
                        terms,
                    ),
                ]

                if (
                    middle_score < 5
                    and all(
                        value >= 5
                        for value in outer_scores
                    )
                ):

                    window_score += 8

            # Prefer a longer window when it adds meaningful
            # technical context, but don't reward length by itself.
            if (
                window_score > best_score
                or (
                    window_score == best_score
                    and len(window)
                    > len(best_window)
                )
            ):

                best_window = window
                best_score = window_score

        return sorted(
            set(best_window)
        )

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

        # --------------------------------------------------------
        # Prefer complete sentences.
        # --------------------------------------------------------

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

        # --------------------------------------------------------
        # Last resort for one extremely long sentence.
        #
        # This is unavoidable if the source itself has a sentence
        # longer than the configured passage limit.
        # --------------------------------------------------------

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
