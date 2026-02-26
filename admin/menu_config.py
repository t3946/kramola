"""
Parametric admin menu description. All menu structure and ready-lists logic is grouped here.
"""

from typing import Type

from flask import current_app

from services.enum import PredefinedListKey
from services.words_list import WordsList
from services.words_list.list_dangerous_words import ListDangerousWords
from services.words_list.list_extremists_international_fiz import ListExtremistsInternationalFIZ
from services.words_list.list_extremists_international_ur import ListExtremistsInternationalUR
from services.words_list.list_extremists_russian_fiz import ListExtremistsRussianFIZ
from services.words_list.list_extremists_russian_ur import ListExtremistsRussianUR
from services.words_list.list_extremists_terrorists import ListExtremistsTerrorists
from services.words_list.list_inagents_fiz import ListInagentsFIZ
from services.words_list.list_inagents_ur import ListInagentsUR
from services.words_list.list_profanity import ListProfanity
from services.words_list.list_prohibited_substances import ListProhibitedSubstances


# --- Ready lists (dropdown) constants ---

READY_LISTS_CATEGORY: str = "Готовые списки"
READY_LISTS_DROPDOWN_TITLE: str = "Готовые списки"
INAGENTS_ENDPOINT: str = "inagents_list"
EXTREMISTS_TERRORISTS_ENDPOINT: str = "words_list_extremists_terrorists"

# Кастомные короткие названия для пунктов «Террористы» в выпадающем меню (базовый + 4 подтипа)
ADMIN_MENU_TERRORISTS_TITLES: dict[str, str] = {
    PredefinedListKey.EXTREMISTS_TERRORISTS.value: "Террористы",
    PredefinedListKey.EXTREMISTS_INTERNATIONAL_FIZ.value: "Террористы (ООН): ФЛ",
    PredefinedListKey.EXTREMISTS_INTERNATIONAL_UR.value: "Террористы (ООН): ЮЛ",
    PredefinedListKey.EXTREMISTS_RUSSIAN_FIZ.value: "Террористы (РФ): ФЛ",
    PredefinedListKey.EXTREMISTS_RUSSIAN_UR.value: "Террористы (РФ): ЮЛ",
}


# --- Menu items: PredefinedListKey -> (endpoint, list class for count) ---

def _words_list_endpoint(key: PredefinedListKey) -> str:
    return f"words_list_{key.value}"


ADMIN_MENU_ITEMS: list[tuple[PredefinedListKey, str, Type[WordsList]]] = [
    (PredefinedListKey.PROFANITY, _words_list_endpoint(PredefinedListKey.PROFANITY), ListProfanity),
    (PredefinedListKey.PROHIBITED_SUBSTANCES, _words_list_endpoint(PredefinedListKey.PROHIBITED_SUBSTANCES), ListProhibitedSubstances),
    (PredefinedListKey.DANGEROUS, _words_list_endpoint(PredefinedListKey.DANGEROUS), ListDangerousWords),
    (PredefinedListKey.FOREIGN_AGENTS_PERSONS, INAGENTS_ENDPOINT, ListInagentsFIZ),
    (PredefinedListKey.FOREIGN_AGENTS_COMPANIES, INAGENTS_ENDPOINT, ListInagentsUR),
    (PredefinedListKey.EXTREMISTS_TERRORISTS, EXTREMISTS_TERRORISTS_ENDPOINT, ListExtremistsTerrorists),
    (PredefinedListKey.EXTREMISTS_INTERNATIONAL_FIZ, EXTREMISTS_TERRORISTS_ENDPOINT, ListExtremistsInternationalFIZ),
    (PredefinedListKey.EXTREMISTS_INTERNATIONAL_UR, EXTREMISTS_TERRORISTS_ENDPOINT, ListExtremistsInternationalUR),
    (PredefinedListKey.EXTREMISTS_RUSSIAN_FIZ, EXTREMISTS_TERRORISTS_ENDPOINT, ListExtremistsRussianFIZ),
    (PredefinedListKey.EXTREMISTS_RUSSIAN_UR, EXTREMISTS_TERRORISTS_ENDPOINT, ListExtremistsRussianUR),
]


# --- Full menu spec for view registration ---

MENU_SPEC: list[dict] = [
    {
        "category": "Пользователи",
        "views": [
            {"view_class": "UserView", "name": "Пользователи", "model": "User"},
            {"view_class": "RoleView", "name": "Роли", "model": "Role"},
        ],
    },
    {
        "category": READY_LISTS_CATEGORY,
        "views": [
            {
                "view_class": "InagentsListView",
                "name": "Инагенты",
                "url": "words-list/inagents",
                "endpoint": INAGENTS_ENDPOINT,
            },
            {
                "view_class": "WordsListView",
                "dynamic": True,
                "exclude_slugs": [
                    "inagents",
                    "extremists-international-fiz",
                    "extremists-international-ur",
                    "extremists-russian-fiz",
                    "extremists-russian-ur",
                ],
            },
        ],
    },
    {
        "category": "Настройки",
        "views": [
            {
                "view_class": "SearchSettingsView",
                "name": "Поиск",
                "url": "settings/search",
                "endpoint": "search_settings",
            },
        ],
    },
    {
        "category": None,
        "views": [
            {
                "view_class": "AutoloadView",
                "name": "Автозагрузка",
                "url": "autoload",
                "endpoint": "autoload",
            },
        ],
    },
]


def get_ready_lists_menu_items() -> list[dict]:
    """Returns list of {title, endpoint, count} for the ready-lists dropdown."""
    predefined: dict[str, str] = current_app.config.get("PREDEFINED_LISTS", {})
    result: list[dict] = []
    for key, endpoint, list_cls in ADMIN_MENU_ITEMS:
        key_val: str = key.value
        if key_val not in predefined and key_val not in ADMIN_MENU_TERRORISTS_TITLES:
            continue
        title: str = ADMIN_MENU_TERRORISTS_TITLES.get(key_val) or predefined.get(key_val, "")
        if not title:
            title = key_val
        result.append({
            "endpoint": endpoint,
            "title": title,
            "count": list_cls().count_phrases(),
        })
    return result
