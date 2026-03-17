"""Flask CLI command: normalize search_terms to {type, text}; strip initials and set type 'surname' where applicable."""

from typing import Any

import click

from extensions import db
from models import Inagent


def _is_initial(token: str) -> bool:
    """Token is a single letter + dot (e.g. 'Е.', 'О.')."""
    return len(token) == 2 and token[1] == "." and token[0].isalpha()


def _strip_initials_from_term(term: str) -> str:
    """If term ends with initials (e.g. 'Фельдман Е. О.'), return only the first word."""
    s = (term or "").strip()
    if not s:
        return s
    parts = s.split()
    if len(parts) <= 1:
        return s
    i = 1
    while i < len(parts) and _is_initial(parts[i]):
        i += 1
    if i > 1:
        return parts[0]
    return s


def _raw_text(term: Any) -> str:
    """Extract plain string from term (string or {type, text} object)."""
    if isinstance(term, str):
        return term
    if isinstance(term, dict) and "text" in term:
        return (term.get("text") or "").strip()
    return ""


def _normalize_term(term: Any) -> dict[str, str] | None:
    """Convert term to {type, text}. type is 'surname' if initials were stripped, else 'text'."""
    raw = _raw_text(term)
    if not raw:
        return None
    stripped = _strip_initials_from_term(raw)
    if stripped != raw:
        return {"type": "surname", "text": stripped}
    return {"type": "text", "text": raw}


@click.command("inagents:strip-search-initials")
def strip_inagents_search_initials_cmd() -> None:
    rows = Inagent.query.filter(Inagent.search_terms.isnot(None)).all()
    updated_count = 0

    for inagent in rows:
        terms = inagent.search_terms
        if not isinstance(terms, list):
            continue
        new_terms: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for t in terms:
            item = _normalize_term(t)
            if not item:
                continue
            key = (item["type"], item["text"])
            if key not in seen:
                seen.add(key)
                new_terms.append(item)
        if new_terms != terms:
            inagent.search_terms = new_terms
            updated_count += 1

    db.session.commit()
    click.echo(f"Updated search_terms for {updated_count} inagents (of {len(rows)} with non-empty terms).")
