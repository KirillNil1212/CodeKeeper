import tkinter as tk
from tkinter import messagebox
import sqlite3
import hashlib
from src.utils import get_font


class LoginWindow(tk.Toplevel):
    """
    Окно авторизации. Используется в двух режимах:
    1. При запуске программы (Login).
    2. При автоблокировке (Lock Screen).
    """

    def __init__(self, parent, on_success, config, icon_manager, is_lock_screen=False):
        super().__init__(parent)
        self.withdraw()
        self.on_success = on_success  # Функция, которую нужно вызвать при успешном входе
        self.config = config
        self.icon_mgr = icon_manager
        self.is_lock_screen = is_lock_screen
        self.scale = self.config['font_size']

        self.icon_mgr.set_app_icon(self)

        title_text = "Блокировка" if is_lock_screen else "Вход"
        self.title(title_text)
        self.geometry("400x380")
        self.resizable(False, False)
        self.configure(bg="#ecf0f1")

        # Центрирование
        x = parent.winfo_screenwidth() // 2 - 200
        y = parent.winfo_screenheight() // 2 - 190
        self.geometry(f"+{x}+{y}")

        if is_lock_screen:
            # Блокируем закрытие окна на крестик
            self.protocol("WM_DELETE_WINDOW", lambda: None)
            self.attributes("-topmost", True)  # Окно всегда сверху
        else:
            # Если закрыть окно входа при старте - программа закрывается
            self.protocol("WM_DELETE_WINDOW", parent.quit)

        self.conn = sqlite3.connect('password_manager.db')
        self.cursor = self.conn.cursor()

        # Проверка, задан ли уже пароль в БД
        self.check_master_password_exists()

        self.create_ui()
        self.deiconify()

    def check_master_password_exists(self):
        """Проверяет наличие хэша пароля в таблице настроек."""
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT)")
        self.cursor.execute(
            "SELECT value FROM app_settings WHERE key='master_hash'")
        self.stored_hash = self.cursor.fetchone()
        # Если нет хэша - это новый пользователь
        self.is_new_user = self.stored_hash is None

    def create_ui(self):
        f_head = get_font(16, "bold", self.scale)
        f_norm = get_font(12, "normal", self.scale)
        f_btn = get_font(10, "bold", self.scale)

        # Логотип (замок или ключ)
        logo_img = self.icon_mgr.get(
            "locked" if self.is_lock_screen else "key")
        if logo_img:
            tk.Label(self, image=logo_img, bg="#ecf0f1").pack(pady=(30, 10))
        else:
            icon_char = "🔒" if self.is_lock_screen else "🔐"
            tk.Label(self, text=icon_char, font=("Arial", 50),
                     bg="#ecf0f1").pack(pady=(30, 10))

        header_text = "Сеанс заблокирован" if self.is_lock_screen else "Кодовник"
        tk.Label(self, text=header_text, font=f_head,
                 bg="#ecf0f1", fg="#2c3e50").pack()

        # Текст инструкции меняется для нового пользователя
        lbl_text = "Создайте мастер-пароль:" if self.is_new_user else "Введите мастер-пароль:"
        tk.Label(self, text=lbl_text, font=f_norm,
                 bg="#ecf0f1", fg="#7f8c8d").pack(pady=(20, 5))

        pass_container = tk.Frame(self, bg="#ecf0f1")
        pass_container.pack(pady=5)

        # Центрирование поля ввода (костыль с пустым фреймом слева)
        tk.Frame(pass_container, width=35, height=1,
                 bg="#ecf0f1").pack(side=tk.LEFT)

        self.entry = tk.Entry(pass_container, show="•",
                              font=f_norm, width=20, relief="solid", bd=1)
        self.entry.pack(side=tk.LEFT, ipady=3)
        self.entry.bind("<Return>", lambda e: self.check_password())

        eye_img = self.icon_mgr.get("show", "small")
        self.btn_eye = tk.Button(pass_container, image=eye_img if eye_img else None, text="👁" if not eye_img else "",
                                 command=self.toggle_pass, relief="flat", bg="#ecf0f1", cursor="hand2")
        self.btn_eye.pack(side=tk.LEFT, padx=(5, 0))

        btn_text = "Создать базу" if self.is_new_user else (
            "Разблокировать" if self.is_lock_screen else "Войти")

        confirm_img = self.icon_mgr.get("confirm", "small")
        tk.Button(self, text=btn_text, image=confirm_img if confirm_img else None, compound="left",
                  command=self.check_password, bg="#27ae60", fg="white", font=f_btn, width=180 if confirm_img else 15, cursor="hand2").pack(pady=20)

        # Кнопка сброса (только при обычном входе и если пароль уже есть)
        if not self.is_new_user and not self.is_lock_screen:
            tk.Button(self, text="Забыли пароль?", command=self.forgot_pass,
                      bg="#ecf0f1", fg="#e74c3c", relief="flat", cursor="hand2").pack()

    def toggle_pass(self):
        """Показать/скрыть вводимый пароль."""
        if self.entry.cget('show') == '':
            self.entry.config(show='•')
            img = self.icon_mgr.get("show", "small")
            if img:
                self.btn_eye.config(image=img)
        else:
            self.entry.config(show='')
            img = self.icon_mgr.get("hide", "small")
            if img:
                self.btn_eye.config(image=img)

    def hash_password(self, pwd):
        """Хэширование пароля SHA-256."""
        return hashlib.sha256(pwd.encode()).hexdigest()

    def check_password(self):
        """Проверка введенного пароля."""
        pwd = self.entry.get()
        if not pwd:
            return
        h = self.hash_password(pwd)

        if self.is_new_user:
            # Если пользователь новый - сохраняем хэш
            self.cursor.execute(
                "INSERT INTO app_settings (key, value) VALUES ('master_hash', ?)", (h,))
            self.conn.commit()
            self.conn.close()
            self.destroy()
            self.on_success()  # Запускаем основное приложение
        else:
            # Если пользователь существует - сверяем хэш
            if h == self.stored_hash[0]:
                self.conn.close()
                self.destroy()
                self.on_success()
            else:
                messagebox.showerror("Ошибка", "Неверный пароль!")
                self.entry.delete(0, tk.END)

    def forgot_pass(self):
        """Сброс базы данных при потере пароля."""
        if messagebox.askyesno("Сброс", "Сброс пароля приведет к потере доступа к старой базе. Создать новую?"):
            # Удаляем хэш мастера, что переведет программу в режим "Новый пользователь"
            # (Сами зашифрованные данные останутся, но прочитать их будет нельзя без старого ключа)
            self.cursor.execute(
                "DELETE FROM app_settings WHERE key='master_hash'")
            self.conn.commit()
            self.check_master_password_exists()
            # Перерисовываем интерфейс
            for widget in self.winfo_children():
                widget.destroy()
            self.create_ui()
