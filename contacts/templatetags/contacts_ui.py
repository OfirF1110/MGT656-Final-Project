from django import template
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

# Pie radius 2.5 drawn with a 5px stroke fills the inside of the ring; C = 2 * pi * 2.5.
_PIE_C = 15.708
_RING = '<circle cx="8" cy="8" r="6.25" fill="none" stroke="currentColor" stroke-width="1.5"/>'


def _pie(fraction):
    return (
        f'<circle cx="8" cy="8" r="2.5" fill="none" stroke="currentColor" stroke-width="5" '
        f'stroke-dasharray="{_PIE_C * fraction:.3f} {_PIE_C:.3f}" transform="rotate(-90 8 8)"/>'
    )


_SHAPES = {
    "to_contact": _RING,
    "awaiting_reply": _RING + _pie(0.25),
    "in_conversation": _RING + _pie(0.5),
    "meeting_set": _RING + _pie(0.75),
    "met": '<circle cx="8" cy="8" r="7" fill="currentColor"/>'
           '<path d="M4.9 8.2l2.1 2.1 4.1-4.4" fill="none" stroke="#fff" stroke-width="1.7" '
           'stroke-linecap="round" stroke-linejoin="round"/>',
    "inactive": '<circle cx="8" cy="8" r="6.25" fill="none" stroke="currentColor" stroke-width="1.5" '
                'stroke-dasharray="2.2 2.2"/>',
}


@register.simple_tag
def stage_icon(stage, size=16):
    """Inline SVG for a stage. Decorative: always render the stage label next to it."""
    shape = _SHAPES.get(str(stage), _RING)
    return format_html(
        '<svg class="stage-icon stage-icon--{}" width="{}" height="{}" viewBox="0 0 16 16" '
        'aria-hidden="true" focusable="false">{}</svg>',
        stage, size, size, mark_safe(shape),
    )


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
