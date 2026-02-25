from enum import Enum


class WordsListKey(str, Enum):
    PROFANITY = "profanity"
    PROHIBITED_SUBSTANCES = "prohibited_substances"
    DANGEROUS = "dangerous"
    EXTREMISTS_TERRORISTS = "extremists_terrorists"
    INAGENTS = "inagents"
    CUSTOM = "custom"
    
