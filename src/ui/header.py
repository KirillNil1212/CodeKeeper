import tkinter as tk
from src.utils import darken


class UIHeader:
    """Компонент шапки окна (самая верхняя панель)."""

    def __init__(self, app):
        self.app = app
        # Создаем темный фрейм фиксированной высоты
        self.frame = tk.Frame(app.root, bg="#2c3e50", height=50)
        self.frame.pack(fill=tk.X)
        # Запрещаем фрейму сжиматься под контент
        self.frame.pack_propagate(False)
        self._build()

    def _build(self):
        # --- Левая часть: Статус и иконка ---
        status_frame = tk.Frame(self.frame, bg="#2c3e50")
        status_frame.pack(side=tk.LEFT, padx=20)

        icon = self.app.icon_mgr.get("show", "small")
        if icon:
            tk.Label(status_frame, image=icon, bg="#2c3e50").pack(
                side=tk.LEFT, padx=(0, 5))

        tk.Label(status_frame, text="Хранилище разблокировано",
                 font=self.app.f_head, bg="#2c3e50", fg="#2ecc71").pack(side=tk.LEFT)

        # --- Правая часть: Кнопка "Заблокировать" ---
        lock_icon = self.app.icon_mgr.get(
            "locked", "small") or self.app.icon_mgr.get("close", "small")

        btn = tk.Button(self.frame, text=" Заблокировать", image=lock_icon if lock_icon else None,
                        compound="left", bg="#c0392b", activebackground=darken("#c0392b"),
                        fg="white", font=("Arial", 10, "bold"), relief="flat",
                        command=self.app.lock_app, cursor="hand2")
        btn.pack(side=tk.RIGHT, padx=20, pady=10, ipady=2)
