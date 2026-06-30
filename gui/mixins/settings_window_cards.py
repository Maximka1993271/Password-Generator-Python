"""
Settings window mixin - Settings cards and search
Миксин окна настроек - Карточки настроек и поиск
Міксин вікна налаштувань - Картки налаштувань та пошук

100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, List, Optional
from utils.logger import get_logger
from Langs.lang import LANGUAGES

logger = get_logger("settings_window")


class SettingsWindowCardsMixin:
    """Settings cards creation and management

    Создание карточек настроек и управление ими
    Створення карток налаштувань та керування ними
    """

    def _add_settings_card(self, parent, title_key: str, description: str) -> Any:
        """
        Add a settings card to the window

        Добавляет карточку настроек в окно
        Додає картку налаштувань у вікно
        """
        L = LANGUAGES[self.current_lang]
        actual_theme = self._get_actual_theme()
        is_dark = actual_theme == "dark"

        if is_dark:
            bg_card = "#2d2d2d"
            text_primary = "#ffffff"
            text_secondary = "#a0a0a0"
            border_color = "#3d3d3d"
        else:
            bg_card = "#ffffff"
            text_primary = "#202020"
            text_secondary = "#606060"
            border_color = "#e0e0e0"

        card = ctk.CTkFrame(parent, fg_color=bg_card, corner_radius=12, border_width=1, border_color=border_color)
        card.pack(fill="x", pady=10)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=20, pady=15)

        title_frame = ctk.CTkFrame(content, fg_color="transparent")
        title_frame.pack(fill="x")

        title_label = ctk.CTkLabel(title_frame, text=L.get(title_key, title_key), font=("Segoe UI", 16, "bold"),
                                  text_color=text_primary)
        title_label.pack(anchor="w")

        description_label = ctk.CTkLabel(content, text=description, font=("Segoe UI", 11),
                                         text_color=text_secondary)
        description_label.pack(anchor="w", pady=(5, 10))

        if not hasattr(self, "settings_cards"):
            self.settings_cards = []
        self.settings_cards.append({
            "parent": parent,
            "card": card,
            "title_key": title_key,
            "description": description,
            "title_label": title_label,
            "description_label": description_label,
        })

        return content

    def _get_settings_section_widgets(self, card_info: dict) -> list:
        """
        Get all widgets in a settings section

        Получает все виджеты в секции настроек
        Отримує всі віджети в секції налаштувань
        """
        parent = card_info.get("parent")
        card = card_info.get("card")
        if not parent or not card:
            return []

        try:
            siblings = list(parent.winfo_children())
            start_index = siblings.index(card)
        except (ValueError, tk.TclError, AttributeError, RuntimeError) as _:
            return [card]

        widgets = [card]
        known_cards = {
            info.get("card")
            for info in getattr(self, "settings_cards", [])
            if info.get("parent") is parent and info.get("card") is not card
        }

        for widget in siblings[start_index + 1:]:
            if widget in known_cards:
                break
            widgets.append(widget)
        return widgets

    def _pack_settings_widget(self, widget) -> None:
        """
        Pack a settings widget

        Упаковывает виджет настроек
        Пакує віджет налаштувань
        """
        try:
            if widget.winfo_ismapped():
                return
            pack_options = getattr(self, "_settings_pack_options", {}).get(widget)
            if pack_options:
                widget.pack(**pack_options)
            else:
                widget.pack(fill="x", pady=10)
        except (tk.TclError, AttributeError, RuntimeError) as _:
            pass

    def _hide_settings_widget(self, widget) -> None:
        """
        Hide a settings widget

        Скрывает виджет настроек
        Ховає віджет налаштувань
        """
        try:
            if not hasattr(self, "_settings_pack_options"):
                self._settings_pack_options = {}
            if widget.winfo_ismapped() and widget not in self._settings_pack_options:
                self._settings_pack_options[widget] = widget.pack_info()
            widget.pack_forget()
        except (tk.TclError, AttributeError, RuntimeError) as _:
            pass

    def _show_all_settings_sections(self) -> None:
        """
        Show all settings sections

        Показывает все секции настроек
        Показує всі секції налаштувань
        """
        for card_info in getattr(self, "settings_cards", []):
            for widget in self._get_settings_section_widgets(card_info):
                self._pack_settings_widget(widget)

    def _settings_text_from_widget(self, widget) -> str:
        """
        Extract text from a widget for search

        Извлекает текст из виджета для поиска
        Виймає текст з віджета для пошуку
        """
        parts = []
        try:
            if isinstance(widget, (ctk.CTkLabel, ctk.CTkButton, ctk.CTkEntry)):
                text = widget.cget("text") if not isinstance(widget, ctk.CTkEntry) else widget.cget("placeholder_text")
                if text:
                    parts.append(str(text))
            for child in widget.winfo_children():
                child_text = self._settings_text_from_widget(child)
                if child_text:
                    parts.append(child_text)
        except (tk.TclError, AttributeError, RuntimeError) as _:
            pass
        return " ".join(parts)

    def _settings_search_text(self, card_info: dict) -> str:
        """
        Get searchable text from a settings card

        Получает текст для поиска из карточки настроек
        Отримує текст для пошуку з картки налаштувань
        """
        parts = [card_info.get("title_key", ""), card_info.get("description", "")]
        title_key = card_info.get("title_key")
        if title_key:
            for language in LANGUAGES.values():
                parts.append(language.get(title_key, ""))
        for widget in self._get_settings_section_widgets(card_info):
            parts.append(self._settings_text_from_widget(widget))
        return " ".join(str(part) for part in parts if part).casefold()

    def _filter_settings(self, query: str) -> None:
        """
        Filter settings by search query

        Фильтрует настройки по поисковому запросу
        Фільтрує налаштування за пошуковим запитом
        """
        query = (query or "").strip().casefold()
        cards = getattr(self, "settings_cards", [])

        if not query:
            self._settings_search_active = False
            self._show_all_settings_sections()
            active = getattr(self, "_active_settings_category", "design")
            for key, frame in self.category_frames.items():
                try:
                    frame.pack_forget()
                except (tk.TclError, RuntimeError) as _:
                    pass
            try:
                self.category_frames[active].pack(fill="both", expand=True)
            except (tk.TclError, RuntimeError, KeyError) as _:
                pass
            self._highlight_settings_category(active)
            return

        self._settings_search_active = True
        terms = [term for term in query.split() if term]
        visible_categories = set()

        for card_info in cards:
            section_widgets = self._get_settings_section_widgets(card_info)
            haystack = self._settings_search_text(card_info)
            matched = all(term in haystack for term in terms)

            for widget in section_widgets:
                if matched:
                    self._pack_settings_widget(widget)
                else:
                    self._hide_settings_widget(widget)

            if matched:
                parent = card_info.get("parent")
                for category_key, frame in self.category_frames.items():
                    if frame is parent:
                        visible_categories.add(category_key)
                        break

        for category_key, frame in self.category_frames.items():
            try:
                frame.pack_forget()
                if category_key in visible_categories:
                    frame.pack(fill="both", expand=True)
            except (tk.TclError, RuntimeError) as _:
                pass

        self._highlight_settings_category(None)

    def _highlight_settings_category(self, active_key: str | None) -> None:
        """
        Highlight the active settings category

        Подсвечивает активную категорию настроек
        Підсвічує активну категорію налаштувань
        """
        actual_theme = self._get_actual_theme()
        bg_card_hover = "#383838" if actual_theme == "dark" else "#f8f8f8"
        for key, btn in getattr(self, "category_buttons", {}).items():
            try:
                btn.configure(fg_color=bg_card_hover if key == active_key else "transparent")
            except (tk.TclError, AttributeError, RuntimeError) as _:
                pass
