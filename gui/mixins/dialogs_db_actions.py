"""
Dialogs mixin - Database window CRUD actions (edit, duplicate, filter)
Миксин диалогов - CRUD действия окна БД (редактирование, дублирование, фильтрация)
Міксин діалогів - CRUD дії вікна БД (редагування, дублювання, фільтрація)

Содержит методы для редактирования, дублирования и фильтрации записей.
"""
from __future__ import annotations

import tkinter as tk
import json
import customtkinter as ctk
from utils.logger import get_logger
from gui.dialogs import CTkMessageBox
from Langs.lang import LANGUAGES
from utils.helpers import apply_window_rounding
from gui.mixins.dialogs_helpers import _setup_window_style, _get_colors_for_theme
from storage.database_db_helpers import _calc_strength, _pwd_age_days, _age_badge

logger = get_logger("dialogs_db_actions")


class DialogsDBActionsMixin:
    """CRUD actions for database dialog window (edit, duplicate, filter)

    CRUD действия для окна базы данных (редактирование, дублирование, фильтрация)
    CRUD дії для вікна бази даних (редагування, дублювання, фільтрація)
    """

    def _open_edit_dialog(self, rec: dict) -> None:
        """Open edit dialog for a record with extended fields"""
        L = LANGUAGES.get(self.current_lang, LANGUAGES.get("EN", LANGUAGES.get("RU")))
        colors = _get_colors_for_theme(self._get_actual_theme())
        radius = self.current_radius

        dlg = ctk.CTkToplevel(self.db_window)
        dlg.title(L.get("db_edit_title", "Edit / Редактирование / Редагування"))
        dlg.resizable(False, True)
        dlg.transient(self.db_window)
        dlg.grab_set()
        dlg.protocol("WM_DELETE_WINDOW", lambda: [dlg.grab_release(), dlg.destroy()])
        dlg.lift()
        dlg.focus_force()
        dlg.after(80, lambda: dlg.attributes("-topmost", False) if dlg and dlg.winfo_exists() else None)
        dlg.attributes("-topmost", True)

        try:
            _setup_window_style(dlg)
            apply_window_rounding(dlg)
        except (tk.TclError, AttributeError, OSError):
            pass

        dlg.configure(fg_color=colors["bg"])

        ctk.CTkLabel(dlg, text=L.get("db_edit_title", "Edit / Редактирование / Редагування"),
                    font=("Segoe UI", 18, "bold"), text_color=colors["label_text"]).pack(pady=(15, 10))

        ctk.CTkFrame(dlg, height=2, fg_color="#2d6a4f").pack(fill="x", padx=20, pady=(0, 15))

        scroll_frame = ctk.CTkFrame(dlg, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        fields = [
            ("db_edit_label", "Label / Метка / Мітка", "label", lbl_var := tk.StringVar(value=rec["label"]), "Segoe UI"),
            ("db_edit_pass", "Password / Пароль / Пароль", "password", pwd_var := tk.StringVar(), "Consolas"),
            ("db_edit_url", "URL / Сайт / Сайт", "url", url_var := tk.StringVar(value=rec.get("url", ""))),
            ("db_edit_username", "Username / Логин / Логін", "username", user_var := tk.StringVar(value=rec.get("username", ""))),
            ("db_edit_email", "Email", "email", email_var := tk.StringVar(value=rec.get("email", ""))),
            ("db_edit_category", "Category / Категория / Категорія", "category", cat_var := tk.StringVar(value=rec.get("category", "")))
        ]

        for key, default_text, db_key, var, *font_family in fields:
            font_name = font_family[0] if font_family else "Segoe UI"
            f_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            f_frame.pack(fill="x", pady=5)

            ctk.CTkLabel(f_frame, text=L.get(key, default_text) + ":",
                        font=("Segoe UI", 13), text_color=colors["label_text"], width=110, anchor="w").pack(side="left")

            entry = ctk.CTkEntry(f_frame, textvariable=var, width=340, height=35,
                                font=(font_name, 13), fg_color=colors["entry_bg"],
                                text_color=colors["fg"], corner_radius=radius)
            if db_key == "password":
                entry.configure(show="*")
            entry.pack(side="left", padx=(10, 0), fill="x", expand=True)

        fav_var = tk.BooleanVar(value=rec.get("favorite", 0) == 1)
        ctk.CTkCheckBox(scroll_frame, text=L.get("db_edit_favorite", "Favorite / Избранное / Обране"),
                        variable=fav_var, font=("Segoe UI", 13)).pack(anchor="w", pady=10)

        notes_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        notes_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(notes_frame, text=L.get("db_notes", "Notes / Заметки / Нотатки") + ":",
                    font=("Segoe UI", 13), text_color=colors["label_text"], anchor="nw").pack(anchor="nw")
        notes_text = ctk.CTkTextbox(notes_frame, height=80, font=("Segoe UI", 12),
                                   fg_color=colors["entry_bg"], text_color=colors["fg"], corner_radius=radius)
        notes_text.pack(fill="x", pady=(5, 0))
        notes_text.insert("1.0", rec.get("notes", ""))

        # Password age info
        _pca = rec.get("password_changed_at", "") or rec.get("created", "")
        _age_days = _pwd_age_days(_pca)
        _badge_txt, _badge_col = _age_badge(_age_days)
        age_line = f"{L.get('icon_key', '')} {L.get('age_changed', 'Password changed / Пароль изменён / Пароль змінено')}: {_pca[:10]}"
        if _badge_txt:
            age_line += f"   {_badge_txt}"
        ctk.CTkLabel(scroll_frame, text=age_line,
                     font=("Segoe UI", 11),
                     text_color=_badge_col or "gray").pack(anchor="w", pady=(6, 2))

        # Custom Fields editor
        ctk.CTkFrame(scroll_frame, height=2, fg_color="#2d4a6a").pack(fill="x", pady=(10, 6))

        cf_header_row = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        cf_header_row.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(cf_header_row,
                     text=L.get("cf_title", "Custom Fields / Доп. поля / Дод. поля"),
                     font=("Segoe UI", 13, "bold"),
                     text_color="#9b8ec4").pack(side="left")

        try:
            _cf_init = json.loads(rec.get("custom_fields", "[]") or "[]")
            if not isinstance(_cf_init, list):
                _cf_init = []
        except (json.JSONDecodeError, TypeError):
            _cf_init = []

        cf_rows_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        cf_rows_frame.pack(fill="x", pady=(0, 0))

        _cf_rows: list = []

        def _add_cf_row(name: str = "", value: str = "", hidden: bool = False) -> None:
            """
            Handle add cf row.
            Обработать add cf row.
            Обробити add cf row.
            """
            row = ctk.CTkFrame(cf_rows_frame, fg_color="transparent")
            row.pack(fill="x", pady=3)

            nv = tk.StringVar(value=name)
            vv = tk.StringVar(value=value)
            hv = tk.BooleanVar(value=hidden)

            ctk.CTkEntry(row, textvariable=nv, width=138, height=30,
                         font=("Segoe UI", 12), fg_color=colors["entry_bg"],
                         text_color=colors["fg"], corner_radius=radius,
                         placeholder_text=L.get("cf_name", "Field / Поле / Поле")
                         ).pack(side="left", padx=(0, 5))

            val_e = ctk.CTkEntry(row, textvariable=vv, width=178, height=30,
                                  font=("Segoe UI", 12), fg_color=colors["entry_bg"],
                                  text_color=colors["fg"], corner_radius=radius,
                                  placeholder_text=L.get("cf_val", "Value / Значение / Значення"),
                                  show="*" if hidden else "")
            val_e.pack(side="left", padx=(0, 5))

            def _toggle(e=val_e, h=hv) -> None:
                """
                Handle toggle.
                Обработать toggle.
                Обробити toggle.
                """
                e.configure(show="*" if h.get() else "")

            ctk.CTkCheckBox(row,
                            text=L.get("cf_hide", "Hide / Скрыть / Приховати"),
                            variable=hv, width=90, font=("Segoe UI", 11),
                            command=lambda e=val_e, h=hv: _toggle(e, h)
                            ).pack(side="left", padx=(0, 5))

            rd = {"name_var": nv, "value_var": vv, "hidden_var": hv, "frame": row}

            def _remove(r=rd) -> None:
                """
                Handle remove.
                Обработать remove.
                Обробити remove.
                """
                try:
                    r["frame"].destroy()
                    _cf_rows.remove(r)
                except (tk.TclError, ValueError):
                    pass

            ctk.CTkButton(row, text=L.get("icon_close_sm", "x"), width=28, height=28,
                          font=("Segoe UI", 13, "bold"),
                          fg_color="#8b0000", hover_color="#b30000",
                          corner_radius=radius, command=_remove).pack(side="left")

            _cf_rows.append(rd)

        ctk.CTkButton(scroll_frame,
                      text=L.get("cf_add", "+ Add field / + Добавить / + Додати"),
                      width=210, height=30, font=("Segoe UI", 11, "bold"),
                      fg_color="#2d4a6a", hover_color="#3a6090",
                      corner_radius=radius, command=_add_cf_row
                      ).pack(anchor="center", pady=(0, 8))

        for _f in _cf_init:
            _add_cf_row(_f.get("name", ""), _f.get("value", ""), bool(_f.get("hidden", False)))

        # Tags editor
        ctk.CTkFrame(scroll_frame, height=2, fg_color="#2d4a2d").pack(fill="x", pady=(10, 6))
        ctk.CTkLabel(scroll_frame,
                     text=L.get("tags_title", "Tags / Теги / Теги"),
                     font=("Segoe UI", 13, "bold"), text_color="#7ec87e").pack(anchor="w")
        ctk.CTkLabel(scroll_frame,
                     text=L.get("tags_hint",
                                "Comma-separated / Через запятую / Через кому"),
                     font=("Segoe UI", 10), text_color="gray").pack(anchor="w")

        try:
            _existing_tags = json.loads(rec.get("tags", "[]") or "[]")
            if not isinstance(_existing_tags, list):
                _existing_tags = []
        except (json.JSONDecodeError, TypeError):
            _existing_tags = []

        tags_var = tk.StringVar(value=", ".join(str(t) for t in _existing_tags))
        ctk.CTkEntry(scroll_frame, textvariable=tags_var, height=30,
                     font=("Segoe UI", 12), fg_color=colors["entry_bg"],
                     text_color=colors["fg"], corner_radius=radius,
                     placeholder_text="работа, 2FA, важное"
                     ).pack(fill="x", pady=(4, 10))

        # Save / Cancel buttons
        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(side="bottom", pady=(8, 14))

        def do_save_edit() -> None:
            """
            Handle do save edit.
            Обработать do save edit.
            Обробити do save edit.
            """
            from storage.database import PasswordDB
            new_label = lbl_var.get().strip() or L.get("db_no_label", "No label")
            new_pwd = pwd_var.get().strip() or None

            cf_data = [
                {"name": r["name_var"].get().strip(),
                 "value": r["value_var"].get(),
                 "hidden": r["hidden_var"].get()}
                for r in _cf_rows
                if r["name_var"].get().strip()
            ]
            cf_json = json.dumps(cf_data, ensure_ascii=False)

            tags_list = [t.strip() for t in tags_var.get().split(",") if t.strip()]
            tags_json = json.dumps(tags_list, ensure_ascii=False)

            # ── Validate before writing to DB ────────────────────
            from core.validators import validate, LabelValidator, URLValidator, EmailValidator, CategoryValidator, TagValidator
            _url   = url_var.get().strip()
            _email = email_var.get().strip()
            _cat   = cat_var.get().strip()
            _errs = validate(
                new_label, LabelValidator(required=True),
                _url,      URLValidator(required=False),
                _email,    EmailValidator(required=False),
                _cat,      CategoryValidator(required=False),
            )
            if tags_list:
                _tag_v = TagValidator(required=False)
                _tag_r = _tag_v.validate_list(tags_list)
                _errs.extend(_tag_r.errors)

            if _errs:
                CTkMessageBox.warning(
                    dlg,
                    L.get("err_title", "Error"),
                    "\n".join(_errs[:3])
                )
                return

            try:
                PasswordDB.update(
                    rec["id"], new_label, new_pwd,
                    notes_text.get("1.0", "end-1c").strip(),
                    _url, user_var.get().strip(),
                    _email, _cat,
                    1 if fav_var.get() else 0,
                    custom_fields=cf_json,
                    tags=tags_json
                )
                dlg.destroy()
                self._refresh_db_window()
            except sqlite3.Error:
                pass

        ctk.CTkButton(btn_row, text=L.get("save", "Save / Сохранить / Зберегти"), width=110, height=34,
                     fg_color="#2d6a4f", corner_radius=radius, command=do_save_edit).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text=L.get("cancel", "Cancel / Отмена / Скасувати"), width=110, height=34,
                     fg_color="#8b0000", corner_radius=radius, command=dlg.destroy).pack(side="left", padx=8)

        def _fit_and_center() -> None:
            """
            Handle fit and center.
            Обработать fit and center.
            Обробити fit and center.
            """
            try:
                dlg.update_idletasks()
                content_h = scroll_frame.winfo_reqheight()
                chrome_h = 145
                want_h = content_h + chrome_h
                screen_h = dlg.winfo_screenheight()
                final_h = min(want_h, int(screen_h * 0.92))
                w = 580
                px = self.db_window.winfo_rootx()
                py = self.db_window.winfo_rooty()
                pw = self.db_window.winfo_width()
                ph = self.db_window.winfo_height()
                x = px + (pw - w) // 2
                y = max(20, py + (ph - final_h) // 2)
                dlg.geometry(f"{w}x{final_h}+{x}+{y}")
            except (tk.TclError, AttributeError):
                dlg.geometry("580x860")

        dlg.after(50, _fit_and_center)

    def _duplicate_entry(self, rec: dict) -> None:
        """Create a copy of the record with label prefix 'Copy of'."""
        from storage.database import PasswordDB
        L = LANGUAGES.get(self.current_lang, LANGUAGES.get("EN", LANGUAGES.get("RU")))
        prefix = L.get("duplicate_prefix", "Copy of")
        new_label = f"{prefix} {rec.get('label', '')}".strip()[:200]
        # Sanitise duplicated label before saving
        from core.validators import sanitize_label
        new_label = sanitize_label(new_label)
        try:
            PasswordDB.save(
                label=new_label,
                password=rec.get("password", ""),
                notes=rec.get("notes", ""),
                url=rec.get("url", ""),
                username=rec.get("username", ""),
                email=rec.get("email", ""),
                category=rec.get("category", ""),
                favorite=rec.get("favorite", 0),
                custom_fields=rec.get("custom_fields", "[]"),
                tags=rec.get("tags", "[]"),
            )
            self._refresh_db_window()
            logger.info(f"Duplicated record id={rec.get('id')} → '{new_label}'")
        except (sqlite3.Error, OSError) as e:
            CTkMessageBox.error(self.db_window, L.get("err_title", "Error"), str(e))

    def _filter_expired(self) -> None:
        """Set sort to password age so expired passwords appear first."""
        try:
            if hasattr(self, '_db_sort_var') and self._db_sort_var:
                self._db_sort_var.set("pwd_age_asc")
                self._refresh_db_window()
        except (OSError, ValueError, TypeError, AttributeError, RuntimeError, tk.TclError):
            pass
