import json
import os

# Имя файла, в котором хранятся настройки.
# Он будет создан рядом с main.py при первом запуске.
CONFIG_FILE = "config.json"


def load_config():
    """
    Загружает конфигурацию из файла config.json.
    Если файла нет или он поврежден, возвращает настройки по умолчанию.
    """
    # Словарь с настройками "по умолчанию".
    # Используется, если пользователь еще ничего не менял.
    default_config = {
        "require_login": True,          # Требовать мастер-пароль при входе
        "auto_lock_min": 5,             # Автоблокировка через 5 минут
        "confirm_copy": False,          # Подтверждать копирование паролем
        "show_passwords_table": False,  # Показывать колонку паролей в таблице
        "font_size": "100%",            # Масштаб шрифта
        "compact_view": False,          # Компактный режим окна
        "backup_freq": "1 раз в неделю",  # Частота бэкапов
        "last_backup": "",              # Дата последнего бэкапа
        # Куда сохранять бэкапы (пусто = _backup)
        "backup_path": "",
        "notify_expired": True,         # Подсвечивать старые пароли
        "notify_weak": True             # Предупреждать о слабых паролях
    }

    # Если файла конфига нет, возвращаем дефолтные настройки
    if not os.path.exists(CONFIG_FILE):
        return default_config

    try:
        # Пытаемся прочитать JSON файл
        with open(CONFIG_FILE, "r") as f:
            c = json.load(f)

            # Важный момент: миграция настроек.
            # Если мы добавили новую опцию в новой версии программы,
            # её нет в старом файле config.json у пользователя.
            # Этот цикл добавляет недостающие ключи из default_config.
            for k, v in default_config.items():
                if k not in c:
                    c[k] = v
            return c
    except:
        # Если файл поврежден (например, некорректный JSON),
        # просто возвращаем дефолт, чтобы программа не упала.
        return default_config


def save_config(config):
    """
    Сохраняет словарь настроек в файл config.json.
    """
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)
