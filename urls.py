from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.urls import path

from dashboard import views

urlpatterns = [
    path("admin/", admin.site.urls),

    path("signup/", views.signup, name="signup"),
    path(
        "login/",
        LoginView.as_view(template_name="login.html"),
        name="login",
    ),
    path("logout/", views.logout_view, name="logout"),

    path("", views.dashboard_home, name="dashboard_home"),
    path("productivity/", views.productivity_dashboard, name="productivity_dashboard"),
    path("engagement/", views.engagement_dashboard, name="engagement_dashboard"),
    path("attrition/", views.attrition_dashboard, name="attrition_dashboard"),
    path("employee/<str:employee_id>/", views.employee_detail, name="employee_detail"),
]

