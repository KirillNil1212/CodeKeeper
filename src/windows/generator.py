import tkinter as tk
from tkinter import ttk
import string
import random
from src.utils import get_font


class PasswordGenerator(tk.Toplevel):
    """
    Утилита для генерации случайных паролей.
    Может работать как отдельное окно или встраиваться в процесс добавления (target_entry).
    """

    def __init__(self, parent, target_entry=None):
        super().__init__(parent.root)
        self.withdraw()
        self.parent_app = parent
        self.icon_mgr = parent.icon_mgr
        # Поле, куда вставить пароль (если вызвано из формы)
        self.target_entry = target_entry

        self.title("Генератор")
        self.icon_mgr.set_app_icon(self)
        self.geometry("400x480")
        self.resizable(False, False)
        self.transient(parent.root)
        self.grab_set()

        # Настройки генерации по умолчанию
        self.length_var = tk.IntVar(value=16)
        self.use_upper = tk.BooleanVar(value=True)
        self.use_lower = tk.BooleanVar(value=True)
        self.use_digits = tk.BooleanVar(value=True)
        self.use_symbols = tk.BooleanVar(value=True)
        self.exclude_similar = tk.BooleanVar(value=False)  # l, 1, I, O, 0...

        self.create_ui()
        self.center_window()
        self.generate()  # Генерируем первый пароль сразу
        self.deiconify()

    def center_window(self):
        """Центрируем относительно родительского окна."""
        x = self.parent_app.root.winfo_x() + 50
        y = self.parent_app.root.winfo_y() + 50
        self.geometry(f"+{x}+{y}")

    def create_ui(self):
        sc = self.parent_app.config['font_size']
        f_norm = get_font(10, "normal", sc)
        f_bold = get_font(10, "bold", sc)
        # Для отображения пароля используем моноширинный шрифт (Courier), чтобы символы были различимы
        from tkinter import font
        f_mono = font.Font(family="Courier", size=int(
            14 * (int(str(sc).replace("%", ""))/100)), weight="bold")

        header = tk.Frame(self, bg="#2980b9", height=50)
        header.pack(fill=tk.X)
        tk.Label(header, text="Генератор паролей", font=get_font(
            12, "bold", sc), bg="#2980b9", fg="white").pack(pady=10)

        # Область отображения результата
        display_frame = tk.Frame(self, pady=15)
        display_frame.pack(fill=tk.X)
        self.password_display = tk.Entry(
            display_frame, font=f_mono, justify="center", bd=1, relief="solid", state="readonly")
        self.password_display.pack(fill=tk.X, padx=20, pady=5)

        # Кнопки под полем (Обновить, Копировать)
        btn_frame = tk.Frame(display_frame)
        btn_frame.pack(pady=5)

        refresh_img = self.icon_mgr.get("key", "small")
        tk.Button(btn_frame, text=" Обновить", image=refresh_img if refresh_img else None, compound="left",
                  command=self.generate, font=f_norm, cursor="hand2").pack(side=tk.LEFT, padx=5)

        copy_img = self.icon_mgr.get("copy", "small")
        tk.Button(btn_frame, text=" Копировать", image=copy_img if copy_img else None, compound="left",
                  command=self.copy_to_clipboard, font=f_norm, cursor="hand2").pack(side=tk.LEFT, padx=5)

        # Настройки генератора
        settings_frame = tk.Frame(self, padx=20, pady=10)
        settings_frame.pack(fill=tk.BOTH, expand=True)

        # Ползунок длины
        tk.Label(settings_frame, text="Длина пароля:",
                 font=f_norm).pack(anchor="w")
        slider_frame = tk.Frame(settings_frame)
        slider_frame.pack(fill=tk.X, pady=5)
        self.length_label = tk.Label(
            slider_frame, text="16", width=3, font=f_bold)
        self.length_label.pack(side=tk.LEFT)
        scale = ttk.Scale(slider_frame, from_=4, to=64, variable=self.length_var,
                          command=lambda v: self.length_label.config(text=str(int(float(v)))))
        scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        # Генерируем новый пароль при отпускании ползунка
        scale.bind("<ButtonRelease-1>", lambda e: self.generate())

        # Чекбоксы опций
        tk.Checkbutton(settings_frame, text="A-Z (Заглавные)", variable=self.use_upper,
                       command=self.generate, font=f_norm, cursor="hand2").pack(anchor="w")
        tk.Checkbutton(settings_frame, text="a-z (Строчные)", variable=self.use_lower,
                       command=self.generate, font=f_norm, cursor="hand2").pack(anchor="w")
        tk.Checkbutton(settings_frame, text="0-9 (Цифры)", variable=self.use_digits,
                       command=self.generate, font=f_norm, cursor="hand2").pack(anchor="w")
        tk.Checkbutton(settings_frame, text="!@#$%^&* (Спецсимволы)", variable=self.use_symbols,
                       command=self.generate, font=f_norm, cursor="hand2").pack(anchor="w")
        tk.Checkbutton(settings_frame, text="Исключать похожие", variable=self.exclude_similar,
                       command=self.generate, font=f_norm, cursor="hand2").pack(anchor="w", pady=(10, 0))

        # Кнопка вставки (если есть целевое поле)
        footer = tk.Frame(self, pady=20)
        footer.pack(side=tk.BOTTOM, fill=tk.X)

        confirm_img = self.icon_mgr.get("confirm", "small")
        if self.target_entry:
            tk.Button(footer, text="Вставить и закрыть", image=confirm_img if confirm_img else None, compound="left",
                      bg="#27ae60", fg="white", font=f_bold, command=self.apply_password, cursor="hand2").pack(pady=5, ipadx=20)

    def generate(self):
        """Основная логика генерации пароля."""
        length = self.length_var.get()
        chars = ""
        if self.use_upper.get():
            chars += string.ascii_uppercase
        if self.use_lower.get():
            chars += string.ascii_lowercase
        if self.use_digits.get():
            chars += string.digits
        if self.use_symbols.get():
            chars += "!@#$%^&*"

        if self.exclude_similar.get():
            for char in "il1|o0O":
                chars = chars.replace(char, "")

        if not chars:
            chars = "abc"  # Заглушка, если всё отключено

        # Генерация случайной строки
        pwd = ''.join(random.choice(chars) for _ in range(length))

        self.password_display.config(state="normal")
        self.password_display.delete(0, tk.END)
        self.password_display.insert(0, pwd)
        self.password_display.config(state="readonly")

    def copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.password_display.get())
        self.update()

    def apply_password(self):
        """Вставляет сгенерированный пароль в поле родительского окна."""
        if self.target_entry:
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, self.password_display.get())
            # Если поле было скрыто звездочками, открываем его, чтобы пользователь видел, что вставилось
            if hasattr(self.target_entry, 'config'):
                self.target_entry.config(show='')
            self.destroy()
