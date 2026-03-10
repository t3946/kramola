from typing import List, Dict, Optional
from services.fulltext_search.phrase import Phrase
from services.words_list.list_inagents_fiz import ListInagentsFIZ
from services.words_list.list_inagents_ur import ListInagentsUR
from services.words_list.list_profanity import ListProfanity
from services.words_list.list_prohibited_substances import ListProhibitedSubstances
from services.words_list.list_dangerous_words import ListDangerousWords
from services.words_list.list_extremists_terrorists import ListExtremistsTerrorists
from services.words_list.list_extremists_international_fiz import ListExtremistsInternationalFIZ
from services.words_list.list_extremists_international_ur import ListExtremistsInternationalUR
from services.words_list.list_extremists_russian_fiz import ListExtremistsRussianFIZ
from services.words_list.list_extremists_russian_ur import ListExtremistsRussianUR
from services.words_list.list_from_text import ListFromText
from services.words_list.list_from_text_exclude import ListFromTextExclude
from services.enum import PredefinedListKey
from services.utils.regex_pattern import RegexPattern
from services.patterns.profanity_words import PROFANITY_WORDS_PATTERNS


class AnalysisData:
    phrases: list[Phrase]
    regex_patterns: List[RegexPattern]

    def __init__(self) -> None:
        self.phrases = []
        self.regex_patterns = []

    def read_regex_patterns(self, patterns: Dict[str, str]) -> None:
        """Load regex patterns for search.

        Args:
            patterns: Dictionary mapping pattern_name to pattern_string
        """
        for pattern_name, pattern_str in patterns.items():
            if pattern_name and pattern_str and pattern_str.strip():
                regex_pattern = RegexPattern(pattern_name=pattern_name, pattern=pattern_str.strip())
                self.regex_patterns.append(regex_pattern)

    def load_user_list(self, task_id: str) -> None:
        phrases: list[Phrase] = ListFromText(task_id).load()

        for phrase in phrases:
            self.phrases.append(phrase)

    def apply_exclude_user_list(self, task_id: str) -> None:
        """Remove from self.phrases any phrase whose text matches an exclude-list phrase (case-insensitive)."""
        exclude_phrases: list[Phrase] = ListFromTextExclude(task_id).load()
        result_phrases: list[Phrase] = []

        for p in self.phrases:
            is_excluded = False

            for ex in exclude_phrases:
                if p.phrase.lower() == ex.phrase.lower():
                    is_excluded = True
                    break

            if not is_excluded:
                result_phrases.append(p)

        self.phrases = result_phrases

    def load_predefined_lists(self, list_keys: Optional[List[str]]) -> None:
        if list_keys is None:
            return

        """Load ready-made Phrase objects from predefined lists (MySQL) by their keys."""
        list_mapping = {
            PredefinedListKey.FOREIGN_AGENTS_PERSONS: ListInagentsFIZ,
            PredefinedListKey.FOREIGN_AGENTS_COMPANIES: ListInagentsUR,
            PredefinedListKey.PROFANITY: ListProfanity,
            PredefinedListKey.PROHIBITED_SUBSTANCES: ListProhibitedSubstances,
            PredefinedListKey.DANGEROUS: ListDangerousWords,
            PredefinedListKey.EXTREMISTS_TERRORISTS: ListExtremistsTerrorists,
            PredefinedListKey.EXTREMISTS_INTERNATIONAL_FIZ: ListExtremistsInternationalFIZ,
            PredefinedListKey.EXTREMISTS_INTERNATIONAL_UR: ListExtremistsInternationalUR,
            PredefinedListKey.EXTREMISTS_RUSSIAN_FIZ: ListExtremistsRussianFIZ,
            PredefinedListKey.EXTREMISTS_RUSSIAN_UR: ListExtremistsRussianUR,
        }

        for key in list_keys:
            # Convert string key to enum if needed
            key_enum = PredefinedListKey(key) if isinstance(key, str) else key

            if key_enum in list_mapping:
                words_list = list_mapping[key_enum]()
                phrases = words_list.load()

                for phrase in phrases:
                    if phrase and phrase.phrase and phrase.phrase.strip():
                        self.phrases.append(phrase)

                if key_enum == PredefinedListKey.PROFANITY:
                    self.read_regex_patterns(PROFANITY_WORDS_PATTERNS)
