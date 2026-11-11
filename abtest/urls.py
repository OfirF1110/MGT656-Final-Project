from django.urls import path

from . import views

# First 7 characters of SHA-1("nameless-grass"), our team nickname.
AB_HASH = "020c45f"

urlpatterns = [
    path(AB_HASH, views.ab_page, name="abtest"),
    path(f"{AB_HASH}/stats", views.ab_stats, name="abtest-stats"),
]
