import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser  # Модуль для открытия ссылок в браузере по умолчанию


class AboutWindow(tk.Toplevel):
    """
    Модальное окно с информацией о программе, авторе и лицензии.
    Наследуется от Toplevel (отдельное окно поверх основного).
    """

    def __init__(self, parent):
        super().__init__(parent.root)
        self.withdraw()  # Скрываем пока настраиваем
        self.parent = parent
        self.icon_mgr = parent.icon_mgr

        self.title("О программе")
        self.icon_mgr.set_app_icon(self)

        # Фиксированный размер окна
        self.geometry("600x650")
        self.resizable(False, False)

        # Делаем окно модальным (блокирует доступ к родительскому окну)
        self.transient(parent.root)
        self.grab_set()

        self.create_ui()

        # Центрируем окно на экране
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")
        self.deiconify()

    def create_ui(self):
        """Создает все визуальные элементы окна."""
        # --- Шапка с логотипом ---
        header_frame = tk.Frame(self, bg="white", padx=20, pady=20)
        header_frame.pack(fill=tk.X)

        logo_img = self.icon_mgr.get("key")
        if logo_img:
            tk.Label(header_frame, image=logo_img, bg="white").pack(
                side=tk.LEFT, padx=(0, 20))

        title_frame = tk.Frame(header_frame, bg="white")
        title_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(title_frame, text="КОДОВНИК", font=(
            "Arial", 22, "bold"), bg="white", fg="#2c3e50").pack(anchor="w")
        tk.Label(title_frame, text="(CODE KEEPER)  |  Версия 1.0.0  Сборка от 10.01.2026",
                 font=("Arial", 10), bg="white", fg="#7f8c8d").pack(anchor="w", pady=(5, 0))

        # --- Основной контейнер с текстом ---
        container = tk.Frame(self, bg="#ecf0f1", padx=15, pady=15)
        container.pack(fill=tk.BOTH, expand=True)

        # Используем виджет Text для форматированного вывода информации
        self.text_area = tk.Text(container, wrap="word", font=(
            "Arial", 11), bg="#ecf0f1", fg="#2c3e50", relief="flat", padx=10, pady=10)

        # Полоса прокрутки
        sb = ttk.Scrollbar(container, orient="vertical",
                           command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=sb.set)

        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.insert_content()
        # Блокируем редактирование текста пользователем
        self.text_area.config(state="disabled")

        # --- Подвал с кнопками ---
        footer_frame = tk.Frame(self, pady=15, padx=20, bg="#ecf0f1")
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

        f_btn = ("Arial", 10, "bold")

        close_img = self.icon_mgr.get("close", "small")
        tk.Button(footer_frame, text="Закрыть", image=close_img if close_img else None, compound="left",
                  bg="#e74c3c", fg="white", font=f_btn, width=120 if close_img else 15, command=self.destroy, cursor="hand2").pack(side=tk.RIGHT, padx=5)

        tk.Button(footer_frame, text="Проверить обновления", bg="#3498db", fg="white", font=f_btn,
                  command=self.check_updates, cursor="hand2", padx=10).pack(side=tk.RIGHT, padx=5)

        tk.Button(footer_frame, text="Сайт проекта", bg="#95a5a6", fg="white", font=f_btn,
                  command=lambda: webbrowser.open("https://github.com/"), cursor="hand2", padx=10).pack(side=tk.RIGHT, padx=5)

    def insert_content(self):
        """Вставка текста с форматированием (тегами) в виджет Text."""
        t = self.text_area
        # Настройка стилей для тегов
        t.tag_config("bold", font=("Arial", 11, "bold"))
        t.tag_config("title", font=("Arial", 12, "bold"),
                     spacing1=10, spacing3=5)
        t.tag_config("check", foreground="#27ae60", font=("Arial", 11, "bold"))
        t.tag_config("warning_box", background="#fadbd8", foreground="#c0392b",
                     lmargin1=10, lmargin2=10, rmargin=10, spacing1=10, spacing3=10)
        t.tag_config("italic", font=("Arial", 11, "italic"),
                     foreground="#7f8c8d")

        t.insert(tk.END, "Кодовник — это безопасный менеджер паролей для локального хранения и управления вашими конфиденциальными данными.\n\n")

        t.insert(tk.END, "Основные возможности:\n", "title")
        feats = [
            "• Шифрованное хранение паролей и данных",
            "• Поддержка различных типов записей",
            "• Мастер-пароль для защиты доступа",
            "• Генератор сложных паролей",
            "• Резервное копирование и восстановление",
            "• Импорт/экспорт данных\n"
        ]
        for f in feats:
            t.insert(tk.END, f + "\n")

        t.insert(tk.END, "Принципы работы:\n", "title")
        princ = [
            "• Все данные хранятся локально на вашем компьютере",
            "• Пароли шифруются перед сохранением",
            "• Программа не требует интернет-соединения",
            "• Исходный код открыт для проверки\n"
        ]
        for p in princ:
            t.insert(tk.END, p + "\n")

        t.insert(tk.END, "\n")
        t.insert(tk.END, "[✓] Для личного использования\n", "check")
        t.insert(tk.END, "[✓] Бесплатно и без рекламы\n", "check")
        t.insert(tk.END, "[✓] Конфиденциальность гарантирована\n", "check")

        t.insert(
            tk.END, "\n______________________________________________________\n\n")

        t.insert(tk.END, "Разработчик: Николаев Кирилл Викторович\n")
        t.insert(tk.END, "Студент 1 курса магистратуры ИТМО\n")
        t.insert(
            tk.END, "направления 'Цифровые методы в гуманитарных исследованиях'\n")
        t.insert(tk.END, "Контакт: Kolmikol12@gmail.com\n\n")

        t.insert(tk.END, "⚠️ Внимание: Мастер-пароль невозможно восстановить при утере.\nРекомендуется регулярно создавать резервные копии вашей базы данных.\n", "warning_box")

        t.insert(tk.END, "\nСпасибо, что используете Кодовник!", "italic")

    def check_updates(self):
        """Заглушка для проверки обновлений."""
        messagebox.showinfo(
            "Обновление", "У вас установлена последняя версия Кодовника (v1.0.0).")
