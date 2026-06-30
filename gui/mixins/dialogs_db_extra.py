"""
Dialogs mixin - Database window extra features (Trash, Stats, Cloud Sync, Expiry)
Миксин диалогов - Доп. функции окна БД (Корзина, Статистика, Облачная синхронизация, Просрочка)
Міксин діалогів - Дод. функції вікна БД (Кошик, Статистика, Хмарна синхронізація, Прострочення)

Содержит методы для: корзины, статистики, облачной синхронизации, предупреждений о просрочке.
"""
from __future__ import annotations

import os
import json
import tkinter as tk
import customtkinter as ctk
from utils.logger import get_logger
from gui.dialogs import CTkMessageBox
from Langs.lang import LANGUAGES
from utils.helpers import center_window_relative
from gui.mixins.dialogs_helpers import _get_colors_for_theme
from storage.database_db_helpers import _pwd_age_days, _age_badge

logger = get_logger("dialogs_db_extra")


class DialogsDBExtraMixin:
    """Extra features for database dialog window (Trash, Stats, Cloud Sync, Expiry)

    Дополнительные функции для окна базы данных (Корзина, Статистика, Облачная синхронизация, Просрочка)
    Додаткові функції для вікна бази даних (Кошик, Статистика, Хмарна синхронізація, Прострочення)
    """

    # ==================== TRASH ====================

    def _show_trash_dialog(self) -> None:
        """Show Trash dialog: list soft-deleted records, restore or permanently delete."""
        from storage.database import PasswordDB
        L = LANGUAGES.get(self.current_lang, LANGUAGES.get("EN", LANGUAGES.get("RU")))
        colors = _get_colors_for_theme(self._get_actual_theme())
        radius = self.current_radius

        dlg = ctk.CTkToplevel(self.db_window)
        dlg.title(L.get("trash_title", "Trash / Корзина / Кошик"))
        dlg.geometry("700x500")
        dlg.resizable(True, True)
        dlg.transient(self.db_window)
        dlg.grab_set()
        dlg.protocol("WM_DELETE_WINDOW", lambda: [dlg.grab_release(), dlg.destroy()])
        dlg.lift()
        dlg.focus_force()
        dlg.after(80, lambda: dlg.attributes("-topmost", False) if dlg and dlg.winfo_exists() else None)
        dlg.attributes("-topmost", True)
        dlg.configure(fg_color=colors["bg"])
        try:
            self._center_window_relative_to_parent(dlg, 700, 500)
        except (tk.TclError, AttributeError):
            pass

        ctk.CTkLabel(dlg, text=L.get("trash_title", "Trash / Корзина / Кошик"),
                     font=("Segoe UI", 18, "bold"), text_color=colors["label_text"]
                     ).pack(pady=(14, 4))
        ctk.CTkFrame(dlg, height=2, fg_color="#8b0000").pack(fill="x", padx=20, pady=(0, 10))

        top_row = ctk.CTkFrame(dlg, fg_color="transparent")
        top_row.pack(fill="x", padx=20, pady=(0, 8))

        def _empty_trash() -> None:
            """
            Handle empty trash.
            Обработать empty trash.
            Обробити empty trash.
            """
            msg = L.get("trash_empty_confirm",
                        "Permanently delete ALL items in Trash?\n"
                        "Удалить ВСЕ элементы корзины навсегда?\n"
                        "Видалити ВСІ елементи кошика назавжди?")
            try:
                dlg.attributes("-topmost", False)
            except (OSError, ValueError, TypeError, AttributeError, RuntimeError, tk.TclError):
                pass
            answer = CTkMessageBox.question(dlg, L.get("trash_title", "Trash"), msg)
            try:
                if dlg.winfo_exists():
                    dlg.attributes("-topmost", True)
            except (OSError, ValueError, TypeError, AttributeError, RuntimeError, tk.TclError):
                pass
            if answer:
                try:
                    n = PasswordDB.empty_trash()
                    logger.info(f"Emptied trash: {n} records permanently deleted")
                    if dlg.winfo_exists():
                        _refresh()
                except sqlite3.Error as e:
                    if dlg.winfo_exists():
                        CTkMessageBox.error(dlg, L.get("err_title", "Error"), str(e))

        ctk.CTkButton(top_row, text=L.get("trash_empty", "Empty Trash / Очистить / Очистити"),
                      width=200, height=32, fg_color="#8b0000", hover_color="#b30000",
                      corner_radius=radius, font=("Segoe UI", 12, "bold"),
                      command=_empty_trash).pack(side="left")

        count_lbl = ctk.CTkLabel(top_row, text="", font=("Segoe UI", 12), text_color="gray")
        count_lbl.pack(side="right")

        scroll = ctk.CTkScrollableFrame(dlg, fg_color=colors["bg"])
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        def _refresh() -> None:
            """
            Handle refresh.
            Обработать refresh.
            Обробити refresh.
            """
            for w in scroll.winfo_children():
                w.destroy()
            try:
                items = PasswordDB.get_trash()
            except (sqlite3.Error, OSError):
                items = []
            count_lbl.configure(text=f"{len(items)} " + L.get("trash_items", "items / элементов / елементів"))
            if not items:
                ctk.CTkLabel(scroll,
                             text=L.get("trash_empty_label", "Trash is empty / Корзина пуста / Кошик порожній"),
                             font=("Segoe UI", 14), text_color="gray").pack(pady=40)
                return
            for rec in items:
                row = ctk.CTkFrame(scroll, fg_color=colors["card_bg"],
                                   corner_radius=8)
                row.pack(fill="x", pady=4)
                row.columnconfigure(0, weight=1)

                info = ctk.CTkFrame(row, fg_color="transparent")
                info.grid(row=0, column=0, sticky="w", padx=10, pady=6)
                ctk.CTkLabel(info, text=rec.get("label", "—")[:60],
                             font=("Segoe UI", 13, "bold"), text_color=colors["label_text"],
                             anchor="w").pack(anchor="w")
                deleted_at = rec.get("deleted_at", "")[:10]
                ctk.CTkLabel(info, text=f"{L.get('icon_trash', '')} {L.get('trash_deleted', 'Deleted')} {deleted_at}",
                             font=("Segoe UI", 11), text_color="gray", anchor="w").pack(anchor="w")

                btn_f = ctk.CTkFrame(row, fg_color="transparent")
                btn_f.grid(row=0, column=1, sticky="e", padx=10)

                def _restore(rid=rec["id"]) -> None:
                    """
                    Handle restore.
                    Обработать restore.
                    Обробити restore.
                    """
                    try:
                        PasswordDB.restore(rid)
                        _refresh()
                        self._refresh_db_window()
                    except sqlite3.Error as e:
                        CTkMessageBox.error(dlg, L.get("err_title", "Error"), str(e))

                def _perm_delete(rid=rec["id"]) -> None:
                    """
                    Handle perm delete.
                    Обработать perm delete.
                    Обробити perm delete.
                    """
                    try:
                        dlg.attributes("-topmost", False)
                    except (OSError, ValueError, TypeError, AttributeError, RuntimeError, tk.TclError):
                        pass
                    answer = CTkMessageBox.question(dlg, L.get("trash_title", "Trash"),
                                             L.get("trash_perm_del", "Delete permanently? / Удалить навсегда? / Видалити назавжди?"))
                    try:
                        if dlg.winfo_exists():
                            dlg.attributes("-topmost", True)
                    except (OSError, ValueError, TypeError, AttributeError, RuntimeError, tk.TclError):
                        pass
                    if answer:
                        try:
                            PasswordDB.delete(rid)
                            if dlg.winfo_exists():
                                _refresh()
                        except sqlite3.Error as e:
                            if dlg.winfo_exists():
                                CTkMessageBox.error(dlg, L.get("err_title", "Error"), str(e))

                ctk.CTkButton(btn_f, text=L.get("trash_restore", "↩ Restore / Восстановить / Відновити"),
                              width=150, height=30, fg_color="#2d6a4f", hover_color="#3a8a65",
                              corner_radius=radius, font=("Segoe UI", 11),
                              command=_restore).pack(side="left", padx=(0, 6))
                ctk.CTkButton(btn_f, text=L.get("trash_del_perm", "Delete / Удалить / Видалити"),
                              width=120, height=30, fg_color="#8b0000", hover_color="#b30000",
                              corner_radius=radius, font=("Segoe UI", 11),
                              command=_perm_delete).pack(side="left")

        _refresh()

        ctk.CTkButton(dlg, text=L.get("close", "Close / Закрыть / Закрити"),
                      width=120, height=34, fg_color="#ca5010", hover_color="#e05a1a",
                      corner_radius=radius, command=dlg.destroy).pack(pady=(0, 14))

    # ==================== STATS ====================

    def _show_stats_dialog(self) -> None:
        """Show vault statistics screen."""
        from storage.database import PasswordDB
        L = LANGUAGES.get(self.current_lang, LANGUAGES.get("EN", LANGUAGES.get("RU")))
        colors = _get_colors_for_theme(self._get_actual_theme())
        radius = self.current_radius

        try:
            stats = PasswordDB.get_stats()
        except (sqlite3.Error, OSError, AttributeError) as e:
            CTkMessageBox.error(self.db_window, L.get("err_title", "Error"), str(e))
            return

        dlg = ctk.CTkToplevel(self.db_window)
        dlg.title(L.get("stats_title", "Vault Statistics / Статистика / Статистика"))
        dlg.geometry("480x420")
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
            self._center_window_relative_to_parent(dlg, 480, 420)
        except (tk.TclError, AttributeError):
            pass

        ctk.CTkLabel(dlg, text=L.get("stats_title", "Vault Statistics / Статистика / Статистика"),
                     font=("Segoe UI", 18, "bold"), text_color=colors["label_text"]
                     ).pack(pady=(16, 4))
        ctk.CTkFrame(dlg, height=2, fg_color="#1a6b5a").pack(fill="x", padx=20, pady=(0, 16))

        rows = [
            ("", L.get("stats_total",     "Total records / Всего записей / Всього записів"),   stats.get("total", 0),     None),
            ("",  L.get("stats_weak",      "Weak passwords / Слабые пароли / Слабкі паролі"),   stats.get("weak", 0),      "#c8860a"),
            ("", L.get("stats_dupl",      "Duplicate passwords / Дублей / Дублів"),             stats.get("duplicates", 0), "#c8860a"),
            ("", L.get("stats_no_url",    "No URL set / Без URL / Без URL"),                   stats.get("no_url", 0),    None),
            ("", L.get("stats_old_pwd",   "Password ≥ 90 days old / Старше 90д / Старше 90д"), stats.get("old_pwd", 0),   "#c0392b" if stats.get("old_pwd", 0) > 0 else None),
            ("", L.get("stats_in_trash",  "In Trash / В корзине / У кошику"),                  stats.get("in_trash", 0),  None),
            ("", L.get("stats_with_tags", "Records with tags / С тегами / З тегами"),           stats.get("with_tags", 0), None),
        ]

        frame = ctk.CTkFrame(dlg, fg_color="transparent")
        frame.pack(fill="x", padx=30)

        for icon, label, value, warn_color in rows:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", pady=5)
            row.columnconfigure(0, weight=1)

            ctk.CTkLabel(row, text=f"{icon}  {label}",
                         font=("Segoe UI", 13), text_color=colors["label_text"],
                         anchor="w").grid(row=0, column=0, sticky="w")

            color = warn_color if (warn_color and value > 0) else colors.get("label_text", "#ffffff")
            ctk.CTkLabel(row, text=str(value),
                         font=("Segoe UI", 14, "bold"), text_color=color,
                         anchor="e").grid(row=0, column=1, sticky="e")

        # Health bar
        total = stats.get("total", 1) or 1
        weak = stats.get("weak", 0) + stats.get("duplicates", 0) + stats.get("old_pwd", 0)
        health = max(0, min(100, int(100 - (weak / total * 100))))
        bar_color = "#2d6a4f" if health >= 80 else ("#c8860a" if health >= 50 else "#c0392b")

        ctk.CTkFrame(dlg, height=1, fg_color="gray").pack(fill="x", padx=30, pady=(16, 8))
        health_row = ctk.CTkFrame(dlg, fg_color="transparent")
        health_row.pack(fill="x", padx=30)
        ctk.CTkLabel(health_row, text=L.get("stats_health", "Vault health / Здоровье / Здоров'я:"),
                     font=("Segoe UI", 13, "bold")).pack(side="left")
        ctk.CTkLabel(health_row, text=f"{health}%",
                     font=("Segoe UI", 14, "bold"), text_color=bar_color).pack(side="right")

        _bar = ctk.CTkProgressBar(dlg, width=420, height=14,
                                  progress_color=bar_color, corner_radius=7)
        _bar.set(health / 100)
        _bar.pack(padx=30, pady=(4, 16))

        ctk.CTkButton(dlg, text=L.get("close", "Close / Закрыть / Закрити"),
                      width=120, height=34, fg_color="#ca5010", hover_color="#e05a1a",
                      corner_radius=radius, command=dlg.destroy).pack(pady=(0, 16))

    # ==================== CLOUD SYNC ====================

    def _show_cloud_sync_dialog(self) -> None:
        """Show cloud sync dialog / Диалог облачной синхронизации / Діалог хмарної синхронізації"""
        import tkinter as tk
        import customtkinter as ctk
        from utils.helpers import center_window_relative

        lang = getattr(self, 'current_lang', 'RU')

        labels = {
            "RU": {
                "title":    "Облачная синхронизация",
                "note":     "Синхронизируется только зашифрованный файл — ключ остаётся на устройстве",
                "url":      "URL WebDAV сервера:",
                "user":     "Логин:",
                "pwd":      "Пароль:",
                "url_ph":   "https://cloud.example.com/remote.php/dav/files/user/",
                "test":     "Проверить соединение",
                "sync_up":  "Загрузить в облако",
                "sync_dn":  "Скачать из облака",
                "cancel":   "Закрыть",
                "testing":  "Проверка...",
                "ok":       "Соединение успешно!",
                "fail":     "Ошибка соединения",
                "no_cfg":   "Укажите URL, логин и пароль.",
                "uploading":"Загрузка...",
                "uploaded": "База загружена в облако!",
                "downloading":"Скачивание...",
                "downloaded":"База скачана из облака! Перезапустите приложение.",
                "no_lib":   "Библиотека requests не установлена.\npip install requests",
                "err":      "Ошибка",
            },
            "UA": {
                "title":    "Хмарна синхронізація",
                "note":     "Синхронізується лише зашифрований файл — ключ залишається на пристрої",
                "url":      "URL WebDAV сервера:",
                "user":     "Логін:",
                "pwd":      "Пароль:",
                "url_ph":   "https://cloud.example.com/remote.php/dav/files/user/",
                "test":     "Перевірити з'єднання",
                "sync_up":  "Завантажити в хмару",
                "sync_dn":  "Завантажити з хмари",
                "cancel":   "Закрити",
                "testing":  "Перевірка...",
                "ok":       "З'єднання успішне!",
                "fail":     "Помилка з'єднання",
                "no_cfg":   "Вкажіть URL, логін і пароль.",
                "uploading":"Завантаження...",
                "uploaded": "Базу завантажено в хмару!",
                "downloading":"Завантаження...",
                "downloaded":"Базу завантажено з хмари! Перезапустіть додаток.",
                "no_lib":   "Бібліотека requests не встановлена.\npip install requests",
                "err":      "Помилка",
            },
            "EN": {
                "title":    "Cloud Sync",
                "note":     "Only the encrypted file is synced — your key never leaves the device",
                "url":      "WebDAV Server URL:",
                "user":     "Username:",
                "pwd":      "Password:",
                "url_ph":   "https://cloud.example.com/remote.php/dav/files/user/",
                "test":     "Test Connection",
                "sync_up":  "Upload to Cloud",
                "sync_dn":  "Download from Cloud",
                "cancel":   "Close",
                "testing":  "Testing...",
                "ok":       "Connection successful!",
                "fail":     "Connection failed",
                "no_cfg":   "Please fill in URL, username and password.",
                "uploading":"Uploading...",
                "uploaded": "Database uploaded to cloud!",
                "downloading":"Downloading...",
                "downloaded":"Database downloaded! Please restart the app.",
                "no_lib":   "requests library is not installed.\npip install requests",
                "err":      "Error",
            },
        }
        T = labels.get(lang, labels["RU"])

        saved_url, saved_user, saved_pwd = "", "", ""
        try:
            from utils.cloud_sync import load_sync_config
            cfg = load_sync_config() or {}
            saved_url  = cfg.get("url", "")
            saved_user = cfg.get("username", "")
            saved_pwd  = cfg.get("password", "")
        except (ImportError, OSError, ValueError, KeyError):
            pass

        win = ctk.CTkToplevel(self.db_window if hasattr(self, 'db_window') and self.db_window else self)
        win.title(T["title"])
        win.resizable(False, False)
        win.grab_set()
        win.lift()
        win.focus_force()

        w, h = 680, 400
        parent_win = self.db_window if hasattr(self, 'db_window') and self.db_window else self
        center_window_relative(parent_win, win, w, h)

        pad = {"padx": 20, "pady": 6}

        ctk.CTkLabel(win, text=T["note"], font=("Segoe UI", 11),
                     text_color="gray", wraplength=480, justify="left").pack(anchor="w", padx=20, pady=(15, 4))

        ctk.CTkLabel(win, text=T["url"], font=("Segoe UI", 12, "bold"), anchor="w").pack(anchor="w", **pad)
        url_var = tk.StringVar(value=saved_url)
        ctk.CTkEntry(win, textvariable=url_var, height=34, font=("Segoe UI", 12),
                     placeholder_text=T["url_ph"], width=640).pack(padx=20)

        ctk.CTkLabel(win, text=T["user"], font=("Segoe UI", 12, "bold"), anchor="w").pack(anchor="w", **pad)
        user_var = tk.StringVar(value=saved_user)
        ctk.CTkEntry(win, textvariable=user_var, height=34, font=("Segoe UI", 12), width=640).pack(padx=20)

        ctk.CTkLabel(win, text=T["pwd"], font=("Segoe UI", 12, "bold"), anchor="w").pack(anchor="w", **pad)
        pwd_var = tk.StringVar(value=saved_pwd)
        ctk.CTkEntry(win, textvariable=pwd_var, height=34, show="*", font=("Segoe UI", 12), width=640).pack(padx=20)

        status_lbl = ctk.CTkLabel(win, text="", font=("Segoe UI", 12))
        status_lbl.pack(pady=(8, 0))

        def _get_cfg() -> Any:
            """
            Handle get cfg.
            Обработать get cfg.
            Обробити get cfg.
            """
            return {
                "url":      url_var.get().strip(),
                "username": user_var.get().strip(),
                "password": pwd_var.get(),
            }

        def _save_and_get_sync() -> Any:
            """
            Save and get sync.
            Сохранить and get sync.
            Зберегти and get sync.
            """
            cfg = _get_cfg()
            # Validate sync URL before attempting connection
            from core.validators import URLValidator, sanitize_url
            _url_val = URLValidator(required=True, field_name="Server URL")
            _url_r   = _url_val.validate(cfg.get("url",""))
            if not cfg["url"] or not cfg["username"] or not _url_r.valid:
                err = "\n".join(_url_r.errors) if not _url_r.valid else T["no_cfg"]
                status_lbl.configure(text=err[:60], text_color="orange")
                return None
            try:
                from utils.cloud_sync import save_sync_config, create_sync_from_config
                save_sync_config(cfg)
                return create_sync_from_config(cfg)
            except ImportError:
                status_lbl.configure(text=T["no_lib"], text_color="#e04040")
                return None
            except (OSError, ValueError, RuntimeError, AttributeError) as e:
                status_lbl.configure(text=f"[ERR] {e}", text_color="#e04040")
                return None

        def do_test() -> None:
            """
            Handle do test.
            Обработать do test.
            Обробити do test.
            """
            status_lbl.configure(text=T["testing"], text_color="gray")
            win.update()
            sync = _save_and_get_sync()
            if not sync:
                return
            try:
                ok, msg = sync.test_connection()
                status_lbl.configure(
                    text=T["ok"] if ok else f"{T['fail']}: {msg}",
                    text_color="#40b040" if ok else "#e04040")
            except (OSError, ValueError, RuntimeError, AttributeError, ConnectionError) as e:
                status_lbl.configure(text=f"[ERR] {e}", text_color="#e04040")

        def do_upload() -> None:
            """
            Handle do upload.
            Обработать do upload.
            Обробити do upload.
            """
            status_lbl.configure(text=T["uploading"], text_color="gray")
            win.update()
            sync = _save_and_get_sync()
            if not sync:
                return
            try:
                from storage.database import PasswordDB
                db_path = PasswordDB.get_db_path() if hasattr(PasswordDB, 'get_db_path') else None
                if not db_path:
                    db_path = os.path.join(os.path.dirname(os.path.dirname(
                        os.path.abspath(__file__))), "data", "passwords.db")
                ok, msg = sync.upload(db_path)
                status_lbl.configure(
                    text=T["uploaded"] if ok else f"[ERR] {msg}",
                    text_color="#40b040" if ok else "#e04040")
            except (OSError, ValueError, RuntimeError, AttributeError, ConnectionError) as e:
                status_lbl.configure(text=f"[ERR] {e}", text_color="#e04040")

        def do_download() -> None:
            """
            Handle do download.
            Обработать do download.
            Обробити do download.
            """
            status_lbl.configure(text=T["downloading"], text_color="gray")
            win.update()
            sync = _save_and_get_sync()
            if not sync:
                return
            try:
                from storage.database import PasswordDB
                db_path = PasswordDB.get_db_path() if hasattr(PasswordDB, 'get_db_path') else None
                if not db_path:
                    db_path = os.path.join(os.path.dirname(os.path.dirname(
                        os.path.abspath(__file__))), "data", "passwords.db")
                ok, msg = sync.download(db_path)
                status_lbl.configure(
                    text=T["downloaded"] if ok else f"[ERR] {msg}",
                    text_color="#40b040" if ok else "#e04040")
            except (OSError, ValueError, RuntimeError, AttributeError, ConnectionError) as e:
                status_lbl.configure(text=f"[ERR] {e}", text_color="#e04040")

        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(pady=(10, 15))

        ctk.CTkButton(btn_row, text=T["test"], command=do_test,
                      width=150, height=36, fg_color="#1565C0", hover_color="#1976D2",
                      font=("Segoe UI", 12, "bold")).pack(side="left", padx=5)

        ctk.CTkButton(btn_row, text=T["sync_up"], command=do_upload,
                      width=150, height=36, fg_color="#2d6a4f", hover_color="#3a8a65",
                      font=("Segoe UI", 12, "bold")).pack(side="left", padx=5)

        ctk.CTkButton(btn_row, text=T["sync_dn"], command=do_download,
                      width=160, height=36, fg_color="#6a3a2d", hover_color="#8a4a3a",
                      font=("Segoe UI", 12, "bold")).pack(side="left", padx=5)

        ctk.CTkButton(btn_row, text=T["cancel"], command=win.destroy,
                      width=100, height=36, fg_color="#444", hover_color="#555",
                      font=("Segoe UI", 12)).pack(side="left", padx=5)

    # ==================== EXPIRY WARNING ====================

    def _check_expiry_on_open(self) -> None:
        """Show a brief non-blocking warning if passwords are overdue for rotation."""
        try:
            from storage.database import PasswordDB
            L = LANGUAGES.get(self.current_lang, LANGUAGES.get("EN", LANGUAGES.get("RU")))
            records = PasswordDB.get_all()
        except (OSError, ValueError, TypeError, AttributeError, RuntimeError, tk.TclError):
            return

        expired = [r for r in records if _pwd_age_days(r.get("password_changed_at", "")) >= 90]
        critical = [r for r in expired if _pwd_age_days(r.get("password_changed_at", "")) >= 180]

        if not expired:
            return

        colors = _get_colors_for_theme(self._get_actual_theme())
        radius = self.current_radius

        banner = ctk.CTkToplevel(self.db_window)
        banner.title(L.get("expiry_title", "Password Expiry / Срок паролей / Термін паролів"))
        banner.geometry("480x220")
        banner.resizable(False, False)
        banner.transient(self.db_window)
        banner.attributes("-topmost", True)
        banner.configure(fg_color=colors["bg"])
        banner.after(80, lambda: banner.attributes("-topmost", False))
        try:
            self._center_window_relative_to_parent(banner, 480, 220)
        except (OSError, ValueError, TypeError, AttributeError, RuntimeError, tk.TclError):
            pass
        banner.protocol("WM_DELETE_WINDOW", banner.destroy)

        accent = "#c0392b" if critical else "#c8860a"
        ctk.CTkLabel(banner,
                     text=L.get("expiry_title", "Password Expiry / Срок паролей / Термін паролів"),
                     font=("Segoe UI", 15, "bold"), text_color=accent).pack(pady=(14, 4))
        ctk.CTkFrame(banner, height=2, fg_color=accent).pack(fill="x", padx=20, pady=(0, 10))

        n_crit = len(critical)
        n_warn = len(expired) - n_crit
        lines = []
        if n_crit:
            lines.append(L.get("expiry_critical",
                               "{n} passwords not changed for 180+ days!\n{n} паролей не менялись 180+ дней!\n{n} паролів не змінювались 180+ днів!"
                               ).replace("{n}", str(n_crit)))
        if n_warn:
            lines.append(L.get("expiry_warn",
                               "{n} passwords not changed for 90+ days.\n{n} паролей не менялись 90+ дней.\n{n} паролів не змінювались 90+ днів."
                               ).replace("{n}", str(n_warn)))

        ctk.CTkLabel(banner, text="\n".join(lines),
                     font=("Segoe UI", 12), text_color=colors["label_text"],
                     wraplength=440, justify="left").pack(padx=20, pady=(0, 8))

        btn_row = ctk.CTkFrame(banner, fg_color="transparent")
        btn_row.pack(pady=(0, 14))
        ctk.CTkButton(btn_row,
                      text=L.get("expiry_view", "View / Посмотреть / Переглянути"),
                      width=120, height=32, fg_color="#2d6a4f", corner_radius=radius,
                      command=lambda: [banner.destroy(), self._filter_expired()]).pack(side="left", padx=6)
        ctk.CTkButton(btn_row,
                      text=L.get("close", "Close / Закрыть / Закрити"),
                      width=100, height=32, fg_color="#555555", corner_radius=radius,
                      command=banner.destroy).pack(side="left", padx=6)
