def nav(request):
    """Contact count for the sidebar. Only for logged-in users."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}
    return {"nav_contact_count": user.contacts.count()}
