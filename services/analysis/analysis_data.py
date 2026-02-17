from typing import List, Optional, Dict
from services.document_service import extract_lines_from_docx
from services.fulltext_search.phrase import Phrase
from services.words_list.list_inagents_fiz import ListInagentsFIZ
from services.words_list.list_inagents_ur import ListInagentsUR
from services.words_list.list_profanity import ListProfanity
from services.words_list.list_prohibited_substances import ListProhibitedSubstances
from services.words_list.list_swear_words import ListSwearWords
from services.words_list.list_extremists_terrorists import ListExtremistsTerrorists
from services.enum import PredefinedListKey
from services.enum.predefined_list import SearchSourceType
from services.utils.regex_pattern import RegexPattern
from services.patterns.profanity_words import PROFANITY_WORDS_PATTERNS


class AnalysisData:
    phrases: Dict[str, Phrase]
    regex_patterns: List[RegexPattern]

    def __init__(self, terms: Optional[List[str]] = None) -> None:
        self.phrases = {}
        self.regex_patterns = []

        if terms is not None:
            self.read_from_list(terms)

    def read_from_list(self, terms: List[str]) -> None:
        for term in terms:
            if term and term.strip():
                text = term.strip()

                if text not in self.phrases:
                    self.phrases[text] = Phrase(text, SearchSourceType.TEXT)

    def read_regex_patterns(self, patterns: Dict[str, str]) -> None:
        """Load regex patterns for search.
        
        Args:
            patterns: Dictionary mapping pattern_name to pattern_string
        """
        for pattern_name, pattern_str in patterns.items():
            if pattern_name and pattern_str and pattern_str.strip():
                regex_pattern = RegexPattern(pattern_name=pattern_name, pattern=pattern_str.strip())
                self.regex_patterns.append(regex_pattern)

    def load_predefined_lists(self, list_keys: List[str]) -> None:
        """Load ready-made Phrase objects from predefined lists (MySQL) by their keys."""
        list_mapping = {
            PredefinedListKey.FOREIGN_AGENTS_PERSONS: ListInagentsFIZ,
            PredefinedListKey.FOREIGN_AGENTS_COMPANIES: ListInagentsUR,
            PredefinedListKey.PROFANITY: ListProfanity,
            PredefinedListKey.PROHIBITED_SUBSTANCES: ListProhibitedSubstances,
            PredefinedListKey.SWEAR_WORDS: ListSwearWords,
            PredefinedListKey.EXTREMISTS_TERRORISTS: ListExtremistsTerrorists
        }

        for key in list_keys:
            # Convert string key to enum if needed
            key_enum = PredefinedListKey(key) if isinstance(key, str) else key
            
            if key_enum in list_mapping:
                words_list = list_mapping[key_enum]()
                phrases = words_list.load()

                for phrase in phrases:
                    if phrase and phrase.phrase and phrase.phrase.strip():
                        text = phrase.phrase.strip()

                        if text not in self.phrases:
                            self.phrases[text] = phrase

                if key_enum == PredefinedListKey.PROFANITY:
                    self.read_regex_patterns(PROFANITY_WORDS_PATTERNS)

    def read_from_docx(self, path: str) -> None:
        terms = extract_lines_from_docx(path)
        self.read_from_list(terms)
