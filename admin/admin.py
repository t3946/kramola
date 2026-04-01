from collections.abc import Callable
from datetime import datetime
from sqlalchemy import Date, func, inspect, or_

from extensions import db
from flask import Flask, current_app, flash, jsonify, redirect, render_template, request, Response, url_for
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_login import current_user
from wtforms import PasswordField

from admin.menu_config import MENU_SPEC
from commands.parse_extremists import run_extremists_parse
from commands.parse_inagents_cmd import get_parse_inagents_module
from commands.update_inagents_cmd import run_update_inagents
from models import Inagent, User, Role
from services.parser_feds_fm import ParserFedsFM
from services.task.task import Task, _datetime_display_moscow
from services.task.tasks import Tasks
from models.extremists_terrorists import (
    EXTREMIST_AREA_LABELS,
    EXTREMIST_TYPE_LABELS,
    ExtremistArea,
    ExtremistType,
    ExtremistTerrorist,
)
from models.inagents import AGENT_TYPE_MAP, AGENT_TYPE_SHORT_LABELS
from models.phrase_list.list_record import ListRecord
from models.phrase_list.phrase_record import PhraseRecord

from admin.words_list_controller import (
    _lines_from_text,
    export_phrases_to_text,
    get_phrases_count,
    get_phrases_paginated,
    get_phrases_sorted,
    import_phrases_from_file,
    import_phrases_from_lines,
    minusate_phrases_from_file,
    minusate_phrases_from_lines,
    remove_phrase_from_list,
    search_phrases,
    update_phrase_in_list,
)

SLUG_EXTREMISTS_TERRORISTS: str = "extremists-terrorists"
PARSING_STATUS_KEY_INAGENTS: str = "parser:status:InagentsXlsxParser"
PARSING_STATUS_KEY_EXTREMISTS: str = "parser:status:ParserFedsFM"
PARSING_STATUS_TTL_SECONDS: int = 6 * 60 * 60
PARSING_SOCKET_EVENT: str = "parsing_status_changed"


VALID_EXTREMIST_TYPES: tuple[str, ...] = (ExtremistType.FIZ.value, ExtremistType.UR.value)


def _parsing_is_running(app: Flask, status_key: str) -> bool:
    redis_client = getattr(app, "redis_client_tasks", None)

    if redis_client is None:
        return False

    return bool(redis_client.get(status_key))


def _parsing_last_datetime(status_key: str) -> datetime | None:
    if status_key == PARSING_STATUS_KEY_INAGENTS:
        inagents_parser_cls = get_parse_inagents_module().InagentsXlsxParser
        return inagents_parser_cls.get_last_parse_datetime()

    if status_key == PARSING_STATUS_KEY_EXTREMISTS:
        return ParserFedsFM.get_last_parse_datetime()

    return None


def _parsing_status_label(is_running: bool, last_dt: datetime | None) -> str:
    if is_running:
        return "В работе"

    if last_dt is None:
        return "Не проводилось"

    return "Выполенено"


def _parsing_realtime_payload(app: Flask, status_key: str, state: str) -> dict[str, str | bool]:
    last_dt: datetime | None = _parsing_last_datetime(status_key)
    is_running: bool = _parsing_is_running(app, status_key)
    status_label: str = _parsing_status_label(is_running, last_dt)

    return {
        "key": status_key,
        "state": state,
        "status": status_label,
        "last_parse": _datetime_display_moscow(last_dt),
        "can_run": not is_running,
    }


def _emit_parsing_status(app: Flask, status_key: str, state: str) -> None:
    socketio = app.extensions.get("socketio")

    if socketio is None:
        return

    socketio.emit(PARSING_SOCKET_EVENT, _parsing_realtime_payload(app, status_key, state))


def _search_terms_for_form(search_terms: list | None) -> list[dict]:
    """Return list of {text, type} for form display (and template)."""
    raw = list(search_terms) if isinstance(search_terms, list) else []
    return [
        {"text": t.get("text", t) if isinstance(t, dict) else t, "type": t.get("type", "text") if isinstance(t, dict) else "text"}
        for t in raw
    ]


def _search_terms_from_form(texts: list, types: list) -> list[dict]:
    """Build list[dict] from form getlist('search_terms_text') and getlist('search_terms_type')."""
    result: list[dict] = []
    for t, ty in zip(texts, types):
        text = t.strip() if isinstance(t, str) else ""
        if not text:
            continue
        type_val = (ty.strip() if isinstance(ty, str) else "text") or "text"
        if type_val not in ("text", "surname", "full_name"):
            type_val = "text"
        result.append({"text": text, "type": type_val})
    return result


def _extremist_to_form_data(et: ExtremistTerrorist) -> dict:
    raw = list(et.search_terms) if isinstance(et.search_terms, list) else []
    terms = _search_terms_for_form(et.search_terms)
    birth_date_str = et.birth_date.strftime("%Y-%m-%d") if et.birth_date else ""
    return {
        "raw_source": et.raw_source or "",
        "type": et.type or "",
        "type_label": EXTREMIST_TYPE_LABELS.get(et.type, et.type or ""),
        "area": et.area or "",
        "area_label": EXTREMIST_AREA_LABELS.get(et.area, et.area or ""),
        "is_active_label": "Да" if et.is_active else "Нет",
        "birth_date": birth_date_str,
        "birth_place": et.birth_place or "",
        "company_region": et.company_region or "",
        "search_terms": terms,
    }


def _form_apply_extremist(form, et: ExtremistTerrorist) -> None:
    type_val = form.get("type", "").strip()
    if type_val in VALID_EXTREMIST_TYPES:
        et.type = type_val
    if et.type == ExtremistType.FIZ.value and et.area == ExtremistArea.RUSSIAN.value:
        if "birth_date" in form:
            raw_birth = form.get("birth_date", "").strip()
            if raw_birth:
                try:
                    et.birth_date = datetime.strptime(raw_birth, "%Y-%m-%d").date()
                except ValueError:
                    et.birth_date = None
            else:
                et.birth_date = None
        if "birth_place" in form:
            et.birth_place = form.get("birth_place", "").strip() or None
    if et.type == ExtremistType.UR.value and et.area == ExtremistArea.RUSSIAN.value:
        if "company_region" in form:
            et.company_region = form.get("company_region", "").strip() or None
    texts = form.getlist("search_terms_text")
    types = form.getlist("search_terms_type")
    et.search_terms = _search_terms_from_form(texts, types)


def _extremists_terrorists_count() -> int:
    return int(ExtremistTerrorist.query.count())


def _extremists_terrorists_paginated(
    limit: int,
    offset: int,
    query: str | None,
    type_filter: str | None = None,
    area_filter: str | None = None,
    phrases_filter: str | None = None,
    active_filter: str | None = None,
) -> tuple[list[ExtremistTerrorist], int]:
    base = ExtremistTerrorist.query
    if query:
        base = base.filter(ExtremistTerrorist.raw_source.ilike(f"%{query}%"))
    if type_filter and type_filter in VALID_EXTREMIST_TYPES:
        base = base.filter(ExtremistTerrorist.type == type_filter)
    if area_filter:
        base = base.filter(ExtremistTerrorist.area == area_filter)
    if phrases_filter == "yes":
        base = base.filter(func.json_length(ExtremistTerrorist.search_terms) > 0)
    elif phrases_filter == "no":
        base = base.filter(
            or_(
                ExtremistTerrorist.search_terms.is_(None),
                func.json_length(ExtremistTerrorist.search_terms) == 0,
            )
        )
    if active_filter == "yes":
        base = base.filter(ExtremistTerrorist.is_active.is_(True))
    elif active_filter == "no":
        base = base.filter(ExtremistTerrorist.is_active.is_(False))
    total: int = base.count()
    rows = base.order_by(ExtremistTerrorist.raw_source.asc()).limit(limit).offset(offset).all()
    return rows, total


class WordsListView(BaseView):
    def __init__(self, list_slug: str, **kwargs):
        self.list_slug = list_slug
        super().__init__(**kwargs)

    def is_visible(self) -> bool:
        return False

    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.has_role("admin")

    def inaccessible_callback(self, name: str, **kwargs) -> redirect:
        return redirect(url_for("admin_auth.login", next=request.url))

    @expose("/")
    def index(self, **kwargs):
        list_record = ListRecord.query.filter_by(slug=self.list_slug).first()
        if self.list_slug == SLUG_EXTREMISTS_TERRORISTS:
            total_count = _extremists_terrorists_count()
        else:
            total_count = get_phrases_count(list_record) if list_record else 0
        list_title = list_record.title if list_record else (self.list_slug if self.list_slug != SLUG_EXTREMISTS_TERRORISTS else "Экстремисты и террористы")
        import_url = url_for(".import_phrases") if list_record and self.list_slug != SLUG_EXTREMISTS_TERRORISTS else None
        export_url = url_for(".export_phrases") if list_record and self.list_slug != SLUG_EXTREMISTS_TERRORISTS else None
        minusate_url = url_for(".minusate_phrases") if list_record and self.list_slug != SLUG_EXTREMISTS_TERRORISTS else None
        endpoint = self.endpoint
        data_url = url_for(f"{endpoint}.data_route") if (list_record or self.list_slug == SLUG_EXTREMISTS_TERRORISTS) else None
        template = "admin/words_list_extremists_terrorists.html" if self.list_slug == SLUG_EXTREMISTS_TERRORISTS else "admin/words_list.html"
        kwargs: dict = {
            "list_title": list_title,
            "list_slug": self.list_slug,
            "total_count": total_count,
            "import_url": import_url,
            "export_url": export_url,
            "minusate_url": minusate_url,
            "data_url": data_url,
        }
        if self.list_slug == SLUG_EXTREMISTS_TERRORISTS:
            kwargs["type_choices"] = list(EXTREMIST_TYPE_LABELS.items())
            kwargs["area_choices"] = list(EXTREMIST_AREA_LABELS.items())
        return self.render(template, **kwargs)

    @expose("/import", methods=["POST"])
    def import_phrases(self):
        list_record = ListRecord.query.filter_by(slug=self.list_slug).first()

        if not list_record:
            return redirect(url_for(".index"))

        phrases_text = request.form.get("phrases_text", "").strip()

        if phrases_text:
            lines = _lines_from_text(phrases_text)
            added = import_phrases_from_lines(list_record, lines)
        else:
            file = request.files.get("file")

            if not file or file.filename == "":
                flash("Укажите файл или введите текст.")
                return redirect(url_for(".index"))

            if not file.filename.lower().endswith(".txt"):
                return redirect(url_for(".index"))

            added = import_phrases_from_file(list_record, file)

        flash(f"Импорт: добавлено фраз в список: {added}.")

        return redirect(url_for(".index"))

    @expose("/minusate", methods=["GET", "POST"])
    def minusate_phrases(self):
        if request.method != "POST":
            return redirect(url_for(".index"))

        list_record = ListRecord.query.filter_by(slug=self.list_slug).first()

        if not list_record:
            return redirect(url_for(".index"))

        phrases_text = request.form.get("phrases_text", "").strip()

        if phrases_text:
            lines = _lines_from_text(phrases_text)
            removed = minusate_phrases_from_lines(list_record, lines)
        else:
            file = request.files.get("file")
            if not file or file.filename == "":
                flash("Укажите файл или введите текст.")
                return redirect(url_for(".index"))
            if not file.filename.lower().endswith(".txt"):
                return redirect(url_for(".index"))
            removed = minusate_phrases_from_file(list_record, file)
        flash(f"Минусация: удалено фраз из списка: {removed}.")
        return redirect(url_for(".index"))

    @expose("/phrase/<int:phrase_id>/edit", methods=["GET", "POST"])
    def edit_phrase(self, phrase_id: int):
        if request.method != "POST":
            return redirect(url_for(".index"))
        if self.list_slug == SLUG_EXTREMISTS_TERRORISTS:
            et = ExtremistTerrorist.query.get(phrase_id)
            if not et:
                flash("Запись не найдена.")
                return redirect(url_for(".index"))
            new_text = request.form.get("phrase", "").strip()
            if not new_text:
                flash("ФИО не может быть пустым.")
                return redirect(url_for(".index"))
            et.raw_source = new_text
            db.session.commit()
            flash("Запись сохранена.")
            return redirect(url_for(".index"))
        list_record = ListRecord.query.filter_by(slug=self.list_slug).first()
        if not list_record:
            return redirect(url_for(".index"))
        new_text = request.form.get("phrase", "").strip()
        err = update_phrase_in_list(list_record, phrase_id, new_text)
        if err:
            flash(err)
        else:
            flash("Фраза сохранена.")
        return redirect(url_for(".index"))

    @expose("/phrase/<int:phrase_id>/delete", methods=["GET", "POST"])
    def delete_phrase(self, phrase_id: int):
        if request.method != "POST":
            return redirect(url_for(".index"))
        if self.list_slug == SLUG_EXTREMISTS_TERRORISTS:
            et = ExtremistTerrorist.query.get(phrase_id)
            if not et:
                flash("Запись не найдена.")
                return redirect(url_for(".index"))
            db.session.delete(et)
            db.session.commit()
            flash("Запись удалена из списка.")
            return redirect(url_for(".index"))
        list_record = ListRecord.query.filter_by(slug=self.list_slug).first()
        if not list_record:
            return redirect(url_for(".index"))
        if remove_phrase_from_list(list_record, phrase_id):
            flash("Фраза удалена из списка.")
        else:
            flash("Фраза не найдена в списке.")
        return redirect(url_for(".index"))

    @expose("/<int:id>/form")
    def extremist_edit_form(self, id: int):
        if self.list_slug != SLUG_EXTREMISTS_TERRORISTS:
            return redirect(url_for(".index"))
        et = ExtremistTerrorist.query.get_or_404(id)
        form_data = _extremist_to_form_data(et)
        edit_save_url = url_for(f"{self.endpoint}.extremist_edit_save", id=id)
        return render_template(
            "admin/extremist_edit_fragment.html",
            form_data=form_data,
            edit_save_url=edit_save_url,
            type_choices=list(EXTREMIST_TYPE_LABELS.items()),
        )

    @expose("/<int:id>/edit", methods=["POST"])
    def extremist_edit_save(self, id: int):
        if self.list_slug != SLUG_EXTREMISTS_TERRORISTS:
            return redirect(url_for(".index"))
        et = ExtremistTerrorist.query.get_or_404(id)
        _form_apply_extremist(request.form, et)
        db.session.commit()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(success=True)
        flash("Запись сохранена.")
        return redirect(url_for(".index"))

    @expose("/data")
    def data_route(self):
        list_record = ListRecord.query.filter_by(slug=self.list_slug).first()
        if not list_record and self.list_slug != SLUG_EXTREMISTS_TERRORISTS:
            return jsonify(data=[], total=0)
        limit = request.args.get("limit", 100, type=int)
        offset = request.args.get("offset", 0, type=int)
        query = request.args.get("q", "").strip() or None
        limit = min(max(1, limit), 500)
        offset = max(0, offset)
        endpoint = self.endpoint
        if self.list_slug == SLUG_EXTREMISTS_TERRORISTS:
            type_filter = request.args.get("type", "").strip() or None
            if type_filter and type_filter not in VALID_EXTREMIST_TYPES:
                type_filter = None
            area_filter = request.args.get("area", "").strip() or None

            phrases_filter = request.args.get("phrases", "").strip() or None
            if phrases_filter and phrases_filter not in ("yes", "no"):
                phrases_filter = None
            active_filter = request.args.get("active", "").strip() or None
            if active_filter and active_filter not in ("yes", "no"):
                active_filter = None
            rows, total = _extremists_terrorists_paginated(
                limit, offset, query,
                type_filter=type_filter,
                area_filter=area_filter,
                phrases_filter=phrases_filter,
                active_filter=active_filter,
            )

            def row_et(et: ExtremistTerrorist) -> dict:
                terms = et.search_terms or []
                st_count = len(terms) if isinstance(terms, list) else 0
                terms_with_type: list[dict] = [
                    {"text": t.get("text", t) if isinstance(t, dict) else t, "type": t.get("type", "text") if isinstance(t, dict) else "text"}
                    for t in terms
                ]
                birth_date_str = et.birth_date.strftime("%d.%m.%Y") if et.birth_date else ""
                display_name: str = (et.raw_source or "") or ""
                return {
                    "id": et.id,
                    "full_name": display_name,
                    "birth_date": birth_date_str,
                    "type": et.type or "",
                    "type_label": EXTREMIST_TYPE_LABELS.get(et.type, et.type or ""),
                    "area": et.area or "",
                    "area_label": EXTREMIST_AREA_LABELS.get(et.area, et.area or ""),
                    "search_terms": terms_with_type,
                    "search_terms_count": st_count,
                    "is_active": bool(et.is_active),
                    "edit_form_url": url_for(f"{endpoint}.extremist_edit_form", id=et.id),
                    "edit_save_url": url_for(f"{endpoint}.extremist_edit_save", id=et.id),
                }

            return jsonify(data=[row_et(w) for w in rows], total=total)
        words_list, total = get_phrases_paginated(list_record, limit=limit, offset=offset, query=query)
        created_at_str = lambda w: w.created_at.strftime("%d.%m.%Y") if w.created_at else ""

        def row(w: PhraseRecord) -> dict:
            return {
                "phrase": w.phrase,
                "created_at": created_at_str(w),
                "edit_url": url_for(f"{endpoint}.edit_phrase", phrase_id=w.id),
                "delete_url": url_for(f"{endpoint}.delete_phrase", phrase_id=w.id),
            }

        payload = {"data": [row(w) for w in words_list], "total": total}
        return jsonify(payload)

    @expose("/export")
    def export_phrases(self) -> Response:
        list_record = ListRecord.query.filter_by(slug=self.list_slug).first()
        if not list_record:
            return redirect(url_for(".index"))
        content = export_phrases_to_text(list_record)
        filename = f"{list_record.slug}.txt"
        return Response(
            content,
            mimetype="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )


VALID_AGENT_TYPES: tuple[str, ...] = tuple(AGENT_TYPE_SHORT_LABELS.keys())


def _form_apply_search_terms_only(form, inagent: Inagent) -> None:
    texts = form.getlist("search_terms_text")
    types = form.getlist("search_terms_type")
    inagent.search_terms = _search_terms_from_form(texts, types)


class InagentsListView(BaseView):
    def is_visible(self) -> bool:
        return False

    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.has_role("admin")

    def inaccessible_callback(self, name: str, **kwargs) -> redirect:
        return redirect(url_for("admin_auth.login", next=request.url))

    @expose("/")
    def index(self, **kwargs):
        total_count: int = db.session.query(Inagent).count()
        agent_type_choices: list[tuple[str, str]] = list(AGENT_TYPE_SHORT_LABELS.items())
        return self.render(
            "admin/inagents_list.html",
            total_count=total_count,
            agent_type_choices=agent_type_choices,
        )

    @expose("/data")
    def data_route(self):
        q = request.args.get("q", "").strip() or None
        agent_type = request.args.get("agent_type", "").strip() or None
        if agent_type and agent_type not in VALID_AGENT_TYPES:
            agent_type = None
        status_filter = request.args.get("status", "").strip() or None
        if status_filter and status_filter not in ("listed", "removed"):
            status_filter = None
        phrases_filter = request.args.get("phrases", "").strip() or None
        if phrases_filter and phrases_filter not in ("yes", "no"):
            phrases_filter = None
        limit = request.args.get("limit", 100, type=int)
        offset = request.args.get("offset", 0, type=int)
        limit = min(max(1, limit), 500)
        offset = max(0, offset)

        query = Inagent.query
        if q:
            q_filter = Inagent.full_name.ilike(f"%{q}%")
            if q.isdigit():
                q_filter = or_(q_filter, Inagent.registry_number == int(q))
            query = query.filter(q_filter)
        if agent_type:
            query = query.filter(Inagent.agent_type == agent_type)
        if status_filter == "listed":
            query = query.filter(
                Inagent.include_minjust_date.isnot(None),
                (Inagent.exclude_minjust_date.is_(None)) | (Inagent.include_minjust_date > Inagent.exclude_minjust_date),
            )
        elif status_filter == "removed":
            query = query.filter(
                Inagent.include_minjust_date.isnot(None),
                Inagent.exclude_minjust_date.isnot(None),
                Inagent.include_minjust_date <= Inagent.exclude_minjust_date,
            )
        if phrases_filter == "yes":
            query = query.filter(
                func.json_length(Inagent.search_terms) > 0,
            )
        elif phrases_filter == "no":
            query = query.filter(
                or_(
                    func.json_length(Inagent.search_terms) == 0,
                )
            )
        total = query.count()
        rows = query.order_by(Inagent.registry_number, Inagent.id).offset(offset).limit(limit).all()

        base_path = request.path.rstrip("/").rsplit("/data", 1)[0]
        def _agent_type_val(agent_type_attr) -> str:
            if agent_type_attr is None:
                return ""
            return getattr(agent_type_attr, "value", None) or str(agent_type_attr) or ""

        def row(r: Inagent) -> dict:
            at = _agent_type_val(r.agent_type)
            terms = r.search_terms or []
            search_terms_count: int = len(terms) if isinstance(terms, list) else 0
            terms_with_type: list[dict] = [
                {"text": t.get("text", t) if isinstance(t, dict) else t, "type": t.get("type", "text") if isinstance(t, dict) else "text"}
                for t in terms
            ]
            return {
                "id": r.id,
                "registry_number": r.registry_number,
                "full_name": r.full_name or "",
                "search_terms": terms_with_type,
                "status_label": _inagent_status_label(r),
                "agent_type": at,
                "agent_type_label": AGENT_TYPE_SHORT_LABELS.get(at, at),
                "search_terms_count": search_terms_count,
                "edit_form_url": f"{base_path}/{r.id}/form",
                "edit_save_url": f"{base_path}/{r.id}/edit",
            }

        return jsonify(data=[row(r) for r in rows], total=total)

    @expose("/<int:id>/form")
    def edit_form(self, id: int):
        inagent = Inagent.query.get_or_404(id)
        form_data = _inagent_to_form_data(inagent)
        base_path = request.path.rstrip("/").rsplit("/form", 1)[0]
        edit_save_url = f"{base_path}/edit"
        return render_template(
            "admin/inagent_edit_fragment.html",
            form_data=form_data,
            inagent_id=id,
            edit_save_url=edit_save_url,
            agent_type_map=AGENT_TYPE_MAP
        )

    @expose("/<int:id>/edit", methods=["POST"])
    def edit_save(self, id: int):
        inagent = Inagent.query.get_or_404(id)
        _form_apply_search_terms_only(request.form, inagent)
        db.session.commit()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(success=True)
        flash("Иноагент сохранён.")
        return redirect(url_for(".index"))


def _agent_type_to_str(agent_type_attr) -> str:
    if agent_type_attr is None:
        return ""
    return getattr(agent_type_attr, "value", None) or str(agent_type_attr) or ""


def _inagent_status_label(inagent: Inagent) -> str:
    i_d: Date | None = inagent.include_minjust_date
    e_d: Date | None = inagent.exclude_minjust_date

    if i_d and not e_d or i_d and e_d and i_d > e_d:
        return "Числится"

    if i_d and e_d and i_d <= e_d:
        return "Снят"

    return "—"

def _inagent_to_form_data(inagent: Inagent) -> dict:
    return {
        "agent_type": _agent_type_to_str(inagent.agent_type),
        "number": str(inagent.registry_number) if inagent.registry_number is not None else "",
        "full_name": inagent.full_name or "",
        "status_label": _inagent_status_label(inagent),
        "date_included": inagent.include_minjust_date.strftime("%Y-%m-%d") if inagent.include_minjust_date else "",
        "date_excluded": inagent.exclude_minjust_date.strftime("%Y-%m-%d") if inagent.exclude_minjust_date else "",
        "domain": _domain_to_text(inagent.domain_name),
        "search_terms": _search_terms_for_form(inagent.search_terms),
        "activity": "",
    }


def _domain_to_text(domain_name: list | None) -> str:
    if not domain_name:
        return ""
    return "\n".join(domain_name) if isinstance(domain_name, list) else str(domain_name)


def _search_terms_to_list(search_terms: list | None) -> list[str]:
    raw = list(search_terms)[:6] if isinstance(search_terms, list) else []
    terms = [t.get("text", t) if isinstance(t, dict) else t for t in raw]
    return terms + [""] * (6 - len(terms))


def form_to_inagent(form, inagent: Inagent) -> None:
    from extensions import db

    val = form.get("agent_type")
    if val in VALID_AGENT_TYPES:
        inagent.agent_type = val
    num = form.get("number", "").strip()
    inagent.registry_number = int(num) if num.isdigit() else None
    inagent.full_name = form.get("full_name", "").strip() or None
    inagent.include_minjust_date = _parse_date(form.get("date_included"))
    inagent.exclude_minjust_date = _parse_date(form.get("date_excluded"))
    domain_raw = form.get("domain", "").strip()
    inagent.domain_name = [s.strip() for s in domain_raw.split() if s.strip()] if domain_raw else None

    texts = form.getlist("search_terms_text")
    types = form.getlist("search_terms_type")
    inagent.search_terms = _search_terms_from_form(texts, types)


def _parse_date(s: str | None):
    if not s or not s.strip():
        return None
    from datetime import datetime
    try:
        return datetime.strptime(s.strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


SEARCH_LISTS: list[tuple[str, str, str]] = [
    ("inagents", "inagents", "Иностранные агенты"),
    ("extremists_terrorists", SLUG_EXTREMISTS_TERRORISTS, "Экстремисты и террористы"),
    ("profanity", "profanity", "Матные слова"),
    ("prohibited_substances", "prohibited_substances", "Запрещенные вещества"),
    ("dangerous", "dangerous", "Опасные слова"),
]


def _hex_color(s: str | None) -> str | None:
    if not s or not s.strip():
        return None
    s = s.strip().lstrip("#")
    if len(s) == 6 and all(c in "0123456789abcdefABCDEF" for c in s):
        return f"#{s.lower()}"
    return None


class SearchSettingsView(BaseView):
    """Settings page: search lists with color picker."""

    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.has_role("admin")

    def inaccessible_callback(self, name: str, **kwargs) -> redirect:
        return redirect(url_for("admin_auth.login", next=request.url))

    def _list_items(self) -> list[dict]:
        slugs = [slug for _, slug, _ in SEARCH_LISTS]
        records = {r.slug: r for r in ListRecord.query.filter(ListRecord.slug.in_(slugs)).all()}
        return [
            {
                "name": name,
                "slug": slug,
                "title": title,
                "color": records[slug].color if slug in records else None,
            }
            for name, slug, title in SEARCH_LISTS
        ]

    @expose("/", methods=["GET", "POST"])
    def index(self, **kwargs):
        if request.method == "POST":
            for _name, slug, _title in SEARCH_LISTS:
                key = f"color_{slug}"
                color = _hex_color(request.form.get(key))
                record = ListRecord.query.filter_by(slug=slug).first()
                if record:
                    record.color = color
                else:
                    record = ListRecord(name=_name, slug=slug, title=_title, color=color)
                    db.session.add(record)
            db.session.commit()
            flash("Цвета сохранены.")
            return redirect(url_for(".index"))
        items = self._list_items()
        return self.render("admin/search_settings.html", items=items)


class AutoloadView(BaseView):
    """Admin page for autoload lists logs."""

    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.has_role("admin")

    def inaccessible_callback(self, name: str, **kwargs) -> redirect:
        return redirect(url_for("admin_auth.login", next=request.url))

    @expose("/")
    def index(self, **kwargs):
        return self.render("admin/autoload.html")


class MonitoringTasksView(BaseView):
    """Admin page: background tasks monitoring."""

    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.has_role("admin")

    def inaccessible_callback(self, name: str, **kwargs) -> redirect:
        return redirect(url_for("admin_auth.login", next=request.url))

    @expose("/")
    def index(self, **kwargs):
        admin = self.admin
        app = admin.app if admin is not None else None
        redis_client = getattr(app, "redis_client_tasks", None) if app is not None else None
        redis_unavailable: bool = redis_client is None
        task_ttl_seconds: int = 7 * 24 * 60 * 60
        tasks: list[Task] = (
            []
            if redis_unavailable
            else Tasks.get_all(redis_client, task_ttl_seconds)
        )

        return self.render(
            "admin/monitoring_tasks.html",
            tasks=tasks,
            redis_unavailable=redis_unavailable,
        )


def _run_inagents_update_job(app: Flask) -> None:
    with app.app_context():
        try:
            run_update_inagents()
        finally:
            redis_client = getattr(app, "redis_client_tasks", None)
            if redis_client is not None:
                redis_client.delete(PARSING_STATUS_KEY_INAGENTS)
            _emit_parsing_status(app, PARSING_STATUS_KEY_INAGENTS, "done")


def _run_extremists_parse_job(app: Flask) -> None:
    with app.app_context():
        try:
            run_extremists_parse()
        finally:
            redis_client = getattr(app, "redis_client_tasks", None)
            if redis_client is not None:
                redis_client.delete(PARSING_STATUS_KEY_EXTREMISTS)
            _emit_parsing_status(app, PARSING_STATUS_KEY_EXTREMISTS, "done")


class MonitoringParsingView(BaseView):
    """Admin page: last run times for inagents and extremists list parsing (Redis via Parser.get_last_parse_datetime)."""

    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.has_role("admin")

    def inaccessible_callback(self, name: str, **kwargs) -> redirect:
        return redirect(url_for("admin_auth.login", next=request.url))

    def _submit_job(self, job_func: Callable[[Flask], None], status_key: str) -> bool:
        executor = current_app.extensions.get("executor")

        if executor is None:
            return False

        redis_client = getattr(current_app, "redis_client_tasks", None)
        if redis_client is not None:
            redis_client.set(status_key, "running", ex=PARSING_STATUS_TTL_SECONDS)

        app: Flask = current_app._get_current_object()
        _emit_parsing_status(app, status_key, "running")
        executor.submit(job_func, app)

        return True

    def _is_job_running(self, status_key: str) -> bool:
        redis_client = getattr(current_app, "redis_client_tasks", None)

        if redis_client is None:
            return False

        return bool(redis_client.get(status_key))

    @expose("/run-inagents", methods=["POST"])
    def run_inagents(self) -> Response:
        app: Flask = current_app._get_current_object()
        is_ajax: bool = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if self._is_job_running(PARSING_STATUS_KEY_INAGENTS):
            if is_ajax:
                return jsonify(
                    success=True,
                    payload=_parsing_realtime_payload(app, PARSING_STATUS_KEY_INAGENTS, "running"),
                )

        elif self._submit_job(_run_inagents_update_job, PARSING_STATUS_KEY_INAGENTS):
            if is_ajax:
                return jsonify(
                    success=True,
                    payload=_parsing_realtime_payload(app, PARSING_STATUS_KEY_INAGENTS, "running"),
                )

        else:
            if is_ajax:
                return jsonify(success=False), 503
            flash("Executor недоступен. Не удалось запустить обновление.")

        return redirect(url_for(".index"))

    @expose("/run-extremists", methods=["POST"])
    def run_extremists(self) -> Response:
        app: Flask = current_app._get_current_object()
        is_ajax: bool = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if self._is_job_running(PARSING_STATUS_KEY_EXTREMISTS):
            if is_ajax:
                return jsonify(
                    success=True,
                    payload=_parsing_realtime_payload(app, PARSING_STATUS_KEY_EXTREMISTS, "running"),
                )

        elif self._submit_job(_run_extremists_parse_job, PARSING_STATUS_KEY_EXTREMISTS):
            if is_ajax:
                return jsonify(
                    success=True,
                    payload=_parsing_realtime_payload(app, PARSING_STATUS_KEY_EXTREMISTS, "running"),
                )

        else:
            if is_ajax:
                return jsonify(success=False), 503
            flash("Executor недоступен. Не удалось запустить обновление.")

        return redirect(url_for(".index"))

    @expose("/")
    def index(self, **kwargs):
        app: Flask = current_app._get_current_object()
        inagents_payload: dict[str, str | bool] = _parsing_realtime_payload(app, PARSING_STATUS_KEY_INAGENTS, "snapshot")
        extremists_payload: dict[str, str | bool] = _parsing_realtime_payload(app, PARSING_STATUS_KEY_EXTREMISTS, "snapshot")
        rows: list[dict[str, str | bool]] = [
            {
                "key": PARSING_STATUS_KEY_INAGENTS,
                "title": "Иноагенты",
                "last_parse": str(inagents_payload["last_parse"]),
                "status": str(inagents_payload["status"]),
                "run_url": url_for(".run_inagents"),
                "can_run": bool(inagents_payload["can_run"]),
            },
            {
                "key": PARSING_STATUS_KEY_EXTREMISTS,
                "title": "Экстремисты",
                "last_parse": str(extremists_payload["last_parse"]),
                "status": str(extremists_payload["status"]),
                "run_url": url_for(".run_extremists"),
                "can_run": bool(extremists_payload["can_run"]),
            },
        ]

        return self.render(
            "admin/monitoring_parsing.html",
            rows=rows,
        )


class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.has_role("admin")

    def inaccessible_callback(self, name: str, **kwargs) -> redirect:
        return redirect(url_for("admin_auth.login", next=request.url))


class SecureModelView(ModelView):
    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.has_role("admin")

    def inaccessible_callback(self, name: str, **kwargs) -> redirect:
        return redirect(url_for("admin_auth.login", next=request.url))


class UserView(SecureModelView):
    column_exclude_list = ["password_hash"]
    form_excluded_columns = ["password_hash"]
    form_extra_fields = {"password": PasswordField("Password (required on create, leave blank on edit)")}
    column_list = ["id", "username", "email", "is_active", "created_at", "role"]
    column_searchable_list = ["username", "email"]
    form_columns = ["username", "email", "is_active", "role"]

    def on_model_change(self, form, model, is_created: bool) -> None:
        if is_created and (not getattr(form, "password", None) or not form.password.data):
            raise ValueError("Password is required when creating a user.")
        if getattr(form, "password", None) and form.password.data:
            model.set_password(form.password.data)


class RoleView(SecureModelView):
    column_list = ["id", "name", "description"]
    column_searchable_list = ["name"]
    form_columns = ["name", "description"]


MODEL_MAP: dict[str, type] = {"User": User, "Role": Role}

VIEW_CLASS_MAP: dict[str, type] = {
    "UserView": UserView,
    "RoleView": RoleView,
    "InagentsListView": InagentsListView,
    "WordsListView": WordsListView,
    "SearchSettingsView": SearchSettingsView,
    "AutoloadView": AutoloadView,
    "MonitoringTasksView": MonitoringTasksView,
    "MonitoringParsingView": MonitoringParsingView,
}


def init_admin(app: Flask, db) -> Admin:
    admin = Admin(
        app,
        name="Kramola",
        theme=Bootstrap4Theme(swatch="cerulean"),
        index_view=SecureAdminIndexView(url="/admin", endpoint="admin", name="Главная"),
    )

    with app.app_context():
        has_pl_lists = "pl_lists" in inspect(db.engine).get_table_names()
        list_records = (
            ListRecord.query.order_by(ListRecord.id).all()
            if has_pl_lists
            else []
        )

    for group in MENU_SPEC:
        category: str | None = group.get("category")
        for view_spec in group["views"]:
            if view_spec.get("dynamic"):
                for list_record in list_records:
                    if list_record.slug in view_spec.get("exclude_slugs", ()):
                        continue
                    endpoint = f"words_list_{list_record.slug.replace('-', '_')}"
                    view_cls = VIEW_CLASS_MAP[view_spec["view_class"]]
                    admin.add_view(
                        view_cls(
                            list_record.slug,
                            name=list_record.title or list_record.slug,
                            url=f"words-list/{list_record.slug}",
                            endpoint=endpoint,
                            category=category,
                        )
                    )
                continue

            view_cls = VIEW_CLASS_MAP[view_spec["view_class"]]
            name = view_spec["name"]
            kwargs: dict = {"name": name, "category": category}
            if "url" in view_spec:
                kwargs["url"] = view_spec["url"]
            if "endpoint" in view_spec:
                kwargs["endpoint"] = view_spec["endpoint"]
            if "model" in view_spec:
                model = MODEL_MAP[view_spec["model"]]
                admin.add_view(view_cls(model, db.session, **kwargs))
            else:
                admin.add_view(view_cls(**kwargs))

    return admin
