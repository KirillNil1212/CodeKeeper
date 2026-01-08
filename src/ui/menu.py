import tkinter as tk
from tkinter import Menu


def create_main_menu(app):
    """
    Создает и настраивает главное меню приложения (верхняя полоска).

    Аргументы:
        app: Ссылка на главный класс приложения (PasswordManager), 
             чтобы вызывать его методы (app.add_password, app.root.quit и т.д.).
    """
    menubar = Menu(app.root)
    app.root.config(menu=menubar)
    ic = app.icon_mgr  # Менеджер иконок

    # --- Меню "Файл" (File) ---
    # tearoff=0 убирает пунктирную линию отрыва
    file_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Файл", menu=file_menu)

    # Пункты меню с горячими клавишами и иконками
    file_menu.add_command(label="Новый пароль", accelerator="Ctrl+N",
                          command=app.add_password, image=ic.get("add", "small"), compound="left")
    file_menu.add_command(label="Импортировать", accelerator="Ctrl+I",
                          command=app.import_csv, image=ic.get("import", "small"), compound="left")
    file_menu.add_command(label="Экспортировать", accelerator="Ctrl+E",
                          command=app.export_csv, image=ic.get("export", "small"), compound="left")
    file_menu.add_separator()  # Разделитель
    file_menu.add_command(label="Настройки", accelerator="Ctrl+,",
                          command=app.open_settings, image=ic.get("settings", "small"), compound="left")
    file_menu.add_separator()
    file_menu.add_command(label="Выход", accelerator="Ctrl+Q",
                          command=app.root.quit, image=ic.get("exit", "small"), compound="left")

    # --- Меню "Вид" (View) ---
    view_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Вид", menu=view_menu)

    # Checkbutton позволяет ставить галочку напротив выбранного пункта
    view_menu.add_checkbutton(label="Полноэкранный режим", onvalue=True, offvalue=False, variable=app.var_fullscreen,
                              accelerator="F11", command=app.toggle_fullscreen, image=ic.get("fullscreen", "small"), compound="left")
    view_menu.add_checkbutton(label="Компактный вид", onvalue=True, offvalue=False, variable=app.var_compact,
                              command=app.toggle_compact, image=ic.get("compact", "small"), compound="left")

    # --- Меню "Данные" (Data) ---
    data_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Данные", menu=data_menu)

    # Фокусировка на поле поиска
    data_menu.add_command(label="Найти пароль", accelerator="Ctrl+F",
                          command=lambda: app.search_entry.focus_set())

    # --- Меню "Помощь" (Help) ---
    help_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Помощь", menu=help_menu)

    help_menu.add_command(label="Горячие клавиши", command=app.show_shortcuts, image=ic.get(
        "shortcuts", "small"), compound="left")
    help_menu.add_command(label="О программе", command=app.show_about, image=ic.get(
        "info", "small"), compound="left")
