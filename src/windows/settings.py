import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3
import hashlib
import os
import shutil
from datetime import datetime
from src.config import save_config, load_config
from src.utils import darken


class SettingsWindow(tk.Toplevel):
    """
    Окно настроек приложения.
    Позволяет менять конфигурацию (JSON) и мастер-пароль (БД).
    Интерфейс разделен на 3 основные вкладки для удобства.
    """

    def __init__(self, parent):
        super().__init__(parent.root)
        self.withdraw()
        self.parent = parent
        self.icon_mgr = parent.icon_mgr

        self.title("Настройки")
        self.icon_mgr.set_app_icon(self)

        # Немного увеличим ширину, чтобы вместить объединенные настройки
        self.geometry("650x550")
        self.resizable(False, False)

        self.transient(parent.root)
        self.grab_set()

        # Загружаем текущие настройки
        self.config = load_config()

        self.create_ui()

        # Центрирование окна
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

        self.deiconify()

    def create_ui(self):
        # Используем Notebook для вкладок
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ==========================================
        # Вкладка 1: ОСНОВНЫЕ (Объединяет Общие, Вид и Уведомления)
        # ==========================================
        frame_main = tk.Frame(notebook, bg="#f0f0f0")
        notebook.add(frame_main, text="Основные")

        # --- Секция: Поведение приложения ---
        group_behavior = tk.LabelFrame(
            frame_main, text="Поведение", padx=10, pady=10)
        group_behavior.pack(fill=tk.X, padx=10, pady=5)

        self.var_login = tk.BooleanVar(value=self.config['require_login'])
        tk.Checkbutton(group_behavior, text="Запрашивать пароль при входе в программу",
                       variable=self.var_login).pack(anchor="w")

        f_lock = tk.Frame(group_behavior)
        f_lock.pack(fill=tk.X, pady=5)
        self.var_lock = tk.BooleanVar(value=self.config['auto_lock_min'] > 0)
        tk.Checkbutton(f_lock, text="Автоблокировка при бездействии:",
                       variable=self.var_lock, command=self.toggle_lock_spin).pack(side=tk.LEFT)

        self.spin_lock = tk.Spinbox(f_lock, from_=1, to=120, width=5)
        self.spin_lock.delete(0, "end")
        self.spin_lock.insert(
            0, self.config['auto_lock_min'] if self.config['auto_lock_min'] > 0 else 5)
        self.spin_lock.pack(side=tk.LEFT, padx=5)
        tk.Label(f_lock, text="минут").pack(side=tk.LEFT)
        self.toggle_lock_spin()  # Активация/деактивация спинбокса

        # --- Секция: Интерфейс ---
        group_ui = tk.LabelFrame(
            frame_main, text="Интерфейс", padx=10, pady=10)
        group_ui.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(group_ui, text="Масштаб шрифта:").pack(side=tk.LEFT)
        self.combo_font = ttk.Combobox(group_ui, values=[
                                       "50%", "75%", "90%", "100%", "125%", "150%"], state="readonly", width=10)
        current_font = str(self.config['font_size'])
        if "%" not in current_font:
            current_font += "%"
        self.combo_font.set(current_font)
        self.combo_font.pack(side=tk.LEFT, padx=10)

        # --- Секция: Уведомления ---
        group_notify = tk.LabelFrame(
            frame_main, text="Уведомления и подсказки", padx=10, pady=10)
        group_notify.pack(fill=tk.X, padx=10, pady=5)

        self.var_exp = tk.BooleanVar(value=self.config['notify_expired'])
        tk.Checkbutton(group_notify, text="Подсвечивать старые пароли (более 1 года) красным цветом",
                       variable=self.var_exp).pack(anchor="w")

        self.var_weak = tk.BooleanVar(value=self.config['notify_weak'])
        tk.Checkbutton(group_notify, text="Предупреждать при сохранении слабых паролей (< 8 символов)",
                       variable=self.var_weak).pack(anchor="w")

        # ==========================================
        # Вкладка 2: БЕЗОПАСНОСТЬ
        # ==========================================
        frame_sec = tk.Frame(notebook, bg="#f0f0f0")
        notebook.add(frame_sec, text="Безопасность")

        # --- Секция: Защита данных ---
        group_access = tk.LabelFrame(
            frame_sec, text="Доступ к данным", padx=10, pady=10)
        group_access.pack(fill=tk.X, padx=10, pady=10)

        self.var_confirm = tk.BooleanVar(value=self.config['confirm_copy'])
        tk.Checkbutton(group_access, text="Требовать ввод мастер-пароля перед копированием",
                       variable=self.var_confirm).pack(anchor="w")

        self.var_show_tbl = tk.BooleanVar(
            value=self.config['show_passwords_table'])
        tk.Checkbutton(group_access, text="Отображать колонку 'Пароль' в главной таблице",
                       variable=self.var_show_tbl).pack(anchor="w", pady=(10, 0))
        tk.Label(group_access, text="(Пароли скрыты точками ••••, показываются при наведении курсора)",
                 fg="gray", font=("Arial", 8)).pack(anchor="w", padx=20)

        # --- Секция: Мастер-пароль ---
        group_master = tk.LabelFrame(
            frame_sec, text="Мастер-пароль", padx=10, pady=10)
        group_master.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(group_master, text="Измените мастер-пароль, если подозреваете, что он стал известен посторонним.",
                 wraplength=550, justify="left").pack(anchor="w", pady=(0, 10))

        key_icon = self.icon_mgr.get("key", "small")
        c_orange = "#e67e22"
        tk.Button(group_master, text=" Сменить мастер-пароль", image=key_icon if key_icon else None, compound="left",
                  command=self.change_master_password, bg=c_orange, activebackground=darken(
                      c_orange),
                  fg="white", font=("Arial", 10, "bold"), cursor="hand2", padx=10).pack(anchor="w")

        # ==========================================
        # Вкладка 3: РЕЗЕРВНОЕ КОПИРОВАНИЕ
        # ==========================================
        frame_bak = tk.Frame(notebook, bg="#f0f0f0")
        notebook.add(frame_bak, text="Резервная копия")

        # --- Секция: Автоматический бэкап ---
        group_auto = tk.LabelFrame(
            frame_bak, text="Автоматическое сохранение", padx=10, pady=10)
        group_auto.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(group_auto, text="Как часто создавать копию базы данных:").pack(
            anchor="w")
        self.combo_backup = ttk.Combobox(
            group_auto, values=["Никогда", "1 раз в неделю", "Каждый день"], state="readonly", width=30)
        self.combo_backup.set(self.config['backup_freq'])
        self.combo_backup.pack(anchor="w", pady=5)

        tk.Label(group_auto, text="Папка для хранения файлов:").pack(
            anchor="w", pady=(10, 0))
        path_frame = tk.Frame(group_auto)
        path_frame.pack(fill=tk.X, pady=5)

        self.path_entry = tk.Entry(path_frame)
        self.path_entry.insert(0, self.config.get(
            'backup_path', '') or "По умолчанию (_backup)")
        self.path_entry.config(state="readonly")
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        search_icon = self.icon_mgr.get("search", "small")
        tk.Button(path_frame, text="...", image=search_icon if search_icon else None,
                  command=self.choose_backup_path, width=30, cursor="hand2").pack(side=tk.LEFT, padx=5)

        # --- Секция: Ручное управление ---
        group_manual = tk.LabelFrame(
            frame_bak, text="Ручное управление", padx=10, pady=10)
        group_manual.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(group_manual, text="Вы можете создать полную копию базы данных прямо сейчас.",
                 fg="gray").pack(anchor="w", pady=(0, 10))

        # Используем иконку экспорта как метафору сохранения
        save_icon = self.icon_mgr.get("export", "small")
        c_blue = "#3498db"
        tk.Button(group_manual, text=" Создать копию сейчас", image=save_icon if save_icon else None, compound="left",
                  command=self.make_backup, bg=c_blue, activebackground=darken(
                      c_blue),
                  fg="white", font=("Arial", 10, "bold"), cursor="hand2", padx=10).pack(anchor="w")

        # ==========================================
        # НИЖНЯЯ ПАНЕЛЬ КНОПОК (Общая для всех вкладок)
        # ==========================================
        # Светлый фон для контраста
        btn_frame = tk.Frame(self, pady=15, padx=10, bg="#ecf0f1")
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)

        save_img = self.icon_mgr.get("confirm", "small")
        close_img = self.icon_mgr.get("close", "small")

        c_save, c_cancel = "#27ae60", "#e74c3c"

        # Кнопка Сохранить (Справа)
        tk.Button(btn_frame, text=" Сохранить и закрыть", image=save_img if save_img else None, compound="left",
                  bg=c_save, activebackground=darken(c_save), fg="white", font=("Arial", 10, "bold"),
                  command=self.save_settings, cursor="hand2", padx=20).pack(side=tk.RIGHT, padx=5)

        # Кнопка Отмена (Слева от сохранить, но визуально можно и справа)
        tk.Button(btn_frame, text="Отмена", image=close_img if close_img else None, compound="left",
                  bg=c_cancel, activebackground=darken(c_cancel), fg="white", font=("Arial", 10),
                  command=self.destroy, cursor="hand2", padx=15).pack(side=tk.RIGHT, padx=5)

    def toggle_lock_spin(self):
        """Блокирует поле ввода минут, если галочка автоблокировки снята."""
        if self.var_lock.get():
            self.spin_lock.config(state="normal")
        else:
            self.spin_lock.config(state="disabled")

    def choose_backup_path(self):
        """Диалог выбора папки для бэкапов."""
        d = filedialog.askdirectory()
        if d:
            self.path_entry.config(state="normal")
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, d)
            self.path_entry.config(state="readonly")
            self.selected_backup_path = d
        else:
            self.selected_backup_path = ""

    def make_backup(self):
        """Создание резервной копии вручную."""
        try:
            target_dir = self.config.get('backup_path', '')
            if not target_dir:
                target_dir = "_backup"
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            fname = os.path.join(
                target_dir, f"backup_manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            shutil.copy("password_manager.db", fname)
            messagebox.showinfo("Бэкап", f"Копия создана успешно:\n{fname}")

            # Обновляем метку времени последнего бэкапа
            new_c = self.config.copy()
            new_c['last_backup'] = datetime.now().strftime('%Y-%m-%d')
            save_config(new_c)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def change_master_password(self):
        """Логика смены мастер-пароля."""
        # 1. Проверка текущего
        current = simpledialog.askstring(
            "Смена пароля", "Введите ТЕКУЩИЙ мастер-пароль:", show='•', parent=self)
        if not current:
            return

        conn = sqlite3.connect('password_manager.db')
        cur = conn.cursor()
        cur.execute("SELECT value FROM app_settings WHERE key='master_hash'")
        res = cur.fetchone()

        if not res:
            conn.close()
            return

        stored_hash = res[0]
        # Хэшируем введенный и сравниваем с БД
        if hashlib.sha256(current.encode()).hexdigest() != stored_hash:
            messagebox.showerror("Ошибка", "Неверный текущий пароль")
            conn.close()
            return

        # 2. Ввод нового
        new_pass = simpledialog.askstring(
            "Смена пароля", "Введите НОВЫЙ мастер-пароль:", show='•', parent=self)
        if not new_pass:
            conn.close()
            return

        # 3. Подтверждение
        confirm_pass = simpledialog.askstring(
            "Смена пароля", "Повторите НОВЫЙ мастер-пароль:", show='•', parent=self)
        if new_pass != confirm_pass:
            messagebox.showerror("Ошибка", "Новые пароли не совпадают!")
            conn.close()
            return

        # 4. Сохранение нового хэша
        new_hash = hashlib.sha256(new_pass.encode()).hexdigest()
        cur.execute(
            "UPDATE app_settings SET value=? WHERE key='master_hash'", (new_hash,))
        conn.commit()
        conn.close()
        messagebox.showinfo("Успех", "Мастер-пароль успешно изменен!")

    def save_settings(self):
        """Сбор всех данных с формы и сохранение в config.json."""
        new_conf = self.config.copy()

        # Основные
        new_conf['require_login'] = self.var_login.get()
        if self.var_lock.get():
            try:
                val = int(self.spin_lock.get())
                new_conf['auto_lock_min'] = val
            except:
                new_conf['auto_lock_min'] = 5  # Фолбэк при ошибке ввода
        else:
            new_conf['auto_lock_min'] = 0

        new_conf['font_size'] = self.combo_font.get()
        new_conf['notify_expired'] = self.var_exp.get()
        new_conf['notify_weak'] = self.var_weak.get()

        # Безопасность
        new_conf['confirm_copy'] = self.var_confirm.get()
        new_conf['show_passwords_table'] = self.var_show_tbl.get()

        # Бэкап
        new_conf['backup_freq'] = self.combo_backup.get()
        current_display = self.path_entry.get()
        if current_display != "По умолчанию (_backup)":
            new_conf['backup_path'] = current_display
        else:
            new_conf['backup_path'] = ""

        # Сохраняем и обновляем приложение
        save_config(new_conf)
        self.destroy()
        self.parent.reload_ui()
