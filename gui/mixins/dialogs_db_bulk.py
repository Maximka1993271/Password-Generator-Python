"""
Dialogs mixin - Database window bulk operations
Миксин диалогов - Bulk-операции окна БД
Міксин діалогів - Bulk-операції вікна БД

Содержит методы для массовых операций: select all, delete all, move all, export all.
"""
from __future__ import annotations

import tkinter as tk
import customtkinter as ctk
from utils.logger import get_logger
from gui.dialogs import CTkMessageBox
from Langs.lang import LANGUAGES
from gui.mixins.dialogs_helpers import _get_colors_for_theme

logger = get_logger("dialogs_db_bulk")


class DialogsDBBulkMixin:
    """Bulk operations for database dialog window

    Bulk-операции для окна базы данных
    Bulk-операції для вікна бази даних
    """

    def _bulk_select_all(self) -> None:
        """Show a quick info popup — selection is vault-wide by default."""
        L = LANGUAGES.get(self.current_lang, LANGUAGES.get("EN", LANGUAGES.get("RU")))
        CTkMessageBox.info(
            self.db_window,
            L.get("db_title", "Password Vault"),
            L.get("bulk_select_info",
                  "All records are selected for the chosen action.\n"
                  "Все записи выбраны для выбранного действия.\n"
                  "Усі записи обрані для обраної дії.")
        )

    def _bulk_delete_all(self) -> None:
        """Delete ALL records in vault after double confirmation."""
        from storage.database import PasswordDB
        L = LANGUAGES.get(self.current_lang, LANGUAGES.get("EN", LANGUAGES.get("RU")))

        try:
            records = PasswordDB.get_all()
        except (sqlite3.Error, OSError):
            return
        if not records:
            CTkMessageBox.info(self.db_window,
                               L.get("db_title", "Password Vault"),
                               L.get("db_empty", "Vault is empty / База пуста / База порожня"))
            return

        n = len(records)
        msg = (L.get("bulk_del_all_confirm",
                     "DELETE ALL {n} records? This CANNOT be undone!\n"
                     "Удалить ВСЕ {n} записей? Это НЕЛЬЗЯ отменить!\n"
                     "Видалити ВСІ {n} записів? Це НЕ можна скасувати!")
               .replace("{n}", str(n)))
        if not CTkMessageBox.question(self.db_window,
                                      L.get("db_title", "Password Vault"), msg):
            return
        deleted = 0
        for rec in records:
            try:
                if PasswordDB.delete(rec["id"]):
                    deleted += 1
            except sqlite3.Error as e:
                logger.error(f"Bulk delete error id={rec['id']}: {e}")
        logger.info(f"Bulk deleted {deleted}/{n} records")
        self._refresh_db_window()

    def _bulk_move_all_category(self) -> None:
        """Move ALL records to a chosen category."""
        from storage.database import PasswordDB
        L = LANGUAGES.get(self.current_lang, LANGUAGES.get("EN", LANGUAGES.get("RU")))
        colors = _get_colors_for_theme(self._get_actual_theme())
        radius = self.current_radius

        try:
            records = PasswordDB.get_all()
        except (sqlite3.Error, OSError):
            return
        if not records:
            CTkMessageBox.info(self.db_window,
                               L.get("db_title", "Password Vault"),
                               L.get("db_empty", "Vault is empty / База пуста / База порожня"))
            return

        dlg = ctk.CTkToplevel(self.db_window)
        dlg.title(L.get("bulk_move_title",
                        "Move all to category / Переместить все / Перемістити всі"))
        dlg.geometry("430x220")
        dlg.resizable(False, False)
        dlg.transient(self.db_window)
        dlg.grab_set()
        dlg.protocol("WM_DELETE_WINDOW", lambda: [dlg.grab_release(), dlg.destroy()])
        dlg.lift()
        dlg.focus_force()
        dlg.after(80, lambda: dlg.attributes("-topmost", False) if dlg and dlg.winfo_exists() else None)
        dlg.attributes("-topmost", True)
        dlg.configure(fg_color=colors["bg"])
        try:
            self._center_window_relative_to_parent(dlg, 430, 220)
        except (tk.TclError, AttributeError):
            pass

        ctk.CTkLabel(
            dlg,
            text=(L.get("bulk_move_label",
                        "Set category for ALL {n} records:\n"
                        "Категория для ВСЕХ {n} записей:\n"
                        "Категорія для ВСІХ {n} записів:")
                  .replace("{n}", str(len(records)))),
            font=("Segoe UI", 13), text_color=colors["label_text"],
            wraplength=390, justify="left"
        ).pack(pady=(16, 8), padx=20, anchor="w")

        cat_var = tk.StringVar(value="")
        ctk.CTkEntry(dlg, textvariable=cat_var, width=370, height=34,
                     font=("Segoe UI", 13), fg_color=colors["entry_bg"],
                     text_color=colors["fg"], corner_radius=radius,
                     placeholder_text=L.get("bulk_move_ph",
                                            "Type or pick / Введите / Введіть")
                     ).pack(padx=20)

        existing = PasswordDB.get_categories()
        if existing:
            ctk.CTkOptionMenu(dlg, values=[""] + existing,
                              command=lambda v: cat_var.set(v),
                              width=370, font=("Segoe UI", 12),
                              corner_radius=radius).pack(padx=20, pady=(5, 0))

        def do_move() -> None:
            new_cat = cat_var.get().strip()
            # Validate category name before bulk-updating all selected records
            from core.validators import CategoryValidator, sanitize_text
            _cat_result = CategoryValidator(required=False).validate(new_cat)
            if not _cat_result.valid:
                CTkMessageBox.warning(dlg, L.get("err_title", "Error"),
                                      "\n".join(_cat_result.errors[:2]))
                return
            new_cat = sanitize_text(new_cat, max_len=100)
            moved = 0
            for rec in records:
                try:
                    PasswordDB.update(rec["id"], rec["label"], category=new_cat)
                    moved += 1
                except (sqlite3.Error, TypeError) as e:
                    logger.error(f"Bulk move id={rec['id']}: {e}")
            dlg.destroy()
            logger.info(f"Bulk moved {moved} records → '{new_cat}'")
            self._refresh_db_window()

        br = ctk.CTkFrame(dlg, fg_color="transparent")
        br.pack(pady=12)
        ctk.CTkButton(br, text=L.get("save", "Save / Сохранить / Зберегти"),
                      width=120, height=32, fg_color="#2d6a4f",
                      corner_radius=radius, command=do_move).pack(side="left", padx=6)
        ctk.CTkButton(br, text=L.get("cancel", "Cancel / Отмена / Скасувати"),
                      width=120, height=32, fg_color="#8b0000",
                      corner_radius=radius, command=dlg.destroy).pack(side="left", padx=6)

    def _bulk_export_all(self) -> None:
        """Export ALL records via the existing DataExporter dialog."""
        from storage.database import PasswordDB
        L = LANGUAGES.get(self.current_lang, LANGUAGES.get("EN", LANGUAGES.get("RU")))

        try:
            records = PasswordDB.get_all()
        except (sqlite3.Error, OSError):
            return
        if not records:
            CTkMessageBox.info(self.db_window,
                               L.get("db_title", "Password Vault"),
                               L.get("db_empty", "Vault is empty / База пуста / База порожня"))
            return
        try:
            from utils.export import DataExporter
            DataExporter.show_export_dialog(records, self.db_window, self.current_lang)
        except ImportError as e:
            CTkMessageBox.error(self.db_window, L.get("err_title", "Error"), str(e))
        except (OSError, IOError, sqlite3.Error) as e:
            logger.error(f"Bulk export error: {e}")
            CTkMessageBox.error(self.db_window, L.get("err_title", "Error"), str(e))