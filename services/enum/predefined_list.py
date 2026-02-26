from enum import Enum

class PredefinedListKey(str, Enum):
    FOREIGN_AGENTS_PERSONS = "foreign_agents_persons"
    FOREIGN_AGENTS_COMPANIES = "foreign_agents_companies"
    PROFANITY = "profanity"
    PROHIBITED_SUBSTANCES = "prohibited_substances"
    DANGEROUS = "dangerous"
    EXTREMISTS_TERRORISTS = "extremists_terrorists"
    EXTREMISTS_INTERNATIONAL_FIZ = "extremists_international_fiz"
    EXTREMISTS_INTERNATIONAL_UR = "extremists_international_ur"
    EXTREMISTS_RUSSIAN_FIZ = "extremists_russian_fiz"
    EXTREMISTS_RUSSIAN_UR = "extremists_russian_ur"


class ESearchSourceAnnotTitle(str, Enum):
    PROFANITY = "Матные слова"
    PROHIBITED_SUBSTANCES = "Запрещенные вещества"
    DANGEROUS = "Опасные слова"
    EXTREMISTS_TERRORISTS = "Экстремисты и террористы"
    INAGENTS = "Иноагенты"
    CUSTOM = "Пользовательский список"