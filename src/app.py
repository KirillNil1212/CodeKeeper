import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import csv
import shutil
import os
import sqlite3
import hashlib
from datetime import datetime
from cryptography.fernet import Fernet

# --- Импорты системные (наши модули ядра) ---
from src.config import load_config, save_config
from src.resources import IconManager
from src.utils import get_font
from src.database import init_database, get_encryption_key

# --- Импорты окон (дополнительные окна) ---
from src.windows.login import LoginWindow
from src.windows.about import AboutWindow
from src.windows.settings import SettingsWindow
from src.windows.add_edit import AddEditPasswordWindow

# --- ИМПОРТЫ МОДУЛЕЙ UI (компоненты интерфейса) ---
from src.ui.header import UIHeader       # Верхняя панель (Header)
from src.ui.toolbar import UIToolbar     # Панель инструментов (кнопки)
from src.ui.filters import UIFilterBar   # Панель фильтров и поиска
from src.ui.table import UITable         # Таблица данных
from src.ui.menu import create_main_menu  # Главное меню (File, View...)


class PasswordManager:
    """
    Главный класс-контроллер приложения.
    Связывает бизнес-логику (БД, шифрование) с интерфейсом (UI).
    Управляет состоянием приложения, блокировкой и переходами между окнами.
    """

    def __init__(self, root):
        self.root = root
        # Скрываем окно при запуске, пока не пройден логин
        self.root.withdraw()

        # Инициализация менеджера иконок
        self.icon_mgr = IconManager(root)
        self.icon_mgr.set_app_icon(self.root)

        # Загрузка настроек
        self.config = load_config()
        self.last_activity = datetime.now()  # Таймер активности

        # --- Инициализация ядра ---
        self.conn = init_database()
        self.cursor = self.conn.cursor()
        self.encryption_key = get_encryption_key()  # Получаем ключ шифрования
        self.cipher = Fernet(self.encryption_key)

        # --- Константы и словари ---
        # Отображение типов в таблице (Код -> Текст)
        self.type_map_display = {
            "WEB": "Сайт", "OFFLINE": "Оффлайн", "SOCIAL": "Соц. сеть",
            "EMAIL": "Почта", "BANK": "Банк", "CARD": "Карта", "CUSTOM": "Другое"
        }
        # Фильтрация (Текст -> Код)
        self.type_map_filter = {
            "Все": "Все", "Сайт": "WEB", "Оффлайн": "OFFLINE", "Соц. сеть": "SOCIAL",
            "Почта": "EMAIL", "Банк": "BANK", "Карта": "CARD", "Другое": "CUSTOM"
        }
        # Варианты сортировки
        self.sort_options = [
            "Дата изменения (новые)", "Дата изменения (старые)",
            "Название (А→Я) ↑", "Название (Я→А) ↓",
            "Логин (А→Я) ↑", "Логин (Я→А) ↓",
            "Последнее использование (недавние)", "Последнее использование (давние)",
            "Избранные в начале", "Избранные в конце"
        ]

        # Проверка расписания бэкапов
        self.check_backup_schedule()

        # --- Глобальные события ---
        # Клик для сброса выделения
        self.root.bind_all("<Button-1>", self.on_global_click)
        # Сброс таймера блокировки
        self.root.bind_all("<Any-KeyPress>", self.reset_inactivity_timer)
        # Сброс таймера при движении мыши
        self.root.bind_all("<Motion>", self.reset_inactivity_timer)

        # Запуск монитора неактивности
        self.check_inactivity()

        # Построение интерфейса
        self.reload_ui()

        # Логика входа
        if self.config['require_login']:
            LoginWindow(self.root, self.start_app, self.config, self.icon_mgr)
        else:
            self.start_app()

    # --- ЛОГИКА АВТО-БЛОКИРОВКИ ---
    def reset_inactivity_timer(self, event=None):
        """Обновляет время последней активности."""
        self.last_activity = datetime.now()

    def check_inactivity(self):
        """Проверяет простой и блокирует приложение при необходимости."""
        lock_min = self.config.get('auto_lock_min', 0)
        if lock_min > 0:
            elapsed = (datetime.now() -
                       self.last_activity).total_seconds() / 60
            if elapsed >= lock_min:
                self.lock_app()
        self.root.after(10000, self.check_inactivity)

    def lock_app(self):
        """Блокирует приложение, скрывая главное окно."""
        if self.root.state() == 'withdrawn':
            return
        self.root.withdraw()
        # Закрываем все модальные окна
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Toplevel):
                widget.destroy()
        # Показываем окно входа
        LoginWindow(self.root, self.unlock_app, self.config,
                    self.icon_mgr, is_lock_screen=True)

    def unlock_app(self):
        """Разблокирует приложение."""
        self.last_activity = datetime.now()
        self.root.deiconify()

    def start_app(self):
        """Запуск основного цикла работы."""
        self.root.deiconify()
        self.filter_passwords()  # Загрузка данных

    def verify_master_password(self):
        """Проверяет мастер-пароль перед важными действиями (если включено в настройках)."""
        if not self.config.get('confirm_copy', False):
            return True
        try:
            self.cursor.execute(
                "SELECT value FROM app_settings WHERE key='master_hash'")
            res = self.cursor.fetchone()
            if not res:
                return True
            pwd = simpledialog.askstring(
                "Подтверждение", "Введите мастер-пароль:", show='•', parent=self.root)
            if not pwd:
                return False
            if hashlib.sha256(pwd.encode()).hexdigest() == res[0]:
                return True
            messagebox.showerror("Ошибка", "Неверный мастер-пароль")
            return False
        except:
            return False

    # --- КРИПТОГРАФИЯ ---
    def encrypt_password(self, password):
        """Шифрует пароль."""
        return self.cipher.encrypt(password.encode()).decode()

    def decrypt_password(self, encrypted_password):
        """Расшифровывает пароль."""
        try:
            return self.cipher.decrypt(encrypted_password.encode()).decode()
        except:
            return "Ошибка"

    def update_last_used(self, pid):
        """Обновляет метку времени последнего использования записи."""
        try:
            self.cursor.execute(
                "UPDATE passwords SET last_used_at = CURRENT_TIMESTAMP WHERE id=?", (pid,))
            self.conn.commit()
        except Exception as e:
            print(f"Error updating last_used: {e}")

    # --- СБОРКА ИНТЕРФЕЙСА ---
    def reload_ui(self):
        """Перестраивает весь интерфейс (полезно при смене настроек)."""
        for widget in self.root.winfo_children():
            if not isinstance(widget, tk.Toplevel):
                widget.destroy()

        self.config = load_config()

        # --- УСТАНОВКА ЗАГОЛОВКА С ВЕРСИЕЙ ---
        app_version = "0.132"
        self.root.title(f"Кодовник v{app_version}")

        # Настройка окна (компактный/обычный режим)
        if self.config.get('compact_view', False):
            self.root.resizable(False, False)
            self.root.geometry("1100x600")
            if self.root.attributes('-fullscreen'):
                self.root.attributes('-fullscreen', False)
        else:
            self.root.resizable(True, True)
            self.root.minsize(1100, 600)
        self.center_window(1100, 600)

        # Шрифты
        sc = self.config['font_size']
        self.f_head = get_font(16, "bold", sc)
        self.f_tree = get_font(12, "normal", sc)
        self.f_bold = get_font(11, "bold", sc)

        # Стили таблицы
        row_h = int(25 * (int(str(sc).replace("%", ""))/100))
        self.style = ttk.Style()
        self.style.configure("Treeview", font=self.f_tree, rowheight=row_h)
        self.style.configure("Treeview.Heading", font=self.f_bold)

        self.var_fullscreen = tk.BooleanVar(
            value=self.root.attributes('-fullscreen'))
        self.var_compact = tk.BooleanVar(
            value=self.config.get('compact_view', False))

        # --- Подключение модулей UI ---
        create_main_menu(self)              # Меню
        self.ui_header = UIHeader(self)     # Шапка
        self.ui_toolbar = UIToolbar(self)   # Тулбар
        self.ui_filter = UIFilterBar(self)  # Фильтры

        self.create_status_bar()            # Статус бар
        self.ui_table = UITable(self)       # Таблица (отдельный класс)

        self.bind_shortcuts()
        self.filter_passwords()  # Загрузка данных

    # --- МЕТОДЫ-ПРОКСИ (Связь UI и Логики) ---

    def filter_passwords(self):
        """Передает команду таблице обновить данные."""
        if hasattr(self, 'ui_table'):
            self.ui_table.reload_data()

    def load_passwords(self):
        """
        Алиас для filter_passwords.
        ВАЖНО: Используется внешними окнами (AddEditPasswordWindow) для обновления таблицы
        после сохранения данных.
        """
        self.filter_passwords()

    def add_password(self):
        """Открывает окно добавления."""
        if hasattr(self, 'ui_table'):
            self.ui_table.checked_items.clear()
        self.filter_passwords()
        AddEditPasswordWindow(self, mode="add")

    def edit_password(self):
        """Открывает окно редактирования."""
        if not hasattr(self, 'ui_table'):
            return
        checked = self.ui_table.checked_items

        if len(checked) == 1:
            pid = list(checked)[0]
            AddEditPasswordWindow(self, mode="edit", password_id=pid)
        elif len(checked) == 0:
            sel = self.ui_table.tree.selection()
            if sel:
                pid = int(self.ui_table.tree.item(sel[0])['tags'][0])
                AddEditPasswordWindow(self, mode="edit", password_id=pid)
            else:
                messagebox.showinfo(
                    "Инфо", "Выберите запись для редактирования")
        else:
            messagebox.showwarning("Внимание", "Выберите только одну запись")

    def delete_password(self):
        """Удаляет выбранные записи."""
        if not hasattr(self, 'ui_table'):
            return

        ids_to_delete = list(self.ui_table.checked_items)
        if not ids_to_delete:
            sel = self.ui_table.tree.selection()
            if sel:
                ids_to_delete = [
                    int(self.ui_table.tree.item(sel[0])['tags'][0])]

        if not ids_to_delete:
            messagebox.showinfo("Инфо", "Ничего не выбрано для удаления")
            return

        if messagebox.askyesno("Удаление", f"Удалить выбранные записи ({len(ids_to_delete)} шт)?"):
            placeholders = ",".join("?" * len(ids_to_delete))
            self.cursor.execute(
                f"DELETE FROM passwords WHERE id IN ({placeholders})", tuple(ids_to_delete))
            self.conn.commit()
            self.ui_table.checked_items.clear()
            self.filter_passwords()

    def on_global_click(self, event):
        """Сбрасывает выделение при клике в пустое место."""
        widget = event.widget
        try:
            cls = widget.winfo_class()
            ignore_list = ["Treeview", "TScrollbar", "Scrollbar", "Button",
                           "TButton", "Entry", "TEntry", "TCombobox", "Combobox", "Menubutton"]
            if cls in ignore_list:
                return
        except:
            pass

        if hasattr(self, 'ui_table'):
            self.ui_table.clear_selection()

    def create_status_bar(self):
        self.status_bar = tk.Label(
            self.root, text="Загрузка...", bg="#34495e", fg="white", anchor="w", padx=10)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, ipady=5)

    def _copy_to_clip(self, text):
        """Копирует текст в буфер обмена."""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

    def show_tooltip(self, x, y, text):
        """Показывает всплывающую подсказку."""
        t = tk.Toplevel(self.root)
        t.wm_overrideredirect(True)
        t.geometry(f"140x25+{x}+{y-30}")
        tk.Label(t, text=text, bg="#2ecc71", fg="white", font=(
            "Arial", 9)).pack(fill="both", expand=True)
        t.after(1000, t.destroy)

    # --- НАСТРОЙКИ ОКНА ---
    def open_settings(self): SettingsWindow(self)

    def center_window(self, w, h):
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def toggle_fullscreen(self):
        if self.config.get('compact_view', False):
            self.var_fullscreen.set(False)
            messagebox.showinfo(
                "Инфо", "Нельзя вкл. полный экран в компактном виде.")
            return
        state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not state)
        self.var_fullscreen.set(not state)

    def toggle_compact(self):
        if self.root.attributes('-fullscreen'):
            self.root.attributes('-fullscreen', False)
            self.var_fullscreen.set(False)
        self.config['compact_view'] = self.var_compact.get()
        save_config(self.config)
        self.reload_ui()

    def show_shortcuts(self):
        msg = ("Основные:\nCtrl+N : Новая запись\nCtrl+, : Настройки\nCtrl+Q : Выход\nF11 : Полноэкранный режим\n\nРабота с данными:\nCtrl+F : Поиск\nCtrl+I : Импорт CSV\nCtrl+E : Экспорт CSV\n\nРедактирование:\nCtrl+C : Копировать\nCtrl+V : Вставить\nCtrl+A : Выделить всё")
        messagebox.showinfo("Горячие клавиши", msg)

    def show_about(self): AboutWindow(self)

    def bind_shortcuts(self):
        self.root.bind("<Control-n>", lambda e: self.add_password())
        self.root.bind("<Control-i>", lambda e: self.import_csv())
        self.root.bind("<Control-e>", lambda e: self.export_csv())
        self.root.bind("<Control-comma>", lambda e: self.open_settings())
        self.root.bind("<Control-q>", lambda e: self.root.quit())
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.root.bind("<Control-f>", lambda e: self.search_entry.focus_set())

    # --- ИМПОРТ / ЭКСПОРТ / БЭКАП ---
    def check_backup_schedule(self):
        """Проверяет необходимость авто-бэкапа."""
        freq = self.config.get('backup_freq', 'Никогда')
        if freq == "Никогда":
            return
        last = self.config.get('last_backup', '')
        do_backup = False
        now = datetime.now()

        if not last:
            do_backup = True
        else:
            try:
                days_diff = (now - datetime.strptime(last, '%Y-%m-%d')).days
                if freq == "Каждый день" and days_diff >= 1:
                    do_backup = True
                elif freq == "1 раз в неделю" and days_diff >= 7:
                    do_backup = True
            except:
                do_backup = True

        if do_backup:
            try:
                target_dir = self.config.get('backup_path', '') or "_backup"
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                fname = os.path.join(
                    target_dir, f"auto_backup_{now.strftime('%Y%m%d_%H%M%S')}.db")
                if os.path.exists("password_manager.db"):
                    shutil.copy("password_manager.db", fname)
                    self.config['last_backup'] = now.strftime('%Y-%m-%d')
                    save_config(self.config)
            except:
                pass

    def export_csv(self):
        """Экспорт в CSV."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        try:
            self.cursor.execute("SELECT * FROM passwords")
            rows = self.cursor.fetchall()
            col_names = [d[0] for d in self.cursor.description]
            with open(file_path, mode='w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow(col_names)
                enc_idx = col_names.index(
                    "password") if "password" in col_names else -1
                for row in rows:
                    rl = list(row)
                    if enc_idx != -1 and rl[enc_idx]:
                        try:
                            rl[enc_idx] = self.decrypt_password(rl[enc_idx])
                        except:
                            pass
                    writer.writerow(rl)
            messagebox.showinfo("Экспорт", "Успешно!")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def import_csv(self):
        """Импорт из CSV."""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        try:
            with open(file_path, mode='r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                c = 0
                for row in reader:
                    if 'id' in row:
                        del row['id']
                    if 'password' in row and row['password']:
                        row['password'] = self.encrypt_password(
                            row['password'])
                    cols = ', '.join(row.keys())
                    placeholders = ', '.join(['?'] * len(row))
                    self.cursor.execute(
                        f"INSERT INTO passwords ({cols}) VALUES ({placeholders})", list(row.values()))
                    c += 1
                self.conn.commit()
                self.filter_passwords()
                messagebox.showinfo("Импорт", f"Добавлено: {c}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
