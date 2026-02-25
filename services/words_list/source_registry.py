"""Registry for phrase source_list: legacy value <-> list class (for serialization and template)."""

from typing import Dict, Type

from services.words_list.list_dangerous_words import ListDangerousWords
from services.words_list.list_extremists_terrorists import ListExtremistsTerrorists
from services.words_list.list_from_text import ListFromText
from services.words_list.list_inagents_fiz import ListInagentsFIZ
from services.words_list.list_profanity import ListProfanity
from services.words_list.list_prohibited_substances import ListProhibitedSubstances

LEGACY_SOURCE_TO_CLASS: Dict[str, Type] = {
    "file": ListFromText,
    "text": ListFromText,
    "list_inagents": ListInagentsFIZ,
    "list_profanity": ListProfanity,
    "list_prohibited_substances": ListProhibitedSubstances,
    "list_dangerous_words": ListDangerousWords,
    "list_extremists_terrorists": ListExtremistsTerrorists,
}
