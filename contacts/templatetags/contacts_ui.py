import zlib

from django import template
from django.utils import timezone
from django.utils.html import format_html

register = template.Library()

@register.filter
def linkedin_display(url):
    """https://www.linkedin.com/in/amy/ -> linkedin.com/in/amy"""
    text = str(url or "")
    for prefix in ("https://", "http://"):
        if text.lower().startswith(prefix):
            text = text[len(prefix):]
    if text.lower().startswith("www."):
        text = text[4:]
    return text.rstrip("/")


@register.filter
def short_date(value):
    """Nov 10 this year, Nov 10, 2025 otherwise, Never when empty."""
    if not value:
        return "Never"
    if value.year == timezone.localdate().year:
        return value.strftime("%b ") + str(value.day)
    return value.strftime("%b ") + f"{value.day}, {value.year}"


AVATAR_TONES = 6


def initials(name):
    """"Amy Chen" -> "AC", "Madonna" -> "M", "李晓明" -> "李", blank -> "?"."""
    words = str(name or "").split()
    if not words:
        return "?"
    first = words[0][0]
    if len(words) == 1 or not first.isascii():
        return first.upper()
    return (first + words[-1][0]).upper()


def avatar_tone(name):
    """Stable 0..5 per name (crc32, not hash(), which changes between processes)."""
    return zlib.crc32(str(name or "").strip().lower().encode("utf-8")) % AVATAR_TONES


@register.simple_tag
def avatar(name, size=""):
    css = f"avatar avatar--tone-{avatar_tone(name)}" + (f" avatar--{size}" if size else "")
    return format_html('<span class="{}" aria-hidden="true">{}</span>', css, initials(name))
