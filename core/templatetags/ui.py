from django import template

register = template.Library()


@register.filter
def add_class(field, css):
    """Render a bound form field's widget with extra CSS classes (and is-invalid on errors)."""
    classes = [field.field.widget.attrs.get("class", ""), css]
    attrs = {}
    if field.errors:
        classes.append("is-invalid")
        attrs["aria-invalid"] = "true"
        attrs["aria-describedby"] = f"{field.auto_id}-error"
    attrs["class"] = " ".join(c for c in classes if c)
    return field.as_widget(attrs=attrs)
