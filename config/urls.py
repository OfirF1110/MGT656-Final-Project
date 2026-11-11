from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from core import views

urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("account/", views.account, name="account"),
    path("admin/", admin.site.urls),
    path("", include("abtest.urls")),
]
