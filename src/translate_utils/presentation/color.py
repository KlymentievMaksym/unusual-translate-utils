def get_color_gradient(percent: float) -> str:
    """Calculates a hex color blending from Red (0%) to Yellow (50%) to Green (100%)."""
    p = max(0, min(100, percent))

    if p <= 50:
        r = 255
        g = int((p / 50.0) * 255)
    else:
        r = int(255 - ((p - 50.0) / 50.0) * 255)
        g = 255

    return f"#{r:02x}{g:02x}00"
