from enum import Enum

class PredefinedListKey(str, Enum):
    FOREIGN_AGENTS_PERSONS = "foreign_agents_persons"
    FOREIGN_AGENTS_COMPANIES = "foreign_agents_companies"
    PROFANITY = "profanity"
    PROHIBITED_SUBSTANCES = "prohibited_substances"
    DANGEROUS_WORDS = "dangerous_words"
    EXTREMISTS_TERRORISTS = "extremists_terrorists"
    EXTREMISTS_INTERNATIONAL_FIZ = "extremists_international_fiz"
    EXTREMISTS_INTERNATIONAL_UR = "extremists_international_ur"
    EXTREMISTS_RUSSIAN_FIZ = "extremists_russian_fiz"
    EXTREMISTS_RUSSIAN_UR = "extremists_russian_ur"


class ESearchSource(str, Enum):
    FILE = "file"
    TEXT = "text"
    LIST_INAGENTS = "list_inagents"
    LIST_PROFANITY = "list_profanity"
    LIST_PROHIBITED_SUBSTANCES = "list_prohibited_substances"
    LIST_DANGEROUS_WORDS = "list_dangerous_words"
    LIST_EXTREMISTS_TERRORISTS = "list_extremists_terrorists"


class ESearchSourceAnnotTitle(str, Enum):
    FILE = "Пользовательский список"
    TEXT = "Пользовательский список"
    LIST_INAGENTS = "Инагенты"
    LIST_PROFANITY = "Матные слова"
    LIST_PROHIBITED_SUBSTANCES = "Запрещенные вещества"
    LIST_DANGEROUS_WORDS = "Опасные слова"
    LIST_EXTREMISTS_TERRORISTS = "Экстремисты и террористы"
