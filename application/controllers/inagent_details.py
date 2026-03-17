from flask import render_template

from models import Inagent
from models.inagents import AGENT_TYPE_MAP


class InagentDetailsController:
    _EMPTY_FORM_DATA: dict = {
        "full_name": "",
        "number": "",
        "agent_type": "",
        "status_label": "—",
        "date_included": "",
        "date_excluded": "",
        "domain": "",
        "search_terms": [],
    }

    @staticmethod
    def _status_label(inagent: Inagent) -> str:
        i_d = inagent.include_minjust_date
        e_d = inagent.exclude_minjust_date
        if i_d and not e_d or i_d and e_d and i_d > e_d:
            return "Числится"
        if i_d and e_d and i_d <= e_d:
            return "Снят"
        return "—"

    @staticmethod
    def _search_terms_to_strings(search_terms: list | None) -> list[str]:
        raw = list(search_terms)[:6] if isinstance(search_terms, list) else []
        return [t.get("text", t) if isinstance(t, dict) else t for t in raw]

    @classmethod
    def _to_form_data(cls, inagent: Inagent) -> dict:
        def _agent_type_str(agent_type_attr) -> str:
            if agent_type_attr is None:
                return ""
            return getattr(agent_type_attr, "value", None) or str(agent_type_attr) or ""

        def _domain_to_text(domain_name: list | None) -> str:
            if not domain_name:
                return ""
            return "\n".join(domain_name) if isinstance(domain_name, list) else str(domain_name)

        return {
            "agent_type": _agent_type_str(inagent.agent_type),
            "number": str(inagent.registry_number) if inagent.registry_number is not None else "",
            "full_name": inagent.full_name or "",
            "status_label": cls._status_label(inagent),
            "date_included": inagent.include_minjust_date.strftime("%Y-%m-%d") if inagent.include_minjust_date else "",
            "date_excluded": inagent.exclude_minjust_date.strftime("%Y-%m-%d") if inagent.exclude_minjust_date else "",
            "domain": _domain_to_text(inagent.domain_name),
            "search_terms": cls._search_terms_to_strings(inagent.search_terms),
        }

    @classmethod
    def render_fragment(cls, phrase: str) -> str:
        if not phrase.strip():
            return render_template(
                "tool_highlight/inagent_details_modal/fragment.html",
                form_data=cls._EMPTY_FORM_DATA,
                agent_type_map=AGENT_TYPE_MAP,
            )

        inagent = Inagent.query.filter(Inagent.full_name == phrase).first()

        if not inagent:
            return render_template(
                "tool_highlight/inagent_details_modal/fragment.html",
                form_data=cls._EMPTY_FORM_DATA,
                agent_type_map=AGENT_TYPE_MAP,
            )

        form_data = cls._to_form_data(inagent)

        return render_template(
            "tool_highlight/inagent_details_modal/fragment.html",
            form_data=form_data,
            agent_type_map=AGENT_TYPE_MAP,
        )
