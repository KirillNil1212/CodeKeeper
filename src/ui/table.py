import tkinter as tk
from tkinter import ttk, Menu, messagebox
from datetime import datetime
from src.windows.details import DetailModal
from src.windows.add_edit import AddEditPasswordWindow


class UITable:
    """
    Компонент таблицы паролей (Treeview).
    Отвечает за:
    - Построение таблицы и колонок
    - Загрузку данных из БД с фильтрацией
    - Обработку кликов (выделение, копирование)
    - Контекстное меню (ПКМ)
    """

    def __init__(self, app):
        self.app = app
        # Множество ID выбранных записей (для множественного выбора)
        self.checked_items = set()

        # Фрейм-контейнер для таблицы и скроллбара
        self.frame = tk.Frame(app.root)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self._build_table()         # Создание колонок
        self._build_scrollbar()     # Создание скроллбара
        self._build_context_menu()  # Создание меню ПКМ
        self._bind_events()         # Привязка событий мыши

    def _build_table(self):
        """Настройка колонок Treeview."""
        cols = ["check", "type", "name", "login", "category"]
        # Колонка пароля отображается только если включена настройка
        if self.app.config['show_passwords_table']:
            cols.append("password_col")
        cols.append("date")

        self.tree = ttk.Treeview(self.frame, columns=tuple(
            cols), show="headings", selectmode="browse")

        # Настройка заголовков (текст и обработчики кликов)
        # Клик по чекбоксу в шапке
        self.tree.heading("check", text="☐", command=self.toggle_all_checks)
        self.tree.heading("type", text="Тип")
        self.tree.heading("name", text="Название")
        self.tree.heading("login", text="Логин")
        self.tree.heading("category", text="Категория")
        self.tree.heading("date", text="Дата")
        if self.app.config['show_passwords_table']:
            self.tree.heading("password_col", text="Пароль")

        # Настройка ширины и выравнивания колонок
        self.tree.column("check", width=40, minwidth=40,
                         anchor="center", stretch=False)
        self.tree.column("type", width=80, minwidth=80,
                         anchor="center", stretch=False)
        self.tree.column("name", width=150, minwidth=100,
                         anchor="w", stretch=True)
        self.tree.column("login", width=150, minwidth=100,
                         anchor="w", stretch=True)
        self.tree.column("category", width=90, minwidth=80,
                         anchor="center", stretch=False)
        self.tree.column("date", width=90, minwidth=90,
                         anchor="center", stretch=False)
        if self.app.config['show_passwords_table']:
            self.tree.column("password_col", width=120,
                             minwidth=100, anchor="w", stretch=True)

        # Тег для подсветки старых паролей (красный фон)
        self.tree.tag_configure("expired", background="#fadbd8")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _build_scrollbar(self):
        """Добавляет вертикальную полосу прокрутки."""
        scrollbar = ttk.Scrollbar(
            self.frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

    def _build_context_menu(self):
        """Создает контекстное меню (появляется при клике ПКМ)."""
        self.context_menu = Menu(self.app.root, tearoff=0)
        ic = self.app.icon_mgr

        self.context_menu.add_command(label="Добавить запись", command=self.app.add_password, image=ic.get(
            "add", "small"), compound="left")
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Просмотреть", command=lambda: self.on_double_click(
            None), image=ic.get("view", "small"), compound="left")
        self.context_menu.add_command(label="Редактировать", command=self.app.edit_password, image=ic.get(
            "edit", "small"), compound="left")
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Копировать пароль", command=self._ctx_copy_pass, image=ic.get(
            "copy_pass", "small"), compound="left")
        self.context_menu.add_command(label="Копировать логин", command=self._ctx_copy_login, image=ic.get(
            "copy_login", "small"), compound="left")
        self.context_menu.add_separator()
        self.context_menu.add_command(label="⭐ Избранное", command=self._ctx_toggle_fav, image=ic.get(
            "favorite", "small"), compound="left")
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Удалить", command=self.app.delete_password, image=ic.get(
            "delete", "small"), compound="left")

    def _bind_events(self):
        """Привязывает обработчики событий мыши."""
        self.tree.bind(
            # ЛКМ (выделение, копирование)
            "<Button-1>", self.on_click)
        # Двойной клик (просмотр)
        self.tree.bind("<Double-1>", self.on_double_click)
        # ПКМ (контекстное меню)
        self.tree.bind("<Button-3>", self.show_context_menu)
        # Перетаскивание (запрет изменения ширины разделителей мышью)
        self.tree.bind('<B1-Motion>', self._handle_drag)
        # Авто-ширина по двойному клику на разделитель
        self.tree.bind('<Double-1>', self._handle_header_double_click)

        # Эффект "подглядывания" пароля при наведении мыши
        if self.app.config['show_passwords_table']:
            self.tree.bind("<Motion>", self._on_hover)

    # --- ПУБЛИЧНЫЕ МЕТОДЫ (вызываются из app.py) ---

    def reload_data(self):
        """
        Основной метод загрузки данных.
        1. Считывает фильтры из app.search_entry и app.filter_combobox.
        2. Формирует SQL запрос.
        3. Очищает таблицу и заполняет новыми данными.
        """
        # Считывание фильтров
        search = self.app.search_entry.get().lower()
        if search == "поиск...":
            search = ""

        ptype_display = self.app.filter_combobox.get()
        ptype = self.app.type_map_filter.get(ptype_display, "Все")
        sort_val = self.app.sort_combobox.get()

        # Формирование сортировки SQL
        order_by = "created_at DESC"
        if sort_val == "Дата изменения (новые)":
            order_by = "updated_at DESC"
        elif sort_val == "Дата изменения (старые)":
            order_by = "updated_at ASC"
        elif sort_val == "Название (А→Я) ↑":
            order_by = "name ASC"
        elif sort_val == "Название (Я→А) ↓":
            order_by = "name DESC"
        elif sort_val == "Логин (А→Я) ↑":
            order_by = "username ASC"
        elif sort_val == "Логин (Я→А) ↓":
            order_by = "username DESC"
        elif sort_val == "Последнее использование (недавние)":
            order_by = "last_used_at DESC"
        elif sort_val == "Последнее использование (давние)":
            order_by = "last_used_at ASC"
        elif sort_val == "Избранные в начале":
            order_by = "is_favorite DESC, name ASC"
        elif sort_val == "Избранные в конце":
            order_by = "is_favorite ASC, name ASC"

        # Очистка текущих данных
        self.tree.delete(*self.tree.get_children())

        # Сборка SQL запроса
        query = "SELECT type, name, username, email, category, created_at, id, is_favorite, updated_at FROM passwords WHERE 1=1"
        params = []
        if ptype != "Все":
            query += " AND type=?"
            params.append(ptype)
        if search:
            query += " AND (lower(name) LIKE ? OR lower(username) LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        query += f" ORDER BY {order_by}"

        self.app.cursor.execute(query, params)
        now = datetime.now()

        # Заполнение таблицы строками
        for row in self.app.cursor.fetchall():
            ptype, name, user, email, cat, date, pid, is_fav, updated_at = row

            display_ptype = self.app.type_map_display.get(ptype, ptype)
            login = user if user else (email if email else "-")
            d_date = date.split()[0] if date else "-"
            display_name = ("★ " + name) if is_fav else name

            # Теги для строки (ID записи и статус просроченности)
            tags = [str(pid)]
            if self.app.config['notify_expired'] and updated_at:
                try:
                    dt = datetime.strptime(updated_at.split('.')[
                                           0], "%Y-%m-%d %H:%M:%S")
                    if (now - dt).days > 365:
                        tags.append("expired")
                except:
                    pass

            row_vals = [("☑" if pid in self.checked_items else "☐"),
                        display_ptype, display_name, login, cat or "-"]

            if self.app.config['show_passwords_table']:
                row_vals.append("••••••••")  # Пароль скрыт точками
            row_vals.append(d_date)

            self.tree.insert("", tk.END, values=row_vals, tags=tuple(tags))

        self.update_status_bar()

    def clear_selection(self):
        """Полностью снимает выделение со всех строк."""
        self.tree.selection_remove(self.tree.selection())
        self.checked_items.clear()
        # Визуально снимаем галочки
        for i in self.tree.get_children():
            vals = list(self.tree.item(i, "values"))
            if vals[0] != "☐":
                vals[0] = "☐"
                self.tree.item(i, values=vals)
        self.tree.heading("check", text="☐")
        self.update_status_bar()

    def toggle_all_checks(self):
        """Переключатель 'Выбрать все / Снять все' в заголовке таблицы."""
        all_items = self.tree.get_children()
        all_ids = [int(self.tree.item(i, "tags")[0]) for i in all_items]

        # Если уже все выбрано -> Снимаем выбор
        if len(self.checked_items) == len(all_ids) and len(all_ids) > 0:
            self.checked_items.clear()
            sym = "☐"
        else:  # Иначе -> Выбираем все
            self.checked_items = set(all_ids)
            sym = "☑"

        self.tree.heading("check", text=sym)
        for i in all_items:
            vals = list(self.tree.item(i, "values"))
            vals[0] = sym
            self.tree.item(i, values=vals)
        self.update_status_bar()

    def update_status_bar(self):
        """Обновляет текст внизу (кол-во записей, последнее изменение) и активирует кнопки."""
        total = len(self.tree.get_children())
        selected = len(self.checked_items)

        # Получаем дату последнего изменения БД
        self.app.cursor.execute(
            "SELECT COALESCE(updated_at, created_at) as last_mod FROM passwords ORDER BY last_mod DESC LIMIT 1")
        res = self.app.cursor.fetchone()

        last_change = "нет данных"
        if res and res[0]:
            try:
                dt = datetime.strptime(
                    res[0].split('.')[0], "%Y-%m-%d %H:%M:%S")
                diff = datetime.now() - dt
                mins = int(diff.total_seconds() / 60)
                if mins < 1:
                    last_change = "только что"
                elif mins < 60:
                    last_change = f"{mins} мин назад"
                elif mins < 1440:
                    last_change = f"{mins//60} ч назад"
                else:
                    last_change = f"{mins//1440} дн назад"
            except:
                pass

        self.app.status_bar.config(
            text=f"Статус: {total} записей | Выбрано: {selected} | Последнее изменение: {last_change}")

        # Активация/деактивация кнопок в Toolbar (через ссылку на app)
        if hasattr(self.app, 'ui_toolbar'):
            # Редактировать можно только 1 запись
            state = "normal" if selected == 1 else "disabled"
            self.app.btn_edit.config(state=state)

            # Удалять можно сколько угодно
            del_text = " Удалить"
            if selected > 0:
                del_text += f" ({selected})"
            self.app.btn_del.config(text=del_text)

    # --- ОБРАБОТЧИКИ СОБЫТИЙ (CLICKS) ---

    def on_click(self, event):
        """Обработка клика ЛКМ по таблице."""
        region = self.tree.identify("region", event.x, event.y)
        if region in ["heading", "separator"]:
            return

        item_id = self.tree.identify_row(event.y)
        if not item_id:
            self.clear_selection()
            return

        col = self.tree.identify_column(event.x)
        col_idx = int(col.replace("#", ""))

        # 1. Если клик по колонке "Логин" -> Копируем логин
        if col_idx == 4:
            val = self.tree.item(item_id, "values")[3]
            if val and val != "-":
                self.app._copy_to_clip(val)
                self.app.show_tooltip(
                    event.x_root, event.y_root, "Логин скопирован!")
                self.app.update_last_used(
                    int(self.tree.item(item_id, "tags")[0]))
                return

        # 2. Если клик по колонке "Пароль" -> Копируем пароль (с проверкой мастер-пароля)
        if self.app.config['show_passwords_table'] and "password_col" in self.tree["columns"]:
            pass_idx = self.tree["columns"].index("password_col") + 1
            if col_idx == pass_idx and self.app.verify_master_password():
                pid = int(self.tree.item(item_id)['tags'][0])
                self.app.cursor.execute(
                    "SELECT password FROM passwords WHERE id=?", (pid,))
                res = self.app.cursor.fetchone()
                if res and res[0]:
                    self.app._copy_to_clip(self.app.decrypt_password(res[0]))
                    self.app.show_tooltip(
                        event.x_root, event.y_root, "Скопировано!")
                    self.app.update_last_used(pid)
                return

        # 3. Иначе -> Выделение строки галочкой
        record_id = int(self.tree.item(item_id, "tags")[0])
        vals = list(self.tree.item(item_id, "values"))

        if record_id in self.checked_items:
            self.checked_items.remove(record_id)
            vals[0] = "☐"
        else:
            self.checked_items.add(record_id)
            vals[0] = "☑"

        self.tree.item(item_id, values=vals)
        self.update_status_bar()

    def on_double_click(self, event):
        """Двойной клик открывает окно деталей."""
        if event and self.tree.identify_region(event.x, event.y) == "separator":
            return
        sel = self.tree.selection()
        if not sel:
            return
        pid = int(self.tree.item(sel[0])['tags'][0])
        DetailModal(self.app, pid)

    def show_context_menu(self, event):
        """Показ контекстного меню (ПКМ)."""
        item_id = self.tree.identify_row(event.y)
        if item_id:
            # Если кликнули по строке -> выделяем её и показываем полное меню
            self.tree.selection_set(item_id)
            self.checked_items.clear()
            pid = int(self.tree.item(item_id)['tags'][0])
            self.checked_items.add(pid)
            self.update_status_bar()
            for i in range(10):
                try:
                    self.context_menu.entryconfig(i, state="normal")
                except:
                    pass
        else:
            # Если кликнули в пустоту -> снимаем выделение, отключаем пункты редактирования
            self.clear_selection()
            for i in range(2, 20):
                try:
                    self.context_menu.entryconfig(i, state="disabled")
                except:
                    pass

        self.context_menu.post(event.x_root, event.y_root)

    # --- ВНУТРЕННИЕ МЕТОДЫ (Hover, Drag) ---

    def _on_hover(self, event):
        """Показывает расшифрованный пароль при наведении мыши (если включено)."""
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        pass_col_idx = -1
        display_cols = self.tree["columns"]

        if "password_col" in display_cols:
            pass_col_idx = display_cols.index("password_col") + 1
        col_str_idx = int(col.replace("#", "")) if col else -1

        # Если мышь над колонкой пароля
        if item and col_str_idx == pass_col_idx:
            pid = int(self.tree.item(item)['tags'][0])
            # Если это новый элемент (не тот, на котором мышь была раньше)
            if getattr(self, "last_hovered_pass", None) != (item, pid):
                self._restore_hidden_passwords()  # Скрываем предыдущий
                self.app.cursor.execute(
                    "SELECT password FROM passwords WHERE id=?", (pid,))
                res = self.app.cursor.fetchone()
                if res and res[0]:
                    try:
                        dec = self.app.decrypt_password(res[0])
                        # Показываем пароль
                        self.tree.set(item, "password_col", dec)
                        self.last_hovered_pass = (item, pid)
                    except:
                        pass
        else:
            self._restore_hidden_passwords()  # Мышь ушла - скрываем пароль

    def _restore_hidden_passwords(self):
        """Скрывает пароль точками обратно."""
        if hasattr(self, "last_hovered_pass") and self.last_hovered_pass:
            try:
                self.tree.set(
                    self.last_hovered_pass[0], "password_col", "••••••••")
            except:
                pass
            self.last_hovered_pass = None

    def _handle_drag(self, event):
        """Блокирует ручное изменение ширины колонок."""
        if self.tree.identify_region(event.x, event.y) == "separator":
            return "break"

    def _handle_header_double_click(self, event):
        """Автоматическая ширина колонки по двойному клику на разделитель."""
        if self.tree.identify("region", event.x, event.y) == "separator":
            try:
                col_id = self.tree.identify_column(event.x)
                col_name = self.tree["columns"][int(
                    col_id.replace("#", "")) - 1]
                self._autosize_column(col_name)
            except:
                pass
            return "break"
        else:
            self.on_double_click(event)

    def _autosize_column(self, col):
        """Вычисляет и устанавливает оптимальную ширину колонки по содержимому."""
        from tkinter import font
        font_obj = font.Font(font=('Arial', 12))
        max_width = font_obj.measure(col.title()) + 20
        # Проходим по всем строкам и ищем самую длинную
        for item in self.tree.get_children():
            val = self.tree.set(item, col)
            w = font_obj.measure(val) + 20
            if w > max_width:
                max_width = w
        if max_width > 400:
            max_width = 400  # Ограничение ширины
        self.tree.column(col, width=max_width)

    # --- ДЕЙСТВИЯ КОНТЕКСТНОГО МЕНЮ (Helpers) ---

    def _ctx_copy_pass(self):
        if not self.app.verify_master_password():
            return
        sel = self.tree.selection()
        if not sel:
            return
        pid = int(self.tree.item(sel[0])['tags'][0])
        self.app.cursor.execute(
            "SELECT password FROM passwords WHERE id=?", (pid,))
        res = self.app.cursor.fetchone()
        if res and res[0]:
            self.app._copy_to_clip(self.app.decrypt_password(res[0]))
            self.app.update_last_used(pid)

    def _ctx_copy_login(self):
        sel = self.tree.selection()
        if not sel:
            return
        pid = int(self.tree.item(sel[0])['tags'][0])
        self.app.cursor.execute(
            "SELECT username, email FROM passwords WHERE id=?", (pid,))
        res = self.app.cursor.fetchone()
        if res:
            login = res[0] if res[0] else (res[1] if res[1] else "")
            self.app._copy_to_clip(login)
            self.app.update_last_used(pid)

    def _ctx_toggle_fav(self):
        """Добавляет/убирает из избранного через контекстное меню."""
        sel = self.tree.selection()
        if not sel:
            return
        pid = int(self.tree.item(sel[0])['tags'][0])
        self.app.cursor.execute(
            "UPDATE passwords SET is_favorite = NOT is_favorite WHERE id=?", (pid,))
        self.app.conn.commit()
        self.reload_data()
