from enum import Enum
from typing import Dict, Tuple


class PredefinedListKey(str, Enum):
    FOREIGN_AGENTS_PERSONS = "foreign_agents_persons"
    FOREIGN_AGENTS_COMPANIES = "foreign_agents_companies"
    PROFANITY = "profanity"
    PROHIBITED_SUBSTANCES = "prohibited_substances"
    SWEAR_WORDS = "swear_words"
    EXTREMISTS_TERRORISTS = "extremists_terrorists"
    EXTREMISTS_INTERNATIONAL_FIZ = "extremists_international_fiz"
    EXTREMISTS_INTERNATIONAL_UR = "extremists_international_ur"
    EXTREMISTS_RUSSIAN_FIZ = "extremists_russian_fiz"
    EXTREMISTS_RUSSIAN_UR = "extremists_russian_ur"


# Static set: 5 thematic lists (backend). Order for reference only.
STATIC_LIST_KEYS: Tuple[PredefinedListKey, ...] = (
    PredefinedListKey.PROFANITY,
    PredefinedListKey.PROHIBITED_SUBSTANCES,
    PredefinedListKey.SWEAR_WORDS,
    PredefinedListKey.FOREIGN_AGENTS_PERSONS,
    PredefinedListKey.FOREIGN_AGENTS_COMPANIES,
    PredefinedListKey.EXTREMISTS_TERRORISTS,
)


class ESearchSource(str, Enum):
    FILE = "file"
    TEXT = "text"
    LIST_INAGENTS = "list_inagents"
    LIST_PROFANITY = "list_profanity"
    LIST_PROHIBITED_SUBSTANCES = "list_prohibited_substances"
    LIST_SWEAR_WORDS = "list_swear_words"
    LIST_EXTREMISTS_TERRORISTS = "list_extremists_terrorists"


class ESearchSourceAnnotTitle(str, Enum):
    FILE = "Пользовательский список"
    TEXT = "Пользовательский список"
    LIST_INAGENTS = "Инагенты"
    LIST_PROFANITY = "Матные слова"
    LIST_PROHIBITED_SUBSTANCES = "Запрещенные вещества"
    LIST_SWEAR_WORDS = "Ругательства"
    LIST_EXTREMISTS_TERRORISTS = "Экстремисты и террористы"


PREDEFINED_LIST_SOURCE: Dict[PredefinedListKey, ESearchSource] = {
    PredefinedListKey.PROFANITY: ESearchSource.LIST_PROFANITY,
    PredefinedListKey.PROHIBITED_SUBSTANCES: ESearchSource.LIST_PROHIBITED_SUBSTANCES,
    PredefinedListKey.SWEAR_WORDS: ESearchSource.LIST_SWEAR_WORDS,
    PredefinedListKey.FOREIGN_AGENTS_PERSONS: ESearchSource.LIST_INAGENTS,
    PredefinedListKey.FOREIGN_AGENTS_COMPANIES: ESearchSource.LIST_INAGENTS,
    PredefinedListKey.EXTREMISTS_TERRORISTS: ESearchSource.LIST_EXTREMISTS_TERRORISTS,
    PredefinedListKey.EXTREMISTS_INTERNATIONAL_FIZ: ESearchSource.LIST_EXTREMISTS_TERRORISTS,
    PredefinedListKey.EXTREMISTS_INTERNATIONAL_UR: ESearchSource.LIST_EXTREMISTS_TERRORISTS,
    PredefinedListKey.EXTREMISTS_RUSSIAN_FIZ: ESearchSource.LIST_EXTREMISTS_TERRORISTS,
    PredefinedListKey.EXTREMISTS_RUSSIAN_UR: ESearchSource.LIST_EXTREMISTS_TERRORISTS,
}