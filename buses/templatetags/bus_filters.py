# buses/templatetags/bus_filters.py

from django import template

register = template.Library()

@register.filter
def format_duration(duration):
    """
    Format a timedelta object to HH:MM string
    Example: timedelta(hours=2, minutes=30) -> "2:30"
    """
    if not duration:
        return ""
    
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    return f"{hours}:{minutes:02d}"