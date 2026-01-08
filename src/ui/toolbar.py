import tkinter as tk
import string
import random
from src.utils import get_font, darken
from src.core.clipboard import ClipboardUtils


class UIToolbar:
    """Компонент панели инструментов (Toolbar), расположенной под шапкой."""

    def __init__(self, app):
        self.app = app
        # Светлый фон для панели инструментов
        self.frame = tk.Frame(app.root, bg="#ecf0f1", height=50)
        self.frame.pack(fill=tk.X, pady=2)
        self._build()

    def _build(self):
        font = get_font(9, "bold", self.app.config['font_size'])
        ic = self.app.icon_mgr
        # Цвета кнопок
        c_add, c_del, c_edit = "#27ae60", "#e74c3c", "#f39c12"

        # --- Кнопка "Добавить" ---
        self.app.btn_add = tk.Button(self.frame, text=" Добавить", image=ic.get("add"), compound="left",
                                     bg=c_add, activebackground=darken(c_add), fg="white", font=font,
                                     padx=15, pady=5, command=self.app.add_password, cursor="hand2")
        self.app.btn_add.pack(side=tk.LEFT, padx=5, pady=5)

        # --- Кнопка "Удалить" ---
        self.app.btn_del = tk.Button(self.frame, text=" Удалить", image=ic.get("delete"), compound="left",
                                     bg=c_del, activebackground=darken(c_del), fg="white", font=font,
                                     padx=15, pady=5, command=self.app.delete_password, cursor="hand2")
        self.app.btn_del.pack(side=tk.LEFT, padx=5, pady=5)

        # --- Кнопка "Редактировать" ---
        self.app.btn_edit = tk.Button(self.frame, text=" Редактировать", image=ic.get("edit"), compound="left",
                                      bg=c_edit, activebackground=darken(c_edit), fg="white", font=font,
                                      padx=15, pady=5, command=self.app.edit_password, cursor="hand2")
        self.app.btn_edit.pack(side=tk.LEFT, padx=5, pady=5)

        # --- Мини-генератор паролей (справа) ---
        self._build_mini_gen(ic)

    def _build_mini_gen(self, ic):
        """Создает виджет быстрого генератора паролей."""
        gen_frame = tk.Frame(self.frame, bg="#bdc3c7", padx=5, pady=5)
        gen_frame.pack(side=tk.RIGHT, padx=10, pady=5)

        tk.Label(gen_frame, text="Быстрый пароль:", bg="#bdc3c7",
                 font=("Arial", 8, "bold"), fg="#2c3e50").pack(side=tk.LEFT, padx=(5, 5))

        # Поле для отображения сгенерированного пароля
        self.entry = tk.Entry(gen_frame, width=16, font=(
            "Courier", 10), justify="center")
        self.entry.pack(side=tk.LEFT, padx=2)

        # Подключаем "умный" буфер обмена (для Ctrl+C)
        ClipboardUtils.enable_universal_shortcuts(self.entry)

        # Кнопка Обновить (Refresh)
        tk.Button(gen_frame, image=ic.get("key", "small"), text="↻",
                  command=self._refresh, bg="white", relief="flat", cursor="hand2").pack(side=tk.LEFT, padx=2)

        # Кнопка Копировать
        tk.Button(gen_frame, image=ic.get("copy", "small"), text="📋",
                  command=self._copy, bg="white", relief="flat", cursor="hand2").pack(side=tk.LEFT, padx=2)

    def _refresh(self):
        """Генерирует случайный пароль длиной 16 символов."""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        pwd = ''.join(random.choice(chars) for _ in range(16))
        self.entry.delete(0, tk.END)
        self.entry.insert(0, pwd)

    def _copy(self):
        """Копирует сгенерированный пароль в буфер обмена."""
        pwd = self.entry.get()
        if pwd:
            self.app.root.clipboard_clear()
            self.app.root.clipboard_append(pwd)
            self.app.root.update()

            # Визуальный эффект (зеленая вспышка)
            self.entry.config(bg="#2ecc71")
            self.app.root.after(300, lambda: self.entry.config(bg="white"))
