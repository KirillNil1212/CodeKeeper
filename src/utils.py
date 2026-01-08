from tkinter import font


def get_font(base_size, weight="normal", scale_str="100%"):
    """
    Возвращает объект шрифта Tkinter с учетом масштабирования.
    Это позволяет менять размер интерфейса через настройки (scale_str).
    """
    s = str(scale_str).replace("%", "")
    try:
        scale = int(s) / 100.0
    except ValueError:
        scale = 1.0
    # Возвращаем шрифт Arial нужного размера и жирности
    return font.Font(family="Arial", size=int(base_size * scale), weight=weight)


def darken(hex_color, factor=0.8):
    """
    Делает hex-цвет темнее на заданный коэффициент (0.8 = 80% яркости).
    Используется для создания эффекта нажатия на кнопки (activebackground).
    """
    if not hex_color.startswith('#'):
        return "#cccccc"  # Заглушка, если передан некорректный цвет

    hex_color = hex_color.lstrip('#')

    # Конвертируем HEX в RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    # Уменьшаем яркость каждого канала
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)

    # Возвращаем обратно в HEX формате
    return f"#{r:02x}{g:02x}{b:02x}"
