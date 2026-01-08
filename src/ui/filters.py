import tkinter as tk
from tkinter import ttk
from src.utils import get_font
from src.core.clipboard import ClipboardUtils


class UIFilterBar:
    """Компонент панели фильтров и поиска (строка с лупой)."""

    def __init__(self, app):
        self.app = app
        # Создаем рамку для панели
        self.frame = tk.Frame(app.root, bg="#ecf0f1", height=45)
        self.frame.pack(fill=tk.X)
        self._build()

    def _build(self):
        font = get_font(10, "normal", self.app.config['font_size'])
        ic = self.app.icon_mgr

        # --- Иконка поиска (декоративная) ---
        icon = ic.get("search", "small")
        tk.Label(self.frame, image=icon if icon else None, text="🔍" if not icon else "",
                 bg="#ecf0f1").pack(side=tk.LEFT, padx=(10, 2))

        # --- Поле ввода поиска ---
        self.app.search_entry = tk.Entry(
            self.frame, width=25, font=font, fg="gray")
        self.app.search_entry.insert(0, "Поиск...")
        self.app.search_entry.pack(side=tk.LEFT, padx=5, pady=10)

        # Подключаем "умный" буфер обмена
        ClipboardUtils.enable_universal_shortcuts(self.app.search_entry)

        # Бинды для эффекта placeholder'а ("Поиск...")
        self.app.search_entry.bind('<FocusIn>', self._on_focus_in)
        self.app.search_entry.bind('<FocusOut>', self._on_focus_out)

        # Живой поиск: обновляем таблицу при каждом отпускании клавиши
        self.app.search_entry.bind(
            '<KeyRelease>', lambda e: self.app.filter_passwords())

        # --- Выпадающий список "Тип" ---
        tk.Label(self.frame, text="Тип:", bg="#ecf0f1",
                 font=font).pack(side=tk.LEFT, padx=(15, 2))
        self.app.filter_combobox = ttk.Combobox(self.frame, values=list(self.app.type_map_filter.keys()),
                                                state="readonly", width=12, font=font)
        self.app.filter_combobox.current(0)  # Выбираем "Все" по умолчанию
        self.app.filter_combobox.pack(side=tk.LEFT, padx=2)
        # При выборе из списка обновляем таблицу
        self.app.filter_combobox.bind(
            '<<ComboboxSelected>>', lambda e: self.app.filter_passwords())

        # --- Выпадающий список "Сортировать" ---
        tk.Label(self.frame, text="Сортировать:", bg="#ecf0f1",
                 font=font).pack(side=tk.LEFT, padx=(15, 2))
        self.app.sort_combobox = ttk.Combobox(self.frame, values=self.app.sort_options,
                                              state="readonly", width=25, font=font)
        self.app.sort_combobox.current(0)  # Выбираем сортировку по умолчанию
        self.app.sort_combobox.pack(side=tk.LEFT, padx=2)
        self.app.sort_combobox.bind(
            '<<ComboboxSelected>>', lambda e: self.app.filter_passwords())

    def _on_focus_in(self, event):
        """Убирает текст 'Поиск...' при клике в поле."""
        if self.app.search_entry.get() == "Поиск...":
            self.app.search_entry.delete(0, tk.END)
            self.app.search_entry.config(fg="black")

    def _on_focus_out(self, event):
        """Возвращает текст 'Поиск...', если поле пустое."""
        if not self.app.search_entry.get():
            self.app.search_entry.insert(0, "Поиск...")
            self.app.search_entry.config(fg="gray")
