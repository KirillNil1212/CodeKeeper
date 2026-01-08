import tkinter as tk


class ClipboardUtils:
    """
    Утилиты для работы с буфером обмена и горячими клавишами.
    Решает проблему неработающих Ctrl+C/V на русской раскладке в Tkinter.
    """

    @staticmethod
    def enable_universal_shortcuts(widget):
        """
        Включает поддержку Ctrl+C/V/X/A для переданного виджета (Entry, Text)
        независимо от текущей раскладки клавиатуры.
        """
        widget.bind("<Control-Key>", ClipboardUtils._handle_ctrl_key)

    @staticmethod
    def _handle_ctrl_key(event):
        """Обработчик нажатия клавиши с зажатым Ctrl."""
        keycode = event.keycode
        widget = event.widget

        # Если Tkinter сам распознал символ (англ. раскладка), ничего не делаем,
        # чтобы не дублировать действие.
        if event.keysym in ['c', 'v', 'x', 'a', 'C', 'V', 'X', 'A']:
            return

        # Проверяем коды клавиш (актуально для Windows, где коды 67=C, 86=V и т.д.)
        # 'break' означает, что стандартная обработка события прерывается
        if keycode == 67:
            ClipboardUtils._copy(widget)
            return "break"
        elif keycode == 86:
            ClipboardUtils._paste(widget)
            return "break"
        elif keycode == 88:
            ClipboardUtils._cut(widget)
            return "break"
        elif keycode == 65:
            ClipboardUtils._select_all(widget)
            return "break"

    @staticmethod
    def _copy(widget):
        """Принудительный вызов события Copy."""
        try:
            if widget.select_present():
                widget.event_generate("<<Copy>>")
        except:
            pass

    @staticmethod
    def _paste(widget):
        """Принудительный вызов события Paste."""
        try:
            widget.event_generate("<<Paste>>")
        except:
            pass

    @staticmethod
    def _cut(widget):
        """Принудительный вызов события Cut."""
        try:
            widget.event_generate("<<Cut>>")
        except:
            pass

    @staticmethod
    def _select_all(widget):
        """Выделение всего текста в поле."""
        try:
            widget.select_range(0, 'end')
            widget.icursor('end')
        except:
            pass
