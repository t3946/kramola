from enum import Enum

class PredefinedListKey(str, Enum):
    FOREIGN_AGENTS_PERSONS = "foreign_agents_persons"
    FOREIGN_AGENTS_COMPANIES = "foreign_agents_companies"
    PROFANITY = "profanity"
    PROHIBITED_SUBSTANCES = "prohibited_substances"
    SWEAR_WORDS = "swear_words"
    EXTREMISTS_TERRORISTS = "extremists_terrorists"
