import tkinter as tk
from tkinter import ttk, messagebox
import re
from datetime import datetime
from src.windows.generator import PasswordGenerator
from src.utils import darken


class AddEditPasswordWindow:
    """
    Класс окна для добавления новой записи или редактирования существующей.
    Интерфейс меняется динамически при выборе типа записи.
    """

    def __init__(self, parent, mode="add", password_id=None):
        self.parent = parent
        self.mode = mode            # "add" или "edit"
        self.password_id = password_id  # ID записи (только для edit)
        self.icon_mgr = parent.icon_mgr

        # Создаем окно, но пока скрываем
        self.window = tk.Toplevel(parent.root)
        self.window.withdraw()
        self.window.title("Новая запись" if mode ==
                          "add" else "Редактирование")
        self.icon_mgr.set_app_icon(self.window)

        # Модальный режим (окно поверх основного, блокирует его)
        self.window.transient(parent.root)
        self.window.grab_set()

        # Включаем поддержку стандартных хоткеев (Ctrl+C/V/X/A)
        self.enable_universal_shortcuts(self.window)

        # Словарь соответствия: Отображение (для юзера) -> Ключ БД (для кода)
        self.type_map = {
            "Сайт / Сервис": "WEB",
            "Оффлайн код": "OFFLINE",
            "Соц. сеть": "SOCIAL",
            "Почта": "EMAIL",
            "Банк / Счет": "BANK",
            "Банковская карта": "CARD",
            "Другое": "CUSTOM"
        }
        # Обратный словарь: Ключ БД -> Отображение (для загрузки данных)
        self.type_map_rev = {v: k for k, v in self.type_map.items()}

        self.fields = {}              # Словарь для хранения ссылок на виджеты ввода
        # Счётчик для динамических полей (тип "Другое")
        self.custom_fields_count = 0
        self.record_data = None       # Данные записи, если мы в режиме редактирования

        # Если редактируем - загружаем данные из БД
        if mode == "edit" and password_id:
            self.parent.cursor.execute(
                "SELECT * FROM passwords WHERE id=?", (password_id,))
            cols = [d[0] for d in self.parent.cursor.description]
            row = self.parent.cursor.fetchone()
            if row:
                self.record_data = dict(zip(cols, row))

        self.create_layout()
        self.center_window()

        # Если есть данные, заполняем поля
        if self.record_data:
            self.fill_data()

        self.window.deiconify()
        self.parent.root.wait_window(self.window)  # Ждем закрытия окна

    def enable_universal_shortcuts(self, window):
        """Включает горячие клавиши для всех текстовых полей окна."""
        window.bind("<Control-Key>", self.handle_ctrl_key)

    def handle_ctrl_key(self, event):
        """Обработчик нажатия Ctrl+..."""
        keycode = event.keycode
        widget = event.widget
        # Работаем только с полями ввода
        if not isinstance(widget, (tk.Entry, tk.Text)):
            return
        # Игнорируем обычные буквы, если это не спецкоманды
        if event.keysym in ['c', 'v', 'x', 'a', 'C', 'V', 'X', 'A']:
            return
        # Коды клавиш
        if keycode == 67:  # Ctrl+C
            self.copy_text(widget)
            return "break"
        elif keycode == 86:  # Ctrl+V
            self.paste_text(widget)
            return "break"
        elif keycode == 88:  # Ctrl+X
            self.cut_text(widget)
            return "break"
        elif keycode == 65:  # Ctrl+A
            self.select_all(widget)
            return "break"

    # --- Функции буфера обмена ---
    def copy_text(self, widget):
        try:
            if widget.select_present():
                widget.event_generate("<<Copy>>")
        except:
            pass

    def paste_text(self, widget):
        try:
            widget.event_generate("<<Paste>>")
        except:
            pass

    def cut_text(self, widget):
        try:
            widget.event_generate("<<Cut>>")
        except:
            pass

    def select_all(self, widget):
        try:
            widget.select_range(0, 'end')
            widget.icursor('end')
        except:
            pass

    def center_window(self):
        """Центрирование окна фиксированного размера 750x700."""
        w, h = 750, 700
        x = (self.window.winfo_screenwidth() // 2) - (w // 2)
        y = (self.window.winfo_screenheight() // 2) - (h // 2)
        self.window.geometry(f"{w}x{h}+{x}+{y}")
        self.window.resizable(False, False)

    def create_layout(self):
        """Создание базовой структуры окна (шапка, скролл-область, подвал)."""
        bg_col = "#2980b9" if self.mode == "add" else "#f39c12"  # Синий для Add, Оранжевый для Edit

        header = tk.Frame(self.window, bg=bg_col, height=60)
        header.pack(fill=tk.X)
        title = "➕ Добавить запись" if self.mode == "add" else "✏️ Редактирование"
        tk.Label(header, text=title, font=("Arial", 14, "bold"),
                 bg=bg_col, fg="white").pack(pady=15)

        # Панель выбора типа
        top_frame = tk.Frame(self.window, bg="#ecf0f1", pady=10)
        top_frame.pack(fill=tk.X)
        left_f = tk.Frame(top_frame, bg="#ecf0f1")
        left_f.pack(side=tk.LEFT, padx=20)
        tk.Label(left_f, text="Тип записи:", font=(
            "Arial", 10, "bold"), bg="#ecf0f1").pack(side=tk.LEFT, padx=5)

        # Используем русские ключи для комбобокса
        types = list(self.type_map.keys())
        self.type_var_display = tk.StringVar(value=types[0])

        type_cb = ttk.Combobox(
            left_f, textvariable=self.type_var_display, values=types, state="readonly", width=20)
        type_cb.pack(side=tk.LEFT, padx=5)

        right_f = tk.Frame(top_frame, bg="#ecf0f1")
        right_f.pack(side=tk.RIGHT, padx=20)
        self.is_favorite_var = tk.BooleanVar()
        tk.Checkbutton(right_f, text="★ В избранное", variable=self.is_favorite_var,
                       bg="#ecf0f1", font=("Arial", 10)).pack(side=tk.RIGHT)

        # Если режим Edit - запрещаем менять тип записи
        if self.mode == "edit":
            type_cb.config(state="disabled")
        else:
            # Иначе при смене типа перерисовываем поля
            type_cb.bind('<<ComboboxSelected>>', self.refresh_fields)

        # Область с прокруткой (Canvas) для полей ввода
        container = tk.Frame(self.window)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 0))
        self.canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            container, orient="vertical", command=self.canvas.yview)

        # Сюда будем добавлять Entry, Label и т.д.
        self.form_frame = tk.Frame(self.canvas)

        self.canvas.create_window((0, 0), window=self.form_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Автонастройка скролла при изменении размера
        self.form_frame.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))

        # Поддержка колесика мыши для скролла
        self.window.bind_all("<MouseWheel>", self._on_mousewheel)
        self.window.bind(
            "<Destroy>", lambda e: self.window.unbind_all("<MouseWheel>"))

        # Кнопки Сохранить / Отмена
        btn_frame = tk.Frame(self.window, bg="#ecf0f1", pady=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        save_img = self.icon_mgr.get("confirm", "small")
        close_img = self.icon_mgr.get("close", "small")
        c_save, c_cancel = "#27ae60", "#e74c3c"

        tk.Button(btn_frame, text="Сохранить", image=save_img if save_img else None, compound="left",
                  bg=c_save, activebackground=darken(c_save), fg="white", width=150 if save_img else 15, font=("Arial", 10, "bold"), command=self.save, cursor="hand2").pack(side=tk.LEFT, padx=(250, 10))

        tk.Button(btn_frame, text="Отмена", image=close_img if close_img else None, compound="left",
                  bg=c_cancel, activebackground=darken(c_cancel), fg="white", width=150 if close_img else 15, font=("Arial", 10), command=self.window.destroy, cursor="hand2").pack(side=tk.LEFT)

        if self.mode == "add":
            self.refresh_fields()

    def _on_mousewheel(self, event):
        """Прокрутка колесиком мыши."""
        if self.window.focus_displayof():
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def refresh_fields(self, event=None):
        """
        Полная перерисовка полей ввода.
        Вызывается при смене типа записи в Combobox.
        """
        # Удаляем все старые поля
        for w in self.form_frame.winfo_children():
            w.destroy()
        self.fields.clear()

        # Получаем реальный код типа (WEB, BANK...)
        ptype = self.type_map.get(self.type_var_display.get(), "WEB")

        # --- КАРТА ПОЛЕЙ (LAYOUT MAP) ---
        # Описывает структуру формы для каждого типа записи.
        # Формат: [ [ (поле, метка, обязательность, тип_валидации), ... ], ... ]
        # обязательность: 2=critical (красный), 1=important (оранжевый), 0=normal
        layout_map = {
            "WEB": [[("name", "★ Название сайта", 2, "entry_name_50")], [("username", "★ Логин", 2, "entry_login_20"), ("password", "★ Пароль", 2, "password_row")], [("url", "◆ Веб-адрес", 1, "entry"), ("email", "◆ Email аккаунта", 1, "entry_email_20")], [("phone", "○ Телефон", 0, "entry_phone"), ("category", "○ Категория", 0, "entry_category_10")], [("security_question", "○ Вопрос безопасности", 0, "entry_sec_30"), ("security_answer", "○ Ответ", 0, "entry_sec_30")], [("recovery_email", "○ Резервный Email", 0, "entry_email_20"), ("recovery_phone", "○ Рез. Телефон", 0, "entry_phone")], [("notes", "○ Примечания", 0, "text_notes_60")]],
            "OFFLINE": [[("name", "★ Название кода", 2, "entry_name_strict_20")], [("password", "★ Код / Текст", 2, "text_password")], [("tags", "○ Теги", 0, "entry_category_10"), ("category", "○ Категория", 0, "entry_category_10")], [("notes", "○ Примечания", 0, "text_notes_60")]],
            "SOCIAL": [[("name", "★ Соц. сеть", 2, "entry_name_50")], [("username", "★ Никнейм", 2, "entry_login_20"), ("password", "★ Пароль", 2, "password_row")], [("email", "◆ Email аккаунта", 1, "entry_email_20"), ("url", "◆ Ссылка на профиль", 1, "entry")], [("phone", "○ Телефон", 0, "entry_phone"), ("full_name", "○ ФИО", 0, "entry")], [("recovery_email", "○ Email восст.", 0, "entry_email_20"), ("recovery_phone", "○ Тел. восст.", 0, "entry_phone")], [("notes", "○ Примечания", 0, "text_notes_60")]],
            "EMAIL": [[("name", "★ Название почты", 2, "entry_name_50")], [("username", "★ Email адрес", 2, "entry_email_20"), ("password", "★ Пароль", 2, "password_row")], [("phone", "◆ Телефон", 1, "entry_phone"), ("full_name", "◆ ФИО владельца", 1, "entry")], [("date_of_birth", "○ Дата рождения", 0, "entry_date_full"), ("recovery_email", "○ Рез. Email", 0, "entry_email_20")], [("security_question", "○ Вопрос безопасности", 0, "entry_sec_30"), ("security_answer", "○ Ответ", 0, "entry_sec_30")], [("notes", "○ Примечания", 0, "text_notes_60")]],
            "BANK": [[("name", "★ Название счета", 2, "entry_name_strict_20")], [("username", "★ Логин/Договор", 2, "entry_login_20"), ("password", "★ Пароль", 2, "password_row")], [("account_number", "★ Номер счета (20)", 2, "entry_account"), ("bank_name", "◆ Банк", 1, "entry")], [("card_number", "◆ Привязанная карта", 1, "entry_card"), ("phone", "◆ Телефон", 1, "entry_phone")], [("bank_bik", "○ БИК (9)", 0, "entry_bik"), ("currency", "○ Валюта", 0, "entry")], [("full_name", "○ ФИО владельца", 0, "entry"), ("date_of_birth", "○ Дата рождения", 0, "entry_date_full")], [("identification_number", "○ ИНН/ID", 0, "entry"), ("address", "○ Адрес", 0, "entry")], [("notes", "○ Примечания", 0, "text_notes_60")]],
            "CARD": [[("name", "★ Название карты", 2, "entry_name_strict_20")], [("card_number", "★ Номер карты", 2, "entry_card")], [("card_cvv", "★ CVV/CVC", 2, "entry_cvv"), ("card_expire", "★ Срок (MM/YY)", 2, "entry_date")], [("card_holder", "◆ Владелец", 1, "entry"), ("bank_name", "◆ Банк", 1, "entry")], [("card_pin", "○ PIN код", 0, "password_simple"), ("card_type", "○ Тип", 0, "entry")], [("cardholder_phone", "○ Телефон", 0, "entry_phone"), ("limit_amount", "○ Лимит", 0, "entry")], [("passport_number", "○ Паспорт", 0, "entry"), ("currency", "○ Валюта", 0, "entry")], [("notes", "○ Примечания", 0, "text_notes_60")]],
            "CUSTOM": [[("name", "★ Название", 2, "entry_name_50")], [("username", "★ Поле 1 (Логин)", 2, "entry"), ("password", "★ Поле 2 (Пароль)", 2, "password_row")], [("custom_field_1", "○ Поле 1", 0, "entry"), ("custom_field_2", "○ Поле 2", 0, "entry")]]
        }

        rows = layout_map.get(ptype, [])
        for i, r in enumerate(rows):
            self.create_row(i, r)

        # Для типа "Другое" добавляем кнопку "Добавить поле"
        if ptype == "CUSTOM":
            self.custom_fields_count = 2
            self.create_add_field_button()
            self.create_row(
                999, [("notes", "○ Примечания", 0, "text_notes_60")])

    def create_add_field_button(self):
        """Кнопка для динамического добавления полей (только для CUSTOM)."""
        f = tk.Frame(self.form_frame, pady=5)
        rows_count = self.form_frame.grid_size()[1]
        f.grid(row=rows_count, column=0, columnspan=2, sticky="ew")
        add_icon = self.icon_mgr.get("add", "small")
        tk.Button(f, text=" Добавить новое поле", image=add_icon if add_icon else None, compound="left",
                  command=self.add_custom_field, bg="#bdc3c7", fg="#2c3e50", cursor="hand2").pack()

    def add_custom_field(self):
        """Логика добавления нового поля (до 10 штук)."""
        if self.custom_fields_count >= 10:
            return
        self.custom_fields_count += 1

        # Сохраняем текущие значения, чтобы не потерять при перерисовке
        current_vals = {}
        for k, w in self.fields.items():
            if isinstance(w, tk.Entry):
                current_vals[k] = w.get()
            elif isinstance(w, tk.Text):
                current_vals[k] = w.get("1.0", tk.END)

        # Очищаем форму
        for w in self.form_frame.winfo_children():
            w.destroy()
        self.fields.clear()

        # Пересобираем структуру строк
        rows = [[("name", "★ Название", 2, "entry_name_50")], [
            ("username", "★ Поле 1", 2, "entry"), ("password", "★ Поле 2", 2, "password_row")]]
        custom_rows = []
        temp_row = []
        for i in range(1, self.custom_fields_count + 1):
            temp_row.append((f"custom_field_{i}", f"○ Поле {i}", 0, "entry"))
            if len(temp_row) == 2:
                custom_rows.append(temp_row)
                temp_row = []
        if temp_row:
            custom_rows.append(temp_row)
        rows.extend(custom_rows)

        # Рисуем заново
        for i, r in enumerate(rows):
            self.create_row(i, r)
        self.create_add_field_button()
        self.create_row(999, [("notes", "○ Примечания", 0, "text_notes_60")])

        # Восстанавливаем значения
        for k, val in current_vals.items():
            if k in self.fields:
                w = self.fields[k]
                if isinstance(w, tk.Entry):
                    w.insert(0, val)
                elif isinstance(w, tk.Text):
                    w.insert("1.0", val.strip())

    def create_row(self, r_idx, fields_data):
        """Создает одну строку с 1 или 2 полями ввода."""
        current_rows = self.form_frame.grid_size()[1]
        self.form_frame.columnconfigure(0, weight=1)
        self.form_frame.columnconfigure(1, weight=1)

        for c_idx, (key, lbl, req, ftype) in enumerate(fields_data):
            frame = tk.Frame(self.form_frame, padx=5, pady=5)
            span = 2 if len(fields_data) == 1 else 1
            r = current_rows if r_idx == 999 else current_rows + 1
            if r_idx != 999:
                r = r_idx
            frame.grid(row=r, column=c_idx, sticky="new", columnspan=span)

            # Цвет метки в зависимости от обязательности
            color = "#e74c3c" if req == 2 else (
                "#f39c12" if req == 1 else "#7f8c8d")
            tk.Label(frame, text=lbl, font=("Arial", 9, "bold"),
                     fg=color).pack(anchor="w")

            validate_cmd = None
            hint_text = ""

            # --- Настройка валидаторов для Entry ---
            if ftype == "entry_name_50":
                validate_cmd = (self.window.register(
                    lambda P: len(P) <= 50), '%P')
            elif ftype == "entry_name_strict_20":
                validate_cmd = (self.window.register(
                    self.validate_strict_20), '%P')
            elif ftype == "entry_login_20":
                validate_cmd = (self.window.register(
                    lambda P: len(P) <= 20), '%P')
            elif ftype == "entry_email_20":
                validate_cmd = (self.window.register(
                    lambda P: len(P) <= 20), '%P')
            elif ftype == "entry_category_10":
                validate_cmd = (self.window.register(
                    self.validate_strict_10), '%P')
            elif ftype == "entry_sec_30":
                validate_cmd = (self.window.register(
                    lambda P: len(P) <= 30), '%P')
            elif ftype == "entry_numeric":
                validate_cmd = (self.window.register(
                    self.validate_numeric), '%P')
            elif ftype == "entry_card":
                validate_cmd = (self.window.register(self.validate_card), '%P')
                hint_text = "Пример: 16-19 цифр"
            elif ftype == "entry_cvv":
                validate_cmd = (self.window.register(self.validate_cvv), '%P')
            elif ftype == "entry_date":
                validate_cmd = (self.window.register(self.validate_date), '%P')
                hint_text = "ММ/ГГ"
            elif ftype == "entry_date_full":
                validate_cmd = (self.window.register(
                    self.validate_date_full), '%P')
                hint_text = "Пример: 01.01.2000"
            elif ftype == "entry_phone":
                validate_cmd = (self.window.register(
                    self.validate_phone_input), '%P')
                hint_text = "+7 (xxx) xxx-xx-xx"
            elif ftype == "entry_account":
                validate_cmd = (self.window.register(
                    self.validate_account), '%P')
                hint_text = "Ровно 20 цифр"
            elif ftype == "entry_bik":
                validate_cmd = (self.window.register(self.validate_bik), '%P')
                hint_text = "Ровно 9 цифр"

            # --- Создание виджета (Entry или Text) ---
            if "entry" in ftype:
                w = tk.Entry(frame, relief="solid", bd=1,
                             validate="key" if validate_cmd else "none", validatecommand=validate_cmd)
                w.pack(fill=tk.X, ipady=3)
                self.fields[key] = w

                # Привязка подсветки цветом
                w.bind('<KeyRelease>', lambda e, k=key, t=ftype,
                       wg=w: self.validate_field_color(wg, k, t))
                if ftype == "entry_date_full":
                    w.bind('<KeyRelease>', self.format_date_input)
                if ftype == "entry_phone":
                    w.bind('<FocusIn>', self.format_phone_focus)
                if hint_text:
                    tk.Label(frame, text=hint_text, font=(
                        "Arial", 7), fg="gray").pack(anchor="w")

            elif "password" in ftype:
                pf = tk.Frame(frame)
                pf.pack(fill=tk.X)
                w = tk.Entry(pf, show="•", relief="solid", bd=1,
                             validate="key" if validate_cmd else "none", validatecommand=validate_cmd)
                w.pack(side="left", fill="x", expand=1, ipady=3)

                eye_img = self.icon_mgr.get("show", "small")
                gen_img = self.icon_mgr.get("key", "small")

                tk.Button(pf, image=eye_img if eye_img else None, text="👁" if not eye_img else "",
                          width=30 if eye_img else 3, command=lambda e=w: self.toggle_vis(e), cursor="hand2").pack(side="left")
                if "row" in ftype:
                    tk.Button(pf, image=gen_img if gen_img else None, text="🎲" if not gen_img else "", width=30 if gen_img else 3,
                              command=lambda e=w: PasswordGenerator(self.parent, target_entry=e), cursor="hand2").pack(side="left")
                self.fields[key] = w
            elif "text" in ftype:
                h_val = 4
                if "notes" in ftype:
                    h_val = 3
                w = tk.Text(frame, height=h_val, relief="solid", bd=1)
                w.pack(fill=tk.X)
                self.fields[key] = w
                if "60" in ftype:
                    w.bind('<KeyRelease>',
                           lambda e: self.limit_text_length(e.widget, 60))

    # --- Функции валидации (возвращают True/False) ---
    def validate_numeric(self, P): return P.isdigit() or P == ""

    def validate_card(self, P): return (
        P.isdigit() or P == "") and len(P) <= 19
    def validate_account(self, P): return (
        P.isdigit() or P == "") and len(P) <= 20

    def validate_bik(self, P): return (P.isdigit() or P == "") and len(P) <= 9
    def validate_cvv(self, P): return (P.isdigit() or P == "") and len(P) <= 4
    def validate_date(self, P): return len(P) <= 5
    def validate_date_full(self, P): return len(P) <= 10

    def validate_phone_input(self, P):
        digits = "".join(filter(str.isdigit, P))
        if len(digits) > 11:
            return False
        return all(c in "0123456789+()- " for c in P)

    def validate_strict_10(self, P): return (len(P) <= 10) and (
        P == "" or bool(re.match(r'^[a-zA-Zа-яА-Я0-9\-_]+$', P)))

    def validate_strict_20(self, P): return (len(P) <= 20) and (
        P == "" or bool(re.match(r'^[a-zA-Zа-яА-Я0-9\-_]+$', P)))

    def limit_text_length(self, widget, limit):
        text = widget.get("1.0", "end-1c")
        if len(text) > limit:
            widget.delete("1.0", tk.END)
            widget.insert("1.0", text[:limit])

    def validate_field_color(self, widget, key, ftype):
        """Меняет цвет фона поля: белый (ОК) или красный (Ошибка)."""
        val = widget.get()
        valid = True
        if not val:
            widget.config(bg="white")
            return
        if "email" in ftype:
            valid = bool(
                re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", val))
        elif ftype == "entry_phone":
            digits = "".join(filter(str.isdigit, val))
            valid = len(digits) >= 10
        elif ftype == "entry_bik":
            valid = len(val) == 9
        elif ftype == "entry_account":
            valid = len(val) == 20
        elif ftype == "entry_card":
            valid = len(val) >= 13
        elif ftype == "entry_date_full":
            valid = len(val) == 10
        widget.config(bg="white" if valid else "#fadbd8")
        if ftype == "entry_date_full":
            self.format_date_input_logic(widget)

    def format_date_input(
        self, event): self.format_date_input_logic(event.widget)

    def format_date_input_logic(self, entry):
        text = entry.get()
        if len(text) == 2 or len(text) == 5:
            entry.insert(tk.END, ".")

    def format_phone_focus(self, event):
        entry = event.widget
        if not entry.get():
            entry.insert(0, "+7 ")

    def toggle_vis(self, e): e.config(
        show='' if e.cget('show') == '•' else '•')

    def fill_data(self):
        """Заполняет поля данными из БД при открытии в режиме Edit."""
        d = self.record_data
        # Конвертируем WEB -> Сайт / Сервис для отображения
        display_type = self.type_map_rev.get(d['type'], "Сайт / Сервис")
        self.type_var_display.set(display_type)

        if d.get('is_favorite'):
            self.is_favorite_var.set(True)
        if d['type'] == 'CUSTOM':
            max_idx = 0
            for i in range(1, 11):
                if d.get(f'custom_field_{i}'):
                    max_idx = i
            self.custom_fields_count = max(2, max_idx)
            self.refresh_fields()
            if self.custom_fields_count > 2:
                count_needed = self.custom_fields_count
                self.custom_fields_count = 2
                while self.custom_fields_count < count_needed:
                    self.add_custom_field()
        else:
            self.refresh_fields()
        encrypted_fields = ["password", "card_number", "card_cvv",
                            "card_pin", "security_answer", "account_number", "passport_number"]
        for key, widget in self.fields.items():
            val = d.get(key)
            if not val:
                continue
            if key in encrypted_fields:
                try:
                    val = self.parent.decrypt_password(val)
                except:
                    pass
            if isinstance(widget, tk.Text):
                widget.delete("1.0", tk.END)
                widget.insert("1.0", str(val))
            elif isinstance(widget, tk.Entry):
                widget.delete(0, tk.END)
                widget.insert(0, str(val))

    def save(self):
        """Сохранение записи в базу данных."""
        data = {}
        for k, w in self.fields.items():
            if isinstance(w, tk.Entry):
                data[k] = w.get().strip()
            elif isinstance(w, tk.Text):
                data[k] = w.get("1.0", tk.END).strip()

        # Получаем реальный код типа (WEB) для сохранения
        ptype = self.type_map.get(self.type_var_display.get(), "WEB")

        if not data.get("name"):
            messagebox.showerror("Ошибка", "Поле 'Название' обязательно!")
            return
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        for k in ["email", "recovery_email", "username"]:
            if ptype == "EMAIL" and k == "username":
                if data.get(k) and not re.match(email_regex, data.get(k)):
                    messagebox.showerror("Ошибка", "Некорректный Email адрес!")
                    return
            elif "email" in k and data.get(k):
                if not re.match(email_regex, data.get(k)):
                    messagebox.showerror("Ошибка", f"Некорректный {k}!")
                    return
        for k in ["phone", "recovery_phone", "cardholder_phone"]:
            ph = data.get(k)
            if ph:
                digits = "".join(filter(str.isdigit, ph))
                if len(digits) < 10:
                    messagebox.showerror(
                        "Ошибка", "Номер телефона слишком короткий!")
                    return
        if data.get("date_of_birth"):
            try:
                datetime.strptime(data.get("date_of_birth"), "%d.%m.%Y")
            except ValueError:
                messagebox.showerror(
                    "Ошибка", "Дата рождения должна быть в формате ДД.ММ.ГГГГ")
                return
        if ptype == "BANK":
            bik = data.get("bank_bik", "")
            acc = data.get("account_number", "")
            if bik and len(bik) != 9:
                messagebox.showerror(
                    "Ошибка", "БИК должен состоять из 9 цифр!")
                return
            if acc and len(acc) != 20:
                messagebox.showerror(
                    "Ошибка", "Номер счета должен состоять из 20 цифр!")
                return
        if ptype == "CARD":
            cn = data.get("card_number", "")
            cvv = data.get("card_cvv", "")
            exp = data.get("card_expire", "")
            if not cn or len(cn) < 13:
                messagebox.showerror("Ошибка", "Номер карты некорректен!")
                return
            if not cvv or len(cvv) < 3:
                messagebox.showerror("Ошибка", "CVV некорректен!")
                return
            if not exp or "/" not in exp:
                messagebox.showerror("Ошибка", "Срок действия некорректен!")
                return
        pwd = data.get("password", "")
        if self.parent.config['notify_weak'] and pwd and len(pwd) < 8:
            if not messagebox.askyesno("Слабый пароль", "Внимание: Пароль короче 8 символов. Все равно сохранить?"):
                return
        encrypted_fields = ["password", "card_number", "card_cvv",
                            "card_pin", "security_answer", "account_number", "passport_number"]
        for f in encrypted_fields:
            if data.get(f):
                data[f] = self.parent.encrypt_password(data[f])

        # Полный список всех возможных колонок в БД
        all_possible_columns = ["name", "username", "password", "type", "url", "email", "phone", "category", "tags", "notes", "is_favorite", "security_question", "security_answer", "recovery_email", "recovery_phone", "full_name", "date_of_birth", "address", "passport_number", "account_number", "bank_name", "card_number", "card_cvv", "card_expire",
                                "card_holder", "card_pin", "card_type", "bank_bik", "account_type", "currency", "limit_amount", "cardholder_phone", "cardholder_full_name", "identification_number", "custom_field_1", "custom_field_2", "custom_field_3", "custom_field_4", "custom_field_5", "custom_field_6", "custom_field_7", "custom_field_8", "custom_field_9", "custom_field_10"]

        insert_cols = []
        insert_vals = []
        update_set = []
        now = datetime.now()
        data['type'] = ptype
        data['is_favorite'] = 1 if self.is_favorite_var.get() else 0

        if self.mode == "add":
            data['created_at'] = now
            for col in all_possible_columns + ['created_at']:
                if col in data:
                    insert_cols.append(col)
                    insert_vals.append(data[col])
            sql = f"INSERT INTO passwords ({','.join(insert_cols)}) VALUES ({','.join(['?']*len(insert_cols))})"
            self.parent.cursor.execute(sql, tuple(insert_vals))
        else:
            data['updated_at'] = now
            for col in all_possible_columns + ['updated_at']:
                if col in data:
                    update_set.append(f"{col}=?")
                    insert_vals.append(data[col])
            insert_vals.append(self.password_id)
            sql = f"UPDATE passwords SET {','.join(update_set)} WHERE id=?"
            self.parent.cursor.execute(sql, tuple(insert_vals))

        self.parent.conn.commit()
        self.parent.load_passwords()
        self.window.destroy()
        messagebox.showinfo("Успех", "Сохранено!")
