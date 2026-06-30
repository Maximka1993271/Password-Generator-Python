"""
Updater mixin for SecurePassPro

Миксин обновления для SecurePassPro
Міксин оновлення для SecurePassPro

FIXED #EX: Replaced broad Exception with specific exceptions
Исправлено #EX: Заменены общие Exception на конкретные исключения
Виправлено #EX: Замінено загальні Exception на конкретні винятки
"""
from __future__ import annotations
import threading
import tkinter as tk
from typing import Optional, Any
from utils.updater import check_for_updates, perform_update, rollback_update, get_current_version, get_update_status
from gui.dialogs import CTkMessageBox
from Langs.lang import LANGUAGES
from utils.logger import get_logger

logger = get_logger("updater_mixin")


class UpdaterMixin:
    """Mixin class for update checking functionality
    Класс-миксин для функциональности проверки обновлений
    Клас-міксин для функціональності перевірки оновлень"""

    def _check_for_updates(self) -> None:
        """Check for updates (asynchronously) with progress dialog
        Проверить наличие обновлений (асинхронно) с диалогом прогресса
        Перевірити наявність оновлень (асинхронно) з діалогом прогресу"""
        L = LANGUAGES[self.current_lang]

        # Store button state for restoration / Сохраняем состояние кнопки для восстановления / Зберігаємо стан кнопки для відновлення
        old_text = ""
        if hasattr(self, 'btn_upd') and self.btn_upd:
            try:
                old_text = self.btn_upd.cget("text")
                self.btn_upd.configure(state="disabled", text=L.get("hibp_checking", "Checking... / Проверка... / Перевірка..."))
            except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
                logger.debug(f"Button configure error / Ошибка настройки кнопки / Помилка налаштування кнопки: {e}")

        # Show progress dialog / Показываем диалог прогресса / Показуємо діалог прогресу
        progress_window = None
        try:
            import customtkinter as ctk
            progress_window = ctk.CTkToplevel(self)
            progress_window.title(L.get("update_check", "Check for updates / Проверка обновлений / Перевірка оновлень"))
            progress_window.geometry("350x150")
            progress_window.resizable(False, False)
            progress_window.transient(self)
            progress_window.grab_set()
            progress_window.attributes("-topmost", True)

            # Center window / Центрируем окно / Центруємо вікно
            self._center_window_relative_to_parent(progress_window, 350, 150)

            main_frame = ctk.CTkFrame(progress_window, fg_color="transparent")
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            ctk.CTkLabel(
                main_frame,
                text=L.get("update_check", "Check for updates / Проверка обновлений / Перевірка оновлень"),
                font=("Segoe UI", 14, "bold")
            ).pack(pady=(0, 10))

            progress_bar = ctk.CTkProgressBar(main_frame, width=280)
            progress_bar.pack(pady=10)
            progress_bar.set(0)

            status_label = ctk.CTkLabel(main_frame, text=L.get("please_wait", "Please wait... / Пожалуйста, подождите... / Будь ласка, зачекайте..."), font=("Segoe UI", 11))
            status_label.pack()

            def animate_progress(i=0) -> None:
                """
                Handle animate progress.
                Обработать animate progress.
                Обробити animate progress.
                """
                if progress_window and progress_window.winfo_exists():
                    if i <= 90:
                        try:
                            progress_bar.set(i / 100)
                            progress_window.after(30, lambda: animate_progress(i + 2))
                        except (tk.TclError, AttributeError, RuntimeError) as e:
                            pass

            animate_progress()
        except (ImportError, AttributeError, RuntimeError, tk.TclError) as e:
            logger.debug(f"Progress window creation error / Ошибка создания окна прогресса / Помилка створення вікна прогресу: {e}")
            progress_window = None

        def _worker() -> None:
            """
            Handle worker.
            Обработать worker.
            Обробити worker.
            """
            release = None
            try:
                release = check_for_updates(self)
                self.after(0, lambda: self._on_update_check_result(release, progress_window))
            except (ImportError, AttributeError, RuntimeError, OSError) as e:
                logger.error(f"Update check error / Ошибка проверки обновлений / Помилка перевірки оновлень: {e}")
                self.after(0, lambda: self._on_update_check_result(None, progress_window))
            finally:
                self.after(0, lambda: self._restore_update_button(old_text))

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def _on_update_check_result(self, release, progress_window: Optional[Any] = None) -> None:
        """Process update check result with progress window cleanup
        Обработать результат проверки обновлений с очисткой окна прогресса
        Обробити результат перевірки оновлень з очищенням вікна прогресу"""
        # Close progress window / Закрываем окно прогресса / Закриваємо вікно прогресу
        if progress_window and progress_window.winfo_exists():
            try:
                progress_window.destroy()
            except (tk.TclError, AttributeError, RuntimeError) as _:
                pass

        L = LANGUAGES[self.current_lang]

        if release is None:
            CTkMessageBox.info(
                self,
                L.get("update_check", "Check for updates / Проверка обновлений / Перевірка оновлень"),
                L.get("update_not_available", "No updates available.\n\nYou are running the latest version. / Обновления не найдены.\n\nУ вас установлена последняя версия. / Оновлень не знайдено.\n\nУ вас встановлена остання версія.")
            )
        else:
            # Format update message with details / Форматируем сообщение об обновлении с деталями / Форматуємо повідомлення про оновлення з деталями
            message = L.get("update_available", "New version {0} available / Доступна новая версия {0} / Доступна нова версія {0}").format(release.version)
            message += f"\n\nDate / Дата: {release.published_at[:10]}"
            message += f"\nSize / Размер: {release.size // 1024 // 1024} MB"

            if CTkMessageBox.question(
                self,
                L.get("update_available_title", "Update available / Доступно обновление / Доступне оновлення"),
                message + "\n\n" + L.get("update_confirm_message", "Install now? / Установить сейчас? / Встановити зараз?")
            ):
                self._perform_update_with_progress(release)

    def _restore_update_button(self, old_text: str = "") -> None:
        """Restore update button / Восстановить кнопку обновления / Відновити кнопку оновлення"""
        if hasattr(self, 'btn_upd') and self.btn_upd:
            try:
                L = LANGUAGES[self.current_lang]
                button_text = old_text if old_text else L.get("btn_upd", "Update / Обновить / Оновити")
                self.btn_upd.configure(state="normal", text=button_text)
            except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
                logger.debug(f"Button restore error / Ошибка восстановления кнопки / Помилка відновлення кнопки: {e}")

    def _perform_update_with_progress(self, release) -> None:
        """Perform update with progress dialog and cancel support
        Выполнить обновление с диалогом прогресса и поддержкой отмены
        Виконати оновлення з діалогом прогресу та підтримкою скасування"""
        L = LANGUAGES[self.current_lang]

        # Create progress window with cancel button
        progress_window = None
        cancel_requested = False
        update_thread = None

        try:
            import customtkinter as ctk

            progress_window = ctk.CTkToplevel(self)
            progress_window.title(L.get("update_confirm_title", "Update / Обновление / Оновлення"))
            progress_window.geometry("450x250")
            progress_window.resizable(False, False)
            progress_window.transient(self)
            progress_window.grab_set()
            progress_window.attributes("-topmost", True)

            # Center window / Центрируем окно / Центруємо вікно
            self._center_window_relative_to_parent(progress_window, 450, 250)

            main_frame = ctk.CTkFrame(progress_window, fg_color="transparent")
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            ctk.CTkLabel(
                main_frame,
                text=L.get("download_start", "Downloading update... / Загрузка обновления... / Завантаження оновлення..."),
                font=("Segoe UI", 14, "bold")
            ).pack(pady=(0, 10))

            progress_bar = ctk.CTkProgressBar(main_frame, width=350)
            progress_bar.pack(pady=10)
            progress_bar.set(0)

            status_label = ctk.CTkLabel(main_frame, text="0%", font=("Segoe UI", 11))
            status_label.pack(pady=(0, 10))

            # Cancel button / Кнопка отмены / Кнопка скасування
            cancel_btn = ctk.CTkButton(
                main_frame,
                text=L.get("cancel", "Cancel / Отмена / Скасувати"),
                width=120,
                height=35,
                fg_color="#8b0000",
                hover_color="#cc0000",
                state="normal"
            )
            cancel_btn.pack(pady=10)

            def on_cancel() -> None:
                """
                Handle the cancel event.
                Обработчик события cancel.
                Обробник події cancel.
                """
                nonlocal cancel_requested
                cancel_requested = True
                try:
                    cancel_btn.configure(state="disabled", text=L.get("please_wait", "Cancelling... / Отмена... / Скасування..."))
                except (tk.TclError, AttributeError, RuntimeError) as _:
                    pass

            cancel_btn.configure(command=on_cancel)

            def update_progress(progress: float) -> None:
                """
                Update progress in the UI.
                Обновить progress в UI.
                Оновити progress в UI.
                """
                if progress_window and progress_window.winfo_exists() and not cancel_requested:
                    try:
                        progress_bar.set(progress)
                        percent = int(progress * 100)
                        status_label.configure(text=f"{percent}%")
                        progress_window.update_idletasks()
                    except (tk.TclError, AttributeError, RuntimeError) as _:
                        pass

            def update_status(message: str) -> None:
                """
                Update status in the UI.
                Обновить status в UI.
                Оновити status в UI.
                """
                if progress_window and progress_window.winfo_exists() and not cancel_requested:
                    try:
                        status_label.configure(text=message)
                        progress_window.update_idletasks()
                    except (tk.TclError, AttributeError, RuntimeError) as _:
                        pass

            def _do_update() -> None:
                """
                Handle do update.
                Обработать do update.
                Обробити do update.
                """
                try:
                    update_status(L.get("download_start", "Downloading update... / Загрузка обновления... / Завантаження оновлення..."))
                    from utils.updater import SecureUpdater
                    updater = SecureUpdater(self, progress_callback=update_progress)

                    # Check if cancelled / Проверяем отмену / Перевіряємо скасування
                    if cancel_requested:
                        update_status(L.get("update_cancelled", "Update cancelled / Обновление отменено / Оновлення скасовано"))
                        if progress_window and progress_window.winfo_exists():
                            progress_window.after(1000, lambda: progress_window.destroy() if progress_window and progress_window.winfo_exists() else None)
                        return

                    status, update_path = updater.download_update(release)

                    # Check if cancelled during download / Проверяем отмену во время загрузки / Перевіряємо скасування під час завантаження
                    if cancel_requested:
                        update_status(L.get("update_cancelled", "Update cancelled / Обновление отменено / Оновлення скасовано"))
                        if progress_window and progress_window.winfo_exists():
                            progress_window.after(1000, lambda: progress_window.destroy() if progress_window and progress_window.winfo_exists() else None)
                        return

                    if status.value != "success" or not update_path:
                        error_msg = L.get("update_error", "Update error / Ошибка обновления / Помилка оновлення")
                        self.after(0, lambda: CTkMessageBox.error(self, L.get("err_title", "Error / Ошибка / Помилка"), error_msg))
                        if progress_window and progress_window.winfo_exists():
                            self.after(0, lambda: progress_window.destroy() if progress_window and progress_window.winfo_exists() else None)
                        return

                    update_status(L.get("update_installing", "Installing update... / Установка обновления... / Встановлення оновлення..."))
                    progress_bar.set(0.95)

                    install_result = updater.install_update(update_path)

                    if install_result.value == "success":
                        update_status(L.get("update_restart", "Update installed, restarting... / Обновление установлено, перезапуск... / Оновлення встановлено, перезапуск..."))
                        progress_bar.set(1.0)
                        if progress_window and progress_window.winfo_exists():
                            progress_window.after(2000, lambda: progress_window.destroy() if progress_window and progress_window.winfo_exists() else None)
                    elif install_result.value == "rollback_success":
                        update_status(L.get("update_rollback", "Rollback performed / Выполнен откат / Виконано відкат"))
                        self.after(2000, lambda: CTkMessageBox.warning(self, L.get("update_title", "Update / Обновление / Оновлення"), L.get("update_rollback_message", "Installation failed, rolled back to previous version / Установка не удалась, выполнен откат к предыдущей версии / Встановлення не вдалося, виконано відкат до попередньої версії")))
                        if progress_window and progress_window.winfo_exists():
                            progress_window.after(3000, lambda: progress_window.destroy() if progress_window and progress_window.winfo_exists() else None)
                    else:
                        error_msg = L.get("update_error", "Update installation error / Ошибка установки обновления / Помилка встановлення оновлення")
                        self.after(0, lambda: CTkMessageBox.error(self, L.get("err_title", "Error / Ошибка / Помилка"), error_msg))
                        if progress_window and progress_window.winfo_exists():
                            progress_window.after(2000, lambda: progress_window.destroy() if progress_window and progress_window.winfo_exists() else None)

                except (ImportError, AttributeError, RuntimeError, OSError) as e:
                    logger.error(f"Update error / Ошибка обновления / Помилка оновлення: {e}")
                    self.after(0, lambda e=e: CTkMessageBox.error(self, L.get("err_title", "Error / Ошибка / Помилка"), f"Failed to install update / Ошибка установки обновления / Помилка встановлення оновлення: {e}"))
                    if progress_window and progress_window.winfo_exists():
                        progress_window.after(2000, lambda: progress_window.destroy() if progress_window and progress_window.winfo_exists() else None)

            update_thread = threading.Thread(target=_do_update, daemon=True)
            update_thread.start()

            # Monitor thread completion / Мониторим завершение потока / Моніторимо завершення потоку
            def check_thread() -> bool:
                """
                Check thread.
                Проверить thread.
                Перевірити thread.
                """
                if not update_thread.is_alive():
                    if progress_window and progress_window.winfo_exists():
                        try:
                            progress_window.destroy()
                        except (tk.TclError, AttributeError, RuntimeError) as _:
                            pass
                    return
                if progress_window and progress_window.winfo_exists() and not cancel_requested:
                    progress_window.after(500, check_thread)

            if progress_window and progress_window.winfo_exists():
                progress_window.after(500, check_thread)

        except (ImportError, AttributeError, RuntimeError, tk.TclError) as e:
            logger.error(f"Progress dialog error / Ошибка диалога прогресса / Помилка діалогу прогресу: {e}")
            # Fallback to simple update without progress dialog
            self._perform_update()

    def _perform_update(self) -> None:
        """Perform program update (simple version without progress)
        Выполнить обновление программы (простая версия без прогресса)
        Виконати оновлення програми (проста версія без прогресу)"""
        L = LANGUAGES[self.current_lang]

        # Disable button / Отключаем кнопку / Вимкаємо кнопку
        old_text = ""
        if hasattr(self, 'btn_upd') and self.btn_upd:
            try:
                old_text = self.btn_upd.cget("text")
                self.btn_upd.configure(state="disabled", text=L.get("please_wait", "Please wait... / Пожалуйста, подождите... / Будь ласка, зачекайте..."))
            except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
                logger.debug(f"Button configure error / Ошибка настройки кнопки / Помилка налаштування кнопки: {e}")

        def _worker() -> None:
            """
            Handle worker.
            Обработать worker.
            Обробити worker.
            """
            try:
                success = perform_update(self)

                if not success:
                    self.after(0, lambda: CTkMessageBox.error(
                        self,
                        L.get("err_title", "Error / Ошибка / Помилка"),
                        L.get("update_error", "Failed to install update. / Не удалось установить обновление. / Не вдалося встановити оновлення.")
                    ))
            except (ImportError, AttributeError, RuntimeError, OSError) as e:
                logger.error(f"Update error / Ошибка обновления / Помилка оновлення: {e}")
                self.after(0, lambda e=e: CTkMessageBox.error(
                    self,
                    L.get("err_title", "Error / Ошибка / Помилка"),
                    f"Failed to install update / Ошибка установки обновления / Помилка встановлення оновлення: {e}"
                ))
            finally:
                self.after(0, lambda: self._restore_update_button(old_text))

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def _show_rollback_dialog(self) -> None:
        """Show rollback dialog for reverting to previous version
        Показать диалог отката к предыдущей версии
        Показати діалог відкату до попередньої версії"""
        L = LANGUAGES[self.current_lang]

        try:
            status = get_update_status()
        except (ImportError, AttributeError, RuntimeError) as e:
            logger.error(f"Failed to get update status / Ошибка получения статуса обновления / Помилка отримання статусу оновлення: {e}")
            status = {"has_backups": False}

        if not status.get("has_backups", False):
            CTkMessageBox.info(
                self,
                L.get("update_rollback", "Rollback / Откат / Відкат"),
                L.get("update_no_backup", "No saved backups for rollback. / Нет сохранённых резервных копий для отката. / Немає збережених резервних копій для відкату.")
            )
            return

        if CTkMessageBox.question(
            self,
            L.get("update_rollback", "Rollback / Откат / Відкат"),
            L.get("update_rollback_confirm", "Are you sure you want to rollback to the previous version?\n\nAny unsaved changes will be lost. / Вы уверены, что хотите откатиться к предыдущей версии?\n\nЛюбые несохранённые изменения будут потеряны. / Ви впевнені, що хочете відкотитися до попередньої версії?\n\nБудь-які незбережені зміни будуть втрачені.")
        ):
            self._perform_rollback()

    def _perform_rollback(self) -> None:
        """Perform rollback to previous version with progress dialog
        Выполнить откат к предыдущей версии с диалогом прогресса
        Виконати відкат до попередньої версії з діалогом прогресу"""
        L = LANGUAGES[self.current_lang]

        # Create progress window / Создаём окно прогресса / Створюємо вікно прогресу
        progress_window = None
        try:
            import customtkinter as ctk

            progress_window = ctk.CTkToplevel(self)
            progress_window.title(L.get("update_rollback", "Rollback / Откат / Відкат"))
            progress_window.geometry("350x150")
            progress_window.resizable(False, False)
            progress_window.transient(self)
            progress_window.grab_set()
            progress_window.attributes("-topmost", True)

            self._center_window_relative_to_parent(progress_window, 350, 150)

            main_frame = ctk.CTkFrame(progress_window, fg_color="transparent")
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            ctk.CTkLabel(
                main_frame,
                text=L.get("update_rollback", "Rollback to previous version... / Откат к предыдущей версии... / Відкат до попередньої версії..."),
                font=("Segoe UI", 14, "bold")
            ).pack(pady=(0, 10))

            progress_bar = ctk.CTkProgressBar(main_frame, width=280)
            progress_bar.pack(pady=10)
            progress_bar.set(0)

            status_label = ctk.CTkLabel(main_frame, text=L.get("please_wait", "Please wait... / Пожалуйста, подождите... / Будь ласка, зачекайте..."), font=("Segoe UI", 11))
            status_label.pack()

            progress_bar.set(0.5)

        except (ImportError, AttributeError, RuntimeError, tk.TclError) as e:
            logger.debug(f"Rollback progress window error / Ошибка окна прогресса отката / Помилка вікна прогресу відкату: {e}")
            progress_window = None

        def _worker() -> None:
            """
            Handle worker.
            Обработать worker.
            Обробити worker.
            """
            try:
                success = rollback_update(self)

                if success:
                    self.after(0, lambda: CTkMessageBox.info(
                        self,
                        L.get("update_rollback", "Rollback / Откат / Відкат"),
                        L.get("update_rollback_success", "Rollback completed successfully.\n\nThe application will restart. / Откат выполнен успешно.\n\nПриложение будет перезапущено. / Відкат виконано успішно.\n\nДодаток буде перезапущено.")
                    ))
                else:
                    self.after(0, lambda: CTkMessageBox.error(
                        self,
                        L.get("err_title", "Error / Ошибка / Помилка"),
                        L.get("update_rollback_error", "Failed to rollback. / Не удалось выполнить откат. / Не вдалося виконати відкат.")
                    ))
            except (ImportError, AttributeError, RuntimeError, OSError) as e:
                logger.error(f"Rollback error / Ошибка отката / Помилка відкату: {e}")
                self.after(0, lambda e=e: CTkMessageBox.error(
                    self,
                    L.get("err_title", "Error / Ошибка / Помилка"),
                    f"Failed to rollback / Ошибка отката / Помилка відкату: {e}"
                ))
            finally:
                if progress_window and progress_window.winfo_exists():
                    self.after(500, lambda: progress_window.destroy() if progress_window and progress_window.winfo_exists() else None)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
