from sqlalchemy import Date, func, inspect, or_

from extensions import db
from flask import Flask, flash, jsonify, redirect, render_template, request, Response, url_for
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_login import current_user
from wtforms import PasswordField

from models import Inagent, User, Role
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
    def index(self):
        list_record = ListRecord.query.filter_by(slug=self.list_slug).first()
        total_count: int = get_phrases_count(list_record) if list_record else 0
        list_title = list_record.title if list_record else self.list_slug
        import_url = url_for(".import_phrases") if list_record else None
        export_url = url_for(".export_phrases") if list_record else None
        minusate_url = url_for(".minusate_phrases") if list_record else None
        endpoint = self.endpoint
        data_url = url_for(f"{endpoint}.data_route") if list_record else None
        return self.render(
            "admin/words_list.html",
            list_title=list_title,
            list_slug=self.list_slug,
            total_count=total_count,
            import_url=import_url,
            export_url=export_url,
            minusate_url=minusate_url,
            data_url=data_url,
        )

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
        list_record = ListRecord.query.filter_by(slug=self.list_slug).first()
        if not list_record:
            return redirect(url_for(".index"))
        if remove_phrase_from_list(list_record, phrase_id):
            flash("Фраза удалена из списка.")
        else:
            flash("Фраза не найдена в списке.")
        return redirect(url_for(".index"))

    @expose("/data")
    def data_route(self):
        list_record = ListRecord.query.filter_by(slug=self.list_slug).first()
        if not list_record:
            return jsonify(data=[], total=0)
        limit = request.args.get("limit", 100, type=int)
        offset = request.args.get("offset", 0, type=int)
        query = request.args.get("q", "").strip() or None
        limit = min(max(1, limit), 500)
        offset = max(0, offset)
        words_list, total = get_phrases_paginated(list_record, limit=limit, offset=offset, query=query)
        endpoint = self.endpoint
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


class InagentsListView(BaseView):
    def is_visible(self) -> bool:
        return False

    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.has_role("admin")

    def inaccessible_callback(self, name: str, **kwargs) -> redirect:
        return redirect(url_for("admin_auth.login", next=request.url))

    @expose("/")
    def index(self):
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
                Inagent.search_terms.isnot(None),
                func.json_length(Inagent.search_terms) > 0,
            )
        elif phrases_filter == "no":
            query = query.filter(
                or_(
                    Inagent.search_terms.is_(None),
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
            search_terms_count: int = len(r.search_terms) if isinstance(r.search_terms, list) else 0
            return {
                "id": r.id,
                "registry_number": r.registry_number,
                "full_name": r.full_name or "",
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
        form_to_inagent(request.form, inagent)
        db.session.commit()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(success=True)
        flash("Инагент сохранён.")
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
        "search_terms": _domain_to_text(inagent.search_terms),
        "activity": "",
    }


def _domain_to_text(domain_name: list | None) -> str:
    if not domain_name:
        return ""
    return "\n".join(domain_name) if isinstance(domain_name, list) else str(domain_name)


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

    search_terms_raw = form.get("search_terms", "").strip()
    inagent.search_terms = [s.strip() for s in search_terms_raw.split() if s.strip()] if search_terms_raw else None


def _parse_date(s: str | None):
    if not s or not s.strip():
        return None
    from datetime import datetime
    try:
        return datetime.strptime(s.strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


class AutoloadView(BaseView):
    """Admin page for autoload lists logs."""

    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.has_role("admin")

    def inaccessible_callback(self, name: str, **kwargs) -> redirect:
        return redirect(url_for("admin_auth.login", next=request.url))

    @expose("/")
    def index(self):
        return self.render("admin/autoload.html")


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


def init_admin(app: Flask, db) -> Admin:
    admin = Admin(
        app,
        name="Kramola",
        theme=Bootstrap4Theme(swatch="cerulean"),
        index_view=SecureAdminIndexView(url="/admin", endpoint="admin", name="Главная"),
    )
    admin.add_view(UserView(User, db.session, category="Пользователи", name="Пользователи"))
    admin.add_view(RoleView(Role, db.session, category="Пользователи", name="Роли"))
    admin.add_view(
        InagentsListView(
            name="Инагенты",
            url="inagents-list",
            endpoint="inagents_list",
            category="Готовые списки",
        )
    )
    admin.add_view(AutoloadView(name="Автозагрузка", url="autoload", endpoint="autoload"))
    with app.app_context():
        has_pl_lists = "pl_lists" in inspect(db.engine).get_table_names()
        list_records = (
            ListRecord.query.order_by(ListRecord.id).all()
            if has_pl_lists
            else []
        )
    for list_record in list_records:
        endpoint = f"words_list_{list_record.slug.replace('-', '_')}"
        admin.add_view(
            WordsListView(
                list_record.slug,
                name=list_record.title or list_record.slug,
                url=f"words-list/{list_record.slug}",
                endpoint=endpoint,
                category="Готовые списки",
            )
        )
    return admin
