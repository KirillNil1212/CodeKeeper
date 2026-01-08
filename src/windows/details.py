import tkinter as tk
from tkinter import ttk, messagebox
from src.utils import get_font, darken
from src.windows.add_edit import AddEditPasswordWindow


class DetailModal(tk.Toplevel):
    """
    Модальное окно для просмотра детальной информации о записи.
    Показывает расшифрованные данные и позволяет копировать их.
    """

    def __init__(self, parent, password_id):
        super().__init__(parent.root)
        self.withdraw()
        self.parent = parent
        self.icon_mgr = parent.icon_mgr
        self.password_id = password_id

        # Обновляем метку "последнее использование" при открытии
        self.parent.update_last_used(password_id)

        self.title("Детали")
        self.icon_mgr.set_app_icon(self)
        self.transient(parent.root)
        self.grab_set()

        # Загружаем данные из БД
        self.parent.cursor.execute(
            "SELECT * FROM passwords WHERE id=?", (password_id,))
        row = self.parent.cursor.fetchone()
        cols = [d[0] for d in self.parent.cursor.description]
        # Преобразуем кортеж в словарь {колонка: значение}
        self.data = dict(zip(cols, row))

        self.current_row = 0
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_ui()
        # Закрытие по клику вне окна (для удобства)
        self.bind("<Button-1>", self.check_outside_click)

        # Центрирование и расчет размера окна
        self.update_idletasks()
        # Запас высоты под шапку и кнопки
        req_h = self.content_frame.winfo_reqheight() + 150
        req_w = 600
        max_h = 700
        final_h = min(req_h, max_h)
        x = (self.winfo_screenwidth() // 2) - (req_w // 2)
        y = (self.winfo_screenheight() // 2) - (final_h // 2)
        self.geometry(f"{req_w}x{final_h}+{x}+{y}")
        self.resizable(False, False)

        self.deiconify()
        self.parent.root.wait_window(self)

    def check_outside_click(self, event):
        """Закрывает окно, если клик был за его пределами."""
        x, y = event.x, event.y
        if x < 0 or x > self.winfo_width() or y < 0 or y > self.winfo_height():
            self.destroy()

    def create_ui(self):
        """Создание интерфейса просмотра."""
        sc = self.parent.config['font_size']
        f_head = get_font(16, "bold", sc)
        f_btn = get_font(10, "bold", sc)

        # --- Шапка с названием ---
        header = tk.Frame(self.main_frame, bg="#34495e", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        name_text = self.data.get('name', 'Без названия')
        if self.data.get('is_favorite'):
            name_text = "★ " + name_text
        tk.Label(header, text=name_text, font=f_head,
                 bg="#34495e", fg="white").pack(expand=True)

        # --- Скроллируемая область контента ---
        canvas_container = tk.Frame(self.main_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(canvas_container, highlightthickness=0)
        sb = ttk.Scrollbar(
            canvas_container, orient="vertical", command=canvas.yview)

        self.content_frame = tk.Frame(canvas, padx=20, pady=15)
        self.content_frame.columnconfigure(0, minsize=120)  # Колонка меток
        self.content_frame.columnconfigure(1, weight=1)    # Колонка значений

        canvas.create_window(
            (0, 0), window=self.content_frame, anchor="nw", width=560)
        canvas.configure(yscrollcommand=sb.set)

        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.content_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))

        # Скролл колесиком
        self.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(
            int(-1*(e.delta/120)), "units"))
        self.bind("<Destroy>", lambda e: self.unbind_all("<MouseWheel>"))

        # --- Вывод полей ---
        # Поля, которые не нужно показывать в списке "остальное"
        exclude = ['id', 'user_id', 'type', 'name', 'password',
                   'is_favorite', 'created_at', 'updated_at', 'last_used_at']
        # Поля, которые нужно скрывать звездочками
        encrypted = ["card_number", "card_cvv", "card_pin",
                     "security_answer", "account_number", "passport_number"]

        # Принудительный порядок важных полей вверху
        if self.data.get('username'):
            self.add_grid_row("Логин/User", self.data.get('username'))
        if self.data.get('email'):
            self.add_grid_row("Email", self.data.get('email'))

        self.add_grid_row("Пароль", self.data.get(
            'password'), is_secure=True, is_big=True)

        # Вывод всех остальных заполненных полей
        for key, val in self.data.items():
            if key in exclude or val is None or val == "":
                continue
            label = key.replace("_", " ").title()
            is_sec = key in encrypted
            self.add_grid_row(label, str(val), is_secure=is_sec)

        # Даты создания/изменения внизу серым цветом
        created = self.data.get('created_at')
        updated = self.data.get('updated_at')
        if created:
            self.add_grid_row("Создано", str(
                created).split('.')[0], color="#95a5a6")
        if updated:
            self.add_grid_row("Изменено", str(
                updated).split('.')[0], color="#95a5a6")

        # --- Подвал с кнопками ---
        footer = tk.Frame(self.main_frame, pady=20, padx=15, bg="#ecf0f1")
        footer.pack(side="bottom", fill=tk.X)
        footer.columnconfigure(0, weight=1)
        footer.columnconfigure(1, weight=1)
        footer.columnconfigure(2, weight=1)

        edit_img = self.icon_mgr.get("edit", "small")
        del_img = self.icon_mgr.get("delete", "small")
        close_img = self.icon_mgr.get("close", "small")

        c_edit, c_del, c_close = "#f39c12", "#e74c3c", "#95a5a6"

        tk.Button(footer, text=" Редактировать", image=edit_img if edit_img else None, compound="left",
                  command=self.edit_entry, bg=c_edit, activebackground=darken(c_edit), fg="white", font=f_btn, relief="raised", cursor="hand2").grid(row=0, column=0, sticky="ew", padx=5, ipady=5)

        tk.Button(footer, text=" Удалить", image=del_img if del_img else None, compound="left",
                  command=self.delete_entry, bg=c_del, activebackground=darken(c_del), fg="white", font=f_btn, relief="raised", cursor="hand2").grid(row=0, column=1, sticky="ew", padx=5, ipady=5)

        tk.Button(footer, text=" Закрыть", image=close_img if close_img else None, compound="left",
                  command=self.destroy, bg=c_close, activebackground=darken(c_close), fg="white", font=f_btn, relief="raised", cursor="hand2").grid(row=0, column=2, sticky="ew", padx=5, ipady=5)

    def add_grid_row(self, label, value, is_secure=False, is_big=False, color="black"):
        """Добавляет одну строку (Метка: Значение) в таблицу просмотра."""
        sc = self.parent.config['font_size']
        f_lbl = get_font(10, "bold", sc)
        f_val = get_font(12, "normal", sc)
        if is_big:
            f_val = get_font(14, "bold", sc)

        r = self.current_row

        # Метка слева
        lbl = tk.Label(self.content_frame, text=label+":",
                       font=f_lbl, fg="#7f8c8d", anchor="w")
        lbl.grid(row=r, column=0, sticky="nw", pady=8)

        # Контейнер для значения справа
        val_frame = tk.Frame(self.content_frame)
        val_frame.grid(row=r, column=1, sticky="ew", pady=4)

        real_value = value
        display_value = value
        if is_secure:
            display_value = "••••••••"

        # Используем Entry в режиме readonly, чтобы можно было выделять текст, но не менять
        entry = tk.Entry(val_frame, font=f_val, fg=color, relief="flat",
                         bg=self.content_frame.cget("bg"), state="readonly")
        self.set_entry_text(entry, display_value)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Кнопки управления (глаз, копировать)
        btn_frame = tk.Frame(val_frame)
        btn_frame.pack(side=tk.RIGHT)

        if is_secure:
            eye_img = self.icon_mgr.get("show", "small")
            btn_eye = tk.Button(btn_frame, image=eye_img if eye_img else None, text="👁" if not eye_img else "",
                                relief="flat", bg="#bdc3c7", width=30 if eye_img else 3, cursor="hand2")
            btn_eye.pack(side=tk.LEFT, padx=2)

            # Логика переключения видимости (расшифровка)
            def toggle_view(e=entry, btn=btn_eye, v=real_value):
                current = e.get()
                if current.startswith("•••"):
                    try:
                        decrypted = self.parent.decrypt_password(v)
                        self.set_entry_text(e, decrypted)
                        # Красный цвет для открытого пароля
                        e.config(fg="#e74c3c")
                    except:
                        pass
                else:
                    self.set_entry_text(e, "••••••••")
                    e.config(fg="black")
            btn_eye.config(command=toggle_view)

        copy_img = self.icon_mgr.get("copy", "small")
        btn_copy = tk.Button(btn_frame, image=copy_img if copy_img else None, text="📋" if not copy_img else "",
                             relief="flat", bg="#bdc3c7", width=30 if copy_img else 3, cursor="hand2")
        btn_copy.pack(side=tk.LEFT, padx=2)

        # Логика копирования
        def copy_action(v=real_value, sec=is_secure):
            # Требуем мастер-пароль, если это настроено
            if not self.parent.verify_master_password():
                return
            text_to_copy = v
            if sec:
                try:
                    text_to_copy = self.parent.decrypt_password(v)
                except:
                    pass
            self.copy_to_clip(text_to_copy)
            self.parent.update_last_used(self.password_id)

        btn_copy.config(command=copy_action)

        # Разделительная линия
        tk.Frame(self.content_frame, height=1, bg="#ecf0f1").grid(
            row=r+1, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        self.current_row += 2

    def set_entry_text(self, entry, text):
        """Безопасно меняет текст в Entry (включает state=normal, пишет, выключает)."""
        entry.config(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, text)
        entry.config(state="readonly")

    def copy_to_clip(self, text):
        """Копирует в буфер и показывает маленькое всплывающее окошко."""
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

        # Создаем временное окошко "Скопировано"
        t = tk.Toplevel(self)
        t.wm_overrideredirect(True)
        x = self.winfo_rootx() + (self.winfo_width()//2) - 50
        y = self.winfo_rooty() + self.winfo_height() - 80
        t.geometry(f"120x30+{x}+{y}")
        tk.Label(t, text="✓ Скопировано!", bg="#2ecc71", fg="white",
                 font=("Arial", 9)).pack(fill="both", expand=True)
        t.after(1500, t.destroy)  # Исчезнет через 1.5 сек

    def edit_entry(self):
        """Переход в режим редактирования."""
        self.destroy()
        AddEditPasswordWindow(
            self.parent, mode="edit", password_id=self.password_id)

    def delete_entry(self):
        """Удаление текущей записи."""
        if messagebox.askyesno("Удаление", "Точно удалить?"):
            self.parent.cursor.execute(
                "DELETE FROM passwords WHERE id=?", (self.password_id,))
            self.parent.conn.commit()
            self.parent.load_passwords()
            self.destroy()
