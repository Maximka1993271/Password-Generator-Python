"""
Dialogs mixin - Database window core (show, refresh, close)
Миксин диалогов - Ядро окна базы данных (показ, обновление, закрытие)
Міксин діалогів - Ядро вікна бази даних (показ, оновлення, закриття)

Содержит основные методы для отображения и управления окном БД.
"""
from __future__ import annotations

import tkinter as tk
import customtkinter as ctk
from utils.logger import get_logger
from gui.dialogs import CTkMessageBox
from Langs.lang import LANGUAGES
from utils.helpers import apply_window_rounding
from gui.mixins.dialogs_helpers import _setup_window_style, _get_colors_for_theme

logger = get_logger("dialogs_db_core")


class DialogsDBCoreMixin:
    """Core methods for database dialog window (show, refresh, close)

    Основные методы для окна базы данных (показ, обновление, закрытие)
    Основні методи для вікна бази даних (показ, оновлення, закриття)
    """

    def _show_db_window(self) -> None:
        """Show password database window with extended fields support"""
        L = LANGUAGES.get(self.current_lang, LANGUAGES.get("EN", LANGUAGES.get("RU")))
        colors = _get_colors_for_theme(self._get_actual_theme())
        radius = self.current_radius

        if self.db_window and self.db_window.winfo_exists():
            try:
                self.db_window.lift()
                self.db_window.focus_force()
            except tk.TclError:
                self.db_window = None
                self._show_db_window()
            return

        self.db_window = ctk.CTkToplevel(self)
        self.db_window.title(L.get("db_title", "Password Vault / База данных / База даних"))
        self.db_window.resizable(True, True)
        self.db_window.minsize(1150, 700)

        try:
            _setup_window_style(self.db_window)
        except (AttributeError, OSError) as e:
            logger.debug(f"Setup window style error: {e}")

        try:
            apply_window_rounding(self.db_window)
        except (AttributeError, OSError) as e:
            logger.debug(f"Window rounding error: {e}")

        try:
            self._center_window_relative_to_parent(self.db_window, 1150, 700)
        except (tk.TclError, AttributeError) as e:
            logger.debug(f"Center window error: {e}")
            self.db_window.geometry("1150x700")

        self.db_window.configure(fg_color=colors["bg"])
        self.db_window.protocol("WM_DELETE_WINDOW", self._close_db_window)

        # Store references
        self._db_scroll_frame = None
        self._db_search_var = None
        self._db_count_label = None
        self._db_category_filter_var = None
        self._db_show_favorites_var = None
        self._db_sort_var = None

        # Header
        header_frame = ctk.CTkFrame(self.db_window, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 5))

        ctk.CTkLabel(header_frame, text=L.get("db_title", "Password Vault / База данных / База даних"),
                    font=("Segoe UI", 22, "bold"), text_color=colors["label_text"]).pack(anchor="center")

        ctk.CTkFrame(self.db_window, height=2, fg_color="#2d6a4f").pack(fill="x", padx=20, pady=(5, 15))

        # Top panel
        top_panel = ctk.CTkFrame(self.db_window, fg_color="transparent")
        top_panel.pack(fill="x", padx=20, pady=(0, 10))

        # Search row
        search_frame = ctk.CTkFrame(top_panel, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(search_frame, text=L.get("db_search", "Search / Поиск / Пошук") + ":",
                    font=("Segoe UI", 13, "bold"), text_color=colors["label_text"]).pack(side="left", padx=(0, 10))

        search_var = tk.StringVar()
        self._db_search_var = search_var

        placeholder = L.get("db_search_placeholder", "Search by label, password, URL, username, email...")
        search_entry = ctk.CTkEntry(search_frame, textvariable=search_var, height=36,
                                    font=("Segoe UI", 13), fg_color=colors["entry_bg"],
                                    text_color=colors["fg"], corner_radius=radius,
                                    placeholder_text=placeholder)
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 15))

        def on_search(*args) -> None:
            """
            Handle the search event.
            Обработчик события search.
            Обробник події search.
            """
            try:
                self._refresh_db_window()
            except (tk.TclError, sqlite3.Error, RuntimeError) as e:
                logger.error(f"Search error: {e}")

        try:
            search_var.trace_add("write", on_search)
        except AttributeError:
            search_var.trace("w", on_search)

        # Filter row
        filter_frame = ctk.CTkFrame(top_panel, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 10))

        # Category filter
        ctk.CTkLabel(filter_frame, text=L.get("db_category_filter", "Category / Категория / Категорія") + ":",
                    font=("Segoe UI", 13, "bold"), text_color=colors["label_text"]).pack(side="left", padx=(0, 10))

        category_var = tk.StringVar(value="")
        self._db_category_filter_var = category_var

        from storage.database import PasswordDB
        categories = PasswordDB.get_categories()
        category_options = [""] + categories
        category_menu = ctk.CTkOptionMenu(filter_frame, values=category_options, variable=category_var,
                                          width=150, font=("Segoe UI", 12), corner_radius=radius)
        category_menu.pack(side="left", padx=(0, 15))

        # Favorite filter checkbox
        show_favorites_var = tk.BooleanVar(value=False)
        self._db_show_favorites_var = show_favorites_var
        fav_check = ctk.CTkCheckBox(filter_frame, text=L.get("db_favorites_only", "Favorites only / Только избранные / Тільки обрані"),
                                     variable=show_favorites_var, font=("Segoe UI", 12))
        fav_check.pack(side="left", padx=(0, 15))

        # Sort option
        ctk.CTkLabel(filter_frame, text=L.get("db_sort", "Sort / Сортировка / Сортування") + ":",
                    font=("Segoe UI", 13, "bold"), text_color=colors["label_text"]).pack(side="left", padx=(15, 10))

        sort_var = tk.StringVar(value="favorite_desc")
        self._db_sort_var = sort_var
        sort_options = [
            (L.get("db_sort_favorite", "Favorites first / Сначала избранные / Спочатку обрані"), "favorite_desc"),
            (L.get("db_sort_date_desc", "Newest first / Сначала новые / Спочатку нові"), "date_desc"),
            (L.get("db_sort_date_asc", "Oldest first / Сначала старые / Спочатку старі"), "date_asc"),
            (L.get("db_sort_label_asc", "Label A-Z / Имя А-Я / Назва А-Я"), "label_asc"),
            (L.get("db_sort_label_desc", "Label Z-A / Имя Я-А / Назва Я-А"), "label_desc"),
            (L.get("db_sort_category", "By category / По категориям / За категоріями"), "category_asc"),
        ]

        sort_menu = ctk.CTkOptionMenu(filter_frame, values=[opt[0] for opt in sort_options],
                                       variable=sort_var, width=480, font=("Segoe UI", 12),
                                       corner_radius=radius, command=lambda x: self._refresh_db_window())
        sort_menu.pack(side="left", padx=(10, 0))

        # Save current password button
        def do_save_current() -> None:
            """
            Handle do save current.
            Обработать do save current.
            Обробити do save current.
            """
            try:
                pwd = None
                if hasattr(self, 'entry_res') and self.entry_res:
                    try:
                        pwd = self.entry_res.get()
                    except tk.TclError:
                        pass

                if not pwd and hasattr(self, 'master') and hasattr(self.master, 'entry_res'):
                    try:
                        pwd = self.master.entry_res.get()
                    except (AttributeError, tk.TclError):
                        pass

                if not pwd:
                    CTkMessageBox.warning(self.db_window, L.get("db_title", "Password Vault"),
                                         L.get("db_no_pass", "Generate a password first! / Сначала создайте пароль! / Спочатку створить пароль!"))
                    return

                import datetime
                label = f"Auto {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                from storage.database import PasswordDB
                from core.validators import validate, LabelValidator, PasswordValidator
                _errs = validate(
                    label, LabelValidator(required=True),
                    pwd,   PasswordValidator(required=True, min_length=1),
                )
                if _errs:
                    CTkMessageBox.warning(
                        self.db_window,
                        L.get("err_title", "Error"),
                        "\n".join(_errs[:3])
                    )
                    return
                PasswordDB.save(label, pwd)
                CTkMessageBox.info(self.db_window, L.get("db_title", "Password Vault"),
                                  L.get("db_saved", "Password saved! / Пароль сохранен! / Пароль збережено!"))
                search_var.set("")
                category_var.set("")
                show_favorites_var.set(False)
                self._refresh_db_window()
                logger.info("Password saved to database")

            except sqlite3.Error as e:
                logger.error(f"Database error saving password: {e}")
                CTkMessageBox.error(self.db_window, L.get("err_title", "Error"), f"{L.get('err_database', 'Database error')}: {e}")
            except (AttributeError, TypeError, OSError, IOError) as e:
                logger.error(f"Error saving password: {e}")
                CTkMessageBox.error(self.db_window, L.get("err_title", "Error"), f"{L.get('err_save', 'Save error')}: {e}")

        save_btn = ctk.CTkButton(
            top_panel,
            text=L.get("db_save_current", "Save current password / Сохранить текущий пароль / Зберегти поточний пароль"),
            width=220,
            height=36,
            fg_color="#1a6b5a",
            hover_color="#2da882",
            font=("Segoe UI", 13, "bold"),
            corner_radius=radius,
            command=do_save_current
        )
        save_btn.pack(anchor="e", pady=(5, 0))

        # Export/Import buttons
        buttons_row = ctk.CTkFrame(self.db_window, fg_color="transparent")
        buttons_row.pack(fill="x", padx=20, pady=(0, 15))

        def do_export() -> None:
            """
            Handle do export.
            Обработать do export.
            Обробити do export.
            """
            try:
                from utils.export import DataExporter
                from storage.database import PasswordDB
                passwords = PasswordDB.get_all()
                if not passwords:
                    CTkMessageBox.warning(self.db_window, L.get("export_title", "Export"),
                                         L.get("export_no_data", "No data to export / Нет данных для экспорта / Немає даних для експорту"))
                    return
                DataExporter.show_export_dialog(passwords, self.db_window, self.current_lang)
            except ImportError as e:
                logger.error(f"Export module import error: {e}")
                CTkMessageBox.error(self.db_window, L.get("err_title", "Error"), f"Export module not available: {e}")
            except (sqlite3.Error, OSError, IOError) as e:
                logger.error(f"Export error: {e}")
                CTkMessageBox.error(self.db_window, L.get("err_title", "Error"), str(e))

        def do_import() -> None:
            """
            Handle do import.
            Обработать do import.
            Обробити do import.
            """
            try:
                from utils.import_passwords import PasswordImporter
                PasswordImporter.import_all(self.db_window, self.current_lang)
                self._refresh_db_window()
            except ImportError as e:
                logger.error(f"Import module import error: {e}")
                CTkMessageBox.error(self.db_window, L.get("err_title", "Error"), f"Import module not available: {e}")
            except (sqlite3.Error, OSError, IOError, ValueError) as e:
                logger.error(f"Import error: {e}")
                CTkMessageBox.error(self.db_window, L.get("err_title", "Error"), str(e))

        export_btn = ctk.CTkButton(
            buttons_row,
            text=L.get("export_title", "Export / Экспорт / Експорт"),
            command=do_export,
            fg_color="#9C27B0",
            hover_color="#BA68C8",
            width=160,
            height=38,
            corner_radius=radius,
            font=("Segoe UI", 13, "bold")
        )
        export_btn.pack(side="left", padx=(0, 15))

        import_btn = ctk.CTkButton(
            buttons_row,
            text=L.get("import_title", "Import / Импорт / Импорт"),
            command=do_import,
            fg_color="#FF9800",
            hover_color="#FFB74D",
            width=160,
            height=38,
            corner_radius=radius,
            font=("Segoe UI", 13, "bold")
        )
        import_btn.pack(side="left", padx=(0, 15))

        def do_cloud_sync() -> None:
            """
            Handle do cloud sync.
            Обработать do cloud sync.
            Обробити do cloud sync.
            """
            self._show_cloud_sync_dialog()

        sync_btn = ctk.CTkButton(
            buttons_row,
            text=L.get("sync_title", "Sync / Синхронизация / Синхронізація"),
            command=do_cloud_sync,
            fg_color="#1565C0",
            hover_color="#1976D2",
            width=160,
            height=38,
            corner_radius=radius,
            font=("Segoe UI", 13, "bold")
        )
        sync_btn.pack(side="left", padx=(0, 15))

        ctk.CTkButton(
            buttons_row,
            text=L.get("trash_btn", "Trash / Корзина / Кошик"),
            command=self._show_trash_dialog,
            fg_color="#5a2d2d", hover_color="#7a3d3d",
            width=140, height=38, corner_radius=radius, font=("Segoe UI", 13, "bold")
        ).pack(side="left", padx=(0, 15))

        ctk.CTkButton(
            buttons_row,
            text=L.get("stats_btn", "Stats / Статистика / Статистика"),
            command=self._show_stats_dialog,
            fg_color="#1a4a6a", hover_color="#2a6090",
            width=155, height=38, corner_radius=radius, font=("Segoe UI", 13, "bold")
        ).pack(side="left")

        # Bulk operations row
        bulk_row = ctk.CTkFrame(self.db_window, fg_color="transparent")
        bulk_row.pack(fill="x", padx=20, pady=(0, 8))

        def _show_bulk_menu() -> None:
            """
            Show the bulk menu UI.
            Показать интерфейс bulk menu.
            Показати інтерфейс bulk menu.
            """
            theme = self._get_actual_theme()
            is_dark = (theme == "dark")
            bg = "#1e1e1e" if is_dark else "#f0f0f0"
            fg = "#ffffff" if is_dark else "#1a1a1a"
            sel_bg = "#2d6a4f"
            sel_fg = "#ffffff"

            menu = tk.Menu(
                self.db_window, tearoff=0,
                font=("Segoe UI", 12),
                bg=bg, fg=fg,
                activebackground=sel_bg, activeforeground=sel_fg,
                bd=0, relief="flat",
            )
            menu.add_command(
                label=L.get("bulk_select_all", "Выбрать все / Select All / Вибрати всі"),
                command=self._bulk_select_all
            )
            menu.add_separator()
            menu.add_command(
                label=L.get("bulk_delete_all", "Удалить все / Delete All / Видалити всі"),
                command=self._bulk_delete_all
            )
            menu.add_command(
                label=L.get("bulk_move_all",   "Переместить все / Move All / Перемістити всі"),
                command=self._bulk_move_all_category
            )
            menu.add_command(
                label=L.get("bulk_export_all", "Экспорт всех / Export All / Експорт усіх"),
                command=self._bulk_export_all
            )
            try:
                bx = bulk_btn.winfo_rootx()
                by = bulk_btn.winfo_rooty() + bulk_btn.winfo_height()
                menu.tk_popup(bx, by)
            finally:
                menu.grab_release()

        bulk_btn = ctk.CTkButton(
            bulk_row,
            text=L.get("bulk_btn", "Действия со всеми  ▾"),
            width=220, height=32,
            font=("Segoe UI", 12, "bold"),
            fg_color="#2b4a6a", hover_color="#3a6090",
            corner_radius=radius,
            command=_show_bulk_menu
        )
        bulk_btn.pack(side="left")

        # Counter
        count_lbl = ctk.CTkLabel(self.db_window, text="", font=("Segoe UI", 12), text_color="gray")
        count_lbl.pack(anchor="w", padx=20, pady=(0, 5))
        self._db_count_label = count_lbl

        # Scroll container
        scroll_frame = ctk.CTkScrollableFrame(self.db_window, fg_color=colors["bg"])
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self._db_scroll_frame = scroll_frame

        # Close button
        close_btn = ctk.CTkButton(
            self.db_window,
            text=L.get("close", "Close / Закрыть / Закрити"),
            width=140,
            height=38,
            fg_color="#ca5010",
            hover_color="#e05a1a",
            font=("Segoe UI", 13, "bold"),
            corner_radius=radius,
            command=self._close_db_window
        )
        close_btn.pack(pady=(0, 15))

        self._refresh_db_window()

        try:
            self.db_window.lift()
            self.db_window.focus_force()
            self.db_window.attributes("-topmost", True)
            self.db_window.after(100, lambda: self.db_window.attributes("-topmost", False) if self.db_window and self.db_window.winfo_exists() else None)
        except (tk.TclError, AttributeError):
            pass

    def _refresh_db_window(self) -> None:
        """Refresh database window content with filters"""
        from storage.database import PasswordDB
        from Langs.lang import LANGUAGES

        L = LANGUAGES.get(self.current_lang, LANGUAGES.get("EN", LANGUAGES.get("RU")))

        scroll_frame = getattr(self, '_db_scroll_frame', None)
        search_var = getattr(self, '_db_search_var', None)
        count_lbl = getattr(self, '_db_count_label', None)
        category_filter = getattr(self, '_db_category_filter_var', None)
        show_favorites = getattr(self, '_db_show_favorites_var', None)
        sort_by = getattr(self, '_db_sort_var', None)

        if scroll_frame is None or not scroll_frame.winfo_exists():
            return

        if not hasattr(self, '_db_expiry_warned'):
            self._db_expiry_warned = False
        if not self._db_expiry_warned:
            self._db_expiry_warned = True
            self.db_window.after(600, self._check_expiry_on_open)

        for w in scroll_frame.winfo_children():
            try:
                w.destroy()
            except tk.TclError:
                pass

        query = search_var.get().strip() if search_var else ""
        category = category_filter.get().strip() if category_filter else ""
        show_fav = show_favorites.get() if show_favorites else False
        sort_value = sort_by.get() if sort_by else "favorite_desc"

        sort_key = "favorite_desc"
        if "date_desc" in sort_value or "новые" in sort_value or "нові" in sort_value:
            sort_key = "date_desc"
        elif "date_asc" in sort_value or "старые" in sort_value or "старі" in sort_value:
            sort_key = "date_asc"
        elif "label_asc" in sort_value or "А-Я" in sort_value:
            sort_key = "label_asc"
        elif "label_desc" in sort_value or "Я-А" in sort_value:
            sort_key = "label_desc"
        elif "category" in sort_value or "категори" in sort_value:
            sort_key = "category_asc"

        try:
            if query:
                records = PasswordDB.search(query)
            elif category:
                records = PasswordDB.get_by_category(category)
            elif show_fav:
                records = PasswordDB.get_favorites()
            else:
                records = PasswordDB.get_sorted(sort_key)
        except (sqlite3.Error, ValueError, TypeError, OSError) as e:
            logger.error(f"DB access error: {e}")
            if count_lbl:
                count_lbl.configure(text=L.get("db_count", "Records: {0}").format(0))
            return

        if count_lbl:
            count_lbl.configure(text=L.get("db_count", "Records / Записей / Записів: {0}").format(len(records)))

        if not records:
            ctk.CTkLabel(scroll_frame, text=L.get("db_empty", "Vault is empty / База пуста / База порожня"),
                        font=("Segoe UI", 16), text_color="gray").pack(pady=50)
            return

        colors = _get_colors_for_theme(self._get_actual_theme())
        radius = self.current_radius

        for rec in records:
            try:
                card = ctk.CTkFrame(scroll_frame, fg_color="transparent")
                card.pack(fill="x", pady=8, padx=5)
                card.columnconfigure(0, weight=1)
                card.columnconfigure(1, weight=0)

                info_frame = ctk.CTkFrame(card, fg_color="transparent")
                info_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=2)

                label_row = ctk.CTkFrame(info_frame, fg_color="transparent")
                label_row.pack(anchor="w", fill="x", pady=(2, 4))

                def make_toggle_favorite(rid=rec["id"]) -> None:
                    """
                    Handle make toggle favorite.
                    Обработать make toggle favorite.
                    Обробити make toggle favorite.
                    """
                    from storage.database import PasswordDB
                    try:
                        PasswordDB.toggle_favorite(rid)
                        self._refresh_db_window()
                    except sqlite3.Error:
                        pass

                is_fav = rec.get("favorite", 0) == 1
                fav_btn = ctk.CTkButton(
                    label_row,
                    text=L.get("icon_star", "") if is_fav else L.get("icon_star_empty", ""),
                    width=35,
                    height=35,
                    font=("Segoe UI", 18, "bold"),
                    fg_color="#FFD700" if is_fav else "transparent",
                    text_color="#5a3e00" if is_fav else "#FFD700",
                    border_color="#FFD700",
                    border_width=1,
                    hover_color="#FFC800" if is_fav else "#333333",
                    corner_radius=radius,
                    command=make_toggle_favorite
                )
                fav_btn.pack(side="left", padx=(0, 12))

                label_text = rec["label"] if rec["label"] else f"{L.get('db_no_label', 'No label')} #{rec['id']}"
                label_color = "#FFD700" if is_fav else colors["label_text"]
                ctk.CTkLabel(label_row, text=label_text, font=("Segoe UI", 15, "bold"),
                            text_color=label_color, anchor="w").pack(side="left", fill="x", expand=True)

                # Password row with show/hide toggle
                pwd_row = ctk.CTkFrame(info_frame, fg_color="transparent")
                pwd_row.pack(anchor="w", fill="x", pady=2)

                _pwd_hidden = [True]
                _masked = "●" * min(len(rec["password"]), 12)
                pwd_lbl = ctk.CTkLabel(pwd_row, text=_masked, font=("Consolas", 14),
                                       text_color="#4EC9B0", anchor="w")
                pwd_lbl.pack(side="left")

                # Strength dot
                from storage.database_db_helpers import _calc_strength
                _score, _slabel, _scolor = _calc_strength(rec["password"])
                if _score > 0:
                    ctk.CTkLabel(pwd_row,
                                 text=L.get("icon_warn", "") if _score < 3 else "",
                                 width=8, height=8,
                                 fg_color=_scolor,
                                 corner_radius=4,
                                 text_color=_scolor).pack(side="left", padx=(4, 0))

                eye_btn = ctk.CTkButton(
                    pwd_row, text=L.get("icon_eye", ""), width=28, height=28,
                    font=("Segoe UI", 14), fg_color="transparent",
                    hover_color="#333333", text_color="#888888",
                    corner_radius=radius, command=None
                )
                eye_btn.pack(side="left", padx=(6, 0))

                def _make_toggle(lbl=pwd_lbl, p=rec["password"],
                                 state=_pwd_hidden, btn=eye_btn) -> None:
                    """
                    Handle make toggle.
                    Обработать make toggle.
                    Обробити make toggle.
                    """
                    if state[0]:
                        lbl.configure(text=p)
                        state[0] = False
                        btn.configure(text=L.get("icon_eye_off", ""))
                    else:
                        lbl.configure(text="●" * min(len(p), 12))
                        state[0] = True
                        btn.configure(text=L.get("icon_eye", ""))

                eye_btn.configure(command=_make_toggle)

                # Extended info frame (URL, username, email, category, tags, custom fields)
                ext_info_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
                ext_info_frame.pack(anchor="w", fill="x", pady=2)

                category_value = rec.get("category", "")
                if category_value and category_value.strip():
                    cat_title = L.get("db_edit_category", "Category / Категория / Категорія")
                    ctk.CTkLabel(ext_info_frame, text=f"{cat_title}: {category_value}",
                                font=("Segoe UI", 11, "bold"), text_color="#e2a145", anchor="w").pack(anchor="w", pady=1)

                info_row = ctk.CTkFrame(ext_info_frame, fg_color="transparent")
                info_row.pack(anchor="w", fill="x", pady=1)

                # Date
                from storage.database_db_helpers import _pwd_age_days, _age_badge
                ctk.CTkLabel(info_row, text=f"{L.get('icon_calendar', '')} {rec['created']}", font=("Segoe UI", 11),
                            text_color="gray").pack(side="left", padx=(0, 8))

                # Password age badge
                _age_days = _pwd_age_days(rec.get("password_changed_at", ""))
                _badge_txt, _badge_col = _age_badge(_age_days)
                if _badge_txt:
                    ctk.CTkLabel(info_row, text=_badge_txt,
                                 font=("Segoe UI", 11, "bold"),
                                 text_color=_badge_col).pack(side="left", padx=(0, 12))
                else:
                    ctk.CTkFrame(info_row, width=4, height=1,
                                 fg_color="transparent").pack(side="left")

                if rec.get("url"):
                    raw_url = rec["url"]
                    display_url = (raw_url[:40] + '...') if len(raw_url) > 40 else raw_url
                    url_row = ctk.CTkFrame(info_row, fg_color="transparent")
                    url_row.pack(side="left", padx=(0, 12))
                    ctk.CTkLabel(url_row, text=f"URL: {display_url}",
                                 font=("Segoe UI", 11), text_color="#888888"
                                 ).pack(side="left", padx=(0, 4))

                    def _open_url(u=raw_url) -> None:
                        """
                        Open the url dialog.
                        Открыть диалог url.
                        Відкрити діалог url.
                        """
                        import webbrowser
                        url = u if u.startswith(("http://", "https://")) else f"https://{u}"
                        try:
                            webbrowser.open(url)
                        except (OSError, ValueError, TypeError, AttributeError, RuntimeError, tk.TclError) as e:
                            logger.debug(f"URL open error: {e}")

                    ctk.CTkButton(url_row, text=L.get("icon_sync", ""),
                                  width=22, height=22, font=("Segoe UI", 11),
                                  fg_color="transparent", hover_color="#2a5a2a",
                                  text_color="#4a9a4a", corner_radius=4,
                                  command=_open_url).pack(side="left")

                if rec.get("username"):
                    ctk.CTkLabel(info_row, text=f"Login: {rec['username'][:30]}", font=("Segoe UI", 11),
                                text_color="#888888").pack(side="left", padx=(0, 12))

                if rec.get("email"):
                    raw_email = rec["email"]
                    display_email = (raw_email[:30] + '...') if len(raw_email) > 30 else raw_email
                    ctk.CTkLabel(info_row, text=f"Email: {display_email}", font=("Segoe UI", 11),
                                text_color="#888888").pack(side="left", padx=(0, 12))

                # Custom fields preview
                try:
                    import json
                    _cf = json.loads(rec.get("custom_fields", "[]") or "[]")
                except (json.JSONDecodeError, TypeError):
                    _cf = []
                if _cf:
                    cf_row = ctk.CTkFrame(ext_info_frame, fg_color="transparent")
                    cf_row.pack(anchor="w", fill="x", pady=(2, 0))
                    for _f in _cf:
                        _fn = str(_f.get("name", "")).strip()
                        _fv = str(_f.get("value", ""))
                        if not _fn:
                            continue
                        _disp = ("●" * min(len(_fv), 8)
                                 if _f.get("hidden")
                                 else (_fv[:22] + "…" if len(_fv) > 22 else _fv))
                        ctk.CTkLabel(cf_row,
                                     text=f"{L.get('icon_field', '')} {_fn}: {_disp}",
                                     font=("Segoe UI", 11),
                                     text_color="#9b8ec4").pack(side="left", padx=(0, 12))

                # Tags display
                try:
                    import json
                    _tags = json.loads(rec.get("tags", "[]") or "[]")
                except (json.JSONDecodeError, TypeError):
                    _tags = []
                if _tags:
                    tags_row = ctk.CTkFrame(ext_info_frame, fg_color="transparent")
                    tags_row.pack(anchor="w", fill="x", pady=(2, 0))
                    for _t in _tags:
                        ctk.CTkLabel(tags_row,
                                     text=f"{L.get('icon_tag', '')} {_t}",
                                     font=("Segoe UI", 10),
                                     fg_color="#2d4a2d",
                                     text_color="#7ec87e",
                                     corner_radius=4).pack(side="left", padx=(0, 4))

                btn_frame = ctk.CTkFrame(card, fg_color="transparent")
                btn_frame.grid(row=0, column=1, sticky="e", padx=10, pady=5)

                def make_copy(p=rec["password"], _btn_ref=[None]) -> None:
                    """
                    Handle make copy.
                    Обработать make copy.
                    Обробити make copy.
                    """
                    try:
                        self.clipboard_clear()
                        self.clipboard_append(p)
                        self.update()
                        _flash_btn(_btn_ref[0], L.get("db_copy", "Copy"))
                    except (tk.TclError, OSError):
                        pass

                def make_delete(rid=rec["id"]) -> None:
                    """
                    Handle make delete.
                    Обработать make delete.
                    Обробити make delete.
                    """
                    from storage.database import PasswordDB
                    msg = L.get("trash_confirm",
                                "Move to Trash? / В корзину? / До кошика?")
                    if CTkMessageBox.question(self.db_window, L.get("db_title", "Password Vault"), msg):
                        try:
                            PasswordDB.soft_delete(rid)
                            self._refresh_db_window()
                        except sqlite3.Error:
                            pass

                def make_duplicate(r=rec) -> None:
                    """
                    Handle make duplicate.
                    Обработать make duplicate.
                    Обробити make duplicate.
                    """
                    self._duplicate_entry(r)

                def make_edit(r=rec) -> None:
                    """
                    Handle make edit.
                    Обработать make edit.
                    Обробити make edit.
                    """
                    self._open_edit_dialog(r)

                def make_copy_url(u=rec.get("url", "")) -> None:
                    """
                    Handle make copy url.
                    Обработать make copy url.
                    Обробити make copy url.
                    """
                    if not u:
                        CTkMessageBox.info(self.db_window,
                            L.get("db_title", "Password Vault"),
                            L.get("db_no_url", "URL not set / URL не задан / URL не вказано"))
                        return
                    try:
                        self.clipboard_clear()
                        self.clipboard_append(u)
                        self.update()
                        _flash_btn(_url_btn_ref[0], L.get("db_copy_url", "Copy URL"))
                    except (tk.TclError, OSError):
                        pass

                def make_copy_username(u=rec.get("username", "") or rec.get("email", "")) -> None:
                    """
                    Handle make copy username.
                    Обработать make copy username.
                    Обробити make copy username.
                    """
                    if not u:
                        CTkMessageBox.info(self.db_window,
                            L.get("db_title", "Password Vault"),
                            L.get("db_no_username", "Username not set / Логин не задан / Логін не вказано"))
                        return
                    try:
                        self.clipboard_clear()
                        self.clipboard_append(u)
                        self.update()
                        _flash_btn(_login_btn_ref[0], L.get("db_copy_username", "Copy Login"))
                    except (tk.TclError, OSError):
                        pass

                def make_autotype(p=rec["password"]) -> None:
                    """
                    Handle make autotype.
                    Обработать make autotype.
                    Обробити make autotype.
                    """
                    try:
                        from utils.autotype import AutoType
                        self.db_window.withdraw()
                        import time
                        time.sleep(0.4)
                        ok = AutoType.clipboard_paste(p, clear_after=15, do_paste=True)
                        self.db_window.deiconify()
                        if not ok:
                            CTkMessageBox.warning(self.db_window,
                                L.get("autotype_title", "Auto-Type"),
                                L.get("autotype_fail", "Auto-type error / Ошибка автовставки / Помилка автовведення"))
                    except ImportError:
                        CTkMessageBox.warning(self.db_window,
                            L.get("autotype_title", "Auto-Type"),
                            L.get("autotype_no_support", "Auto-type not available on this system"))
                    except (tk.TclError, OSError, RuntimeError) as e:
                        logger.error(f"Auto-type error: {e}")

                btn_w = 135
                btn_h = 34
                btn_font = ("Segoe UI", 11, "bold")

                def _flash_btn(btn, orig_text: str, ok_text: str = None) -> None:
                    """
                    Handle flash btn.
                    Обработать flash btn.
                    Обробити flash btn.
                    """
                    if btn is None:
                        return
                    ok = ok_text or L.get("copied_ok", "Copied!")
                    try:
                        btn.configure(text=ok, fg_color="#0a5a0a")
                        btn.after(1200, lambda: _restore_btn(btn, orig_text))
                    except tk.TclError:
                        pass

                def _restore_btn(btn, orig_text: str) -> None:
                    """
                    Handle restore btn.
                    Обработать restore btn.
                    Обробити restore btn.
                    """
                    try:
                        btn.configure(text=orig_text, fg_color="#107c10")
                    except tk.TclError:
                        pass

                actions_row = ctk.CTkFrame(btn_frame, fg_color="transparent")
                actions_row.pack(fill="x")

                _btn_ref = [None]
                _copy_btn = ctk.CTkButton(
                    actions_row, text=L.get("db_copy", "Copy / Копировать / Копіювати"),
                    width=btn_w, height=btn_h, font=btn_font, fg_color="#107c10",
                    hover_color="#159e15", text_color="white", corner_radius=radius, command=make_copy
                )
                _copy_btn.pack(side="left", padx=(0, 6))
                _btn_ref[0] = _copy_btn

                ctk.CTkButton(
                    actions_row, text=L.get("db_edit", "Edit / Изменить / Редагувати"),
                    width=btn_w, height=btn_h, font=btn_font, fg_color="#0078d4",
                    hover_color="#1a92ec", text_color="white", corner_radius=radius, command=make_edit
                ).pack(side="left", padx=(0, 6))

                ctk.CTkButton(
                    actions_row, text=L.get("db_delete", "Trash / В корзину / До кошика"),
                    width=btn_w, height=btn_h, font=btn_font, fg_color="#8b0000",
                    hover_color="#b30000", text_color="white", corner_radius=radius, command=make_delete
                ).pack(side="left", padx=(0, 6))

                ctk.CTkButton(
                    actions_row, text=L.get("db_duplicate", "⧉ Copy entry / Дубль / Дублювати"),
                    width=btn_w, height=btn_h, font=btn_font, fg_color="#4a4a6a",
                    hover_color="#6060a0", text_color="white", corner_radius=radius,
                    command=make_duplicate
                ).pack(side="left", padx=(0, 6))

                # Extra action buttons (new row)
                if rec.get("url") or rec.get("username") or rec.get("email"):
                    extra_row = ctk.CTkFrame(btn_frame, fg_color="transparent")
                    extra_row.pack(fill="x", pady=(4, 0))

                    _url_btn_ref = [None]
                    _login_btn_ref = [None]

                    if rec.get("url"):
                        _ub = ctk.CTkButton(
                            extra_row,
                            text=L.get("db_copy_url", "Copy URL"),
                            width=btn_w, height=btn_h, font=btn_font,
                            fg_color="#5c4a8a", hover_color="#7a61b5",
                            text_color="white", corner_radius=radius,
                            command=make_copy_url
                        )
                        _ub.pack(side="left", padx=(0, 6))
                        _url_btn_ref[0] = _ub

                    if rec.get("username") or rec.get("email"):
                        _lb = ctk.CTkButton(
                            extra_row,
                            text=L.get("db_copy_username", "Copy Login"),
                            width=btn_w, height=btn_h, font=btn_font,
                            fg_color="#2d6a8a", hover_color="#3a86b0",
                            text_color="white", corner_radius=radius,
                            command=make_copy_username
                        )
                        _lb.pack(side="left", padx=(0, 6))
                        _login_btn_ref[0] = _lb

                    ctk.CTkButton(
                        extra_row,
                        text=L.get("autotype_btn", "Auto-Type"),
                        width=btn_w, height=btn_h, font=btn_font,
                        fg_color="#1a5c3a", hover_color="#217a4e",
                        text_color="white", corner_radius=radius,
                        command=make_autotype
                    ).pack(side="left")

            except (tk.TclError, KeyError, ValueError) as e:
                logger.error(f"Error rendering record: {e}")
                continue

    def _close_db_window(self) -> None:
        """Close password database window"""
        if self.db_window and self.db_window.winfo_exists():
            try:
                self.db_window.grab_release()
                self.db_window.destroy()
            except tk.TclError:
                pass
            finally:
                self.db_window = None
