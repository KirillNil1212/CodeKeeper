import os
import sys
from tkinter import PhotoImage


def resource_path(relative_path):
    """
    Возвращает абсолютный путь к ресурсу.
    Работает и в IDE, и в EXE.
    """
    if hasattr(sys, '_MEIPASS'):
        # --- РЕЖИМ EXE (PyInstaller) ---
        return os.path.join(sys._MEIPASS, relative_path)

    # --- РЕЖИМ PYTHON (Разработка) ---
    # Путь: CodeKeeper/src/resources.py
    current_file = os.path.abspath(__file__)
    # Путь: CodeKeeper/src
    src_dir = os.path.dirname(current_file)
    # Путь: CodeKeeper (корень проекта)
    project_root = os.path.dirname(src_dir)

    return os.path.join(project_root, relative_path)


class IconManager:
    def __init__(self, root):
        self.root = root
        self.icons = {}
        self._load_icons()

    def _load_icons(self):
        # Базовая папка с иконками: assets/icons
        icons_dir = resource_path(os.path.join("assets", "icons"))

        # Карта соответствия: Ключ в коде -> Имя файла на диске
        # Я составил её на основе твоего списка
        icon_map = {
            # Основные действия
            "add": "Add.gif",
            "delete": "Delete.gif",
            "edit": "Edit.gif",
            "save": "Confirm.gif",      # В коде часто используется save, а файл Confirm
            "close": "Close.gif",       # Закрыть диалог
            "search": "Search.gif",     # Если файла нет, код просто пропустит

            # Статусы и виды
            "lock": "Locked.gif",
            "unlock": "Unlocked.gif",
            "show": "Show.gif",
            "hide": "Hide.gif",
            "favorite": "Favorite.gif",

            # Импорт/Экспорт
            "import": "Import_csv.gif",
            "export": "Export_csv.gif",

            # Разное
            "key": "Key.gif",
            "copy": "Сopy.gif",         # Внимание: буква С может быть кириллической в имени файла
            "copy_pass": "copy_password.gif",
            "copy_login": "copy_login.gif",

            # Меню и окна
            "settings": "Settings.gif",
            "exit": "exit.gif",
            "fullscreen": "fullscreen.gif",
            "compact": "compact.gif",
            "shortcuts": "shortcuts.gif",
            "info": "info.gif",
            "view": "view.gif"
        }

        print(f"[IconManager] Загрузка иконок из: {icons_dir}")

        if not os.path.exists(icons_dir):
            print(f"[IconManager] ОШИБКА: Папка не найдена: {icons_dir}")
            return

        for key, filename in icon_map.items():
            full_path = os.path.join(icons_dir, filename)

            # Проверка на случай, если файл называется copy.gif (латиница), а в списке Сopy.gif (кириллица)
            if not os.path.exists(full_path):
                # Попробуем привести к нижнему регистру для поиска
                alt_path = os.path.join(icons_dir, filename.lower())
                if os.path.exists(alt_path):
                    full_path = alt_path

            if os.path.exists(full_path):
                try:
                    # Загружаем оригинал
                    original = PhotoImage(file=full_path)

                    # Создаем уменьшенную копию (subsample 2)
                    small = original.subsample(2, 2)

                    self.icons[key] = original
                    self.icons[f"{key}_small"] = small
                    # print(f"OK: {key}")
                except Exception as e:
                    print(f"Ошибка чтения {filename}: {e}")
            else:
                print(f"Файл не найден: {filename}")

        # Дополнительный алиас для замка блокировки (если в коде используется locked)
        if "lock" in self.icons:
            self.icons["locked"] = self.icons["lock"]
            self.icons["locked_small"] = self.icons["lock_small"]

    def get(self, name, size="normal"):
        key = name if size == "normal" else f"{name}_small"
        return self.icons.get(key, None)

    def set_app_icon(self, window):
        """Установка иконки приложения (.ico для окна)"""
        try:
            # Путь: assets/icons/app_ico/cood32x32.ico
            path_ico = resource_path(os.path.join(
                "assets", "icons", "app_ico", "cood32x32.ico"))

            if os.path.exists(path_ico):
                window.iconbitmap(path_ico)
            else:
                print(f"Иконка приложения не найдена: {path_ico}")

                # Попытка загрузить png версию
                path_png = resource_path(os.path.join(
                    "assets", "icons", "app_ico", "cood32x32.png"))
                if os.path.exists(path_png):
                    icon = PhotoImage(file=path_png)
                    window.iconphoto(True, icon)
        except Exception as e:
            print(f"Не удалось установить иконку окна: {e}")
