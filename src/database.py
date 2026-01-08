import sqlite3
import os
from cryptography.fernet import Fernet


def init_database():
    """
    Инициализирует подключение к БД и создает необходимые таблицы, если их нет.
    Возвращает объект соединения (connection).
    """
    # Подключаемся к файлу базы данных
    conn = sqlite3.connect('password_manager.db')
    cursor = conn.cursor()

    # Создаем основную таблицу для хранения записей.
    # Используем IF NOT EXISTS, чтобы не сломать существующую базу.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
            last_used_at TIMESTAMP, 
            name TEXT NOT NULL,       -- Название записи
            type TEXT NOT NULL,       -- Тип (WEB, CARD, ...)
            password TEXT,            -- Зашифрованный пароль
            username TEXT             -- Логин/Имя пользователя
        )
    ''')

    # Таблица для хранения системных настроек, например, хэша мастер-пароля.
    # (Остальные настройки хранятся в JSON, но хэш безопаснее держать в БД)
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT)")

    # Проверяем, все ли колонки есть в таблице (миграция структуры)
    ensure_columns(cursor)

    conn.commit()
    return conn


def ensure_columns(cursor):
    """
    Проверяет структуру таблицы passwords и добавляет недостающие колонки.
    Это простая система миграций: если мы добавили новое поле (например, 'bank_bik'),
    оно автоматически добавится в старую базу данных пользователя.
    """
    # Список всех возможных полей для всех типов записей
    required_columns = {
        "email": "TEXT", "url": "TEXT", "phone": "TEXT", "category": "TEXT", "tags": "TEXT",
        "notes": "TEXT", "is_favorite": "BOOLEAN DEFAULT 0", "last_used_at": "TIMESTAMP",
        "security_question": "TEXT", "security_answer": "TEXT", "recovery_email": "TEXT",
        "recovery_phone": "TEXT", "full_name": "TEXT", "date_of_birth": "TEXT", "address": "TEXT",
        "passport_number": "TEXT", "identification_number": "TEXT", "account_number": "TEXT",
        "bank_name": "TEXT", "card_number": "TEXT", "card_cvv": "TEXT", "card_expire": "TEXT",
        "card_holder": "TEXT", "card_pin": "TEXT", "card_type": "TEXT", "bank_bik": "TEXT",
        "account_type": "TEXT", "currency": "TEXT", "limit_amount": "TEXT",
        "cardholder_phone": "TEXT", "cardholder_full_name": "TEXT",
        # Поля для пользовательских типов записей
        "custom_field_1": "TEXT", "custom_field_2": "TEXT", "custom_field_3": "TEXT",
        "custom_field_4": "TEXT", "custom_field_5": "TEXT", "custom_field_6": "TEXT",
        "custom_field_7": "TEXT", "custom_field_8": "TEXT", "custom_field_9": "TEXT",
        "custom_field_10": "TEXT"
    }

    # Получаем список уже существующих колонок в БД
    cursor.execute("PRAGMA table_info(passwords)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    # Добавляем те, которых не хватает
    for col, dtype in required_columns.items():
        if col not in existing_columns:
            try:
                cursor.execute(
                    f"ALTER TABLE passwords ADD COLUMN {col} {dtype}")
            except:
                pass


def get_encryption_key():
    """
    Загружает или генерирует ключ шифрования (Fernet).
    Ключ хранится в файле encryption.key.
    ВНИМАНИЕ: Потеря этого файла означает потерю доступа ко всем паролям!
    """
    try:
        # Пытаемся прочитать существующий ключ
        with open('encryption.key', 'rb') as f:
            return f.read()
    except FileNotFoundError:
        # Если ключа нет, генерируем новый и сохраняем его
        key = Fernet.generate_key()
        with open('encryption.key', 'wb') as f:
            f.write(key)
        return key
