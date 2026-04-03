"""Template filters for duration formatting."""
from django import template

register = template.Library()


@register.filter
def duration_hms(seconds):
    """
    Convert seconds (int) to HH:MM:SS or MM:SS format.
    Examples: 3661 -> "1h 01m 01s", 125 -> "2m 05s", 45 -> "45s"
    """
    if seconds is None:
        return "—"
    try:
        seconds = int(seconds)
    except (ValueError, TypeError):
        return "—"
    if seconds < 0:
        return "—"

    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    if h > 0:
        return f"{h}h {m:02d}m {s:02d}s"
    elif m > 0:
        return f"{m}m {s:02d}s"
    else:
        return f"{s}s"


@register.filter
def duration_minutes_hms(minutes):
    """
    Convert minutes (float/int) to HH:MM:SS or MM:SS format.
    Examples: 61.5 -> "1h 01m 30s", 2.5 -> "2m 30s"
    """
    if minutes is None:
        return "—"
    try:
        total_seconds = int(float(minutes) * 60)
    except (ValueError, TypeError):
        return "—"
    return duration_hms(total_seconds)
