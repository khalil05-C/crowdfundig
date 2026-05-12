from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="home"),
    path("approve/<int:project_id>/", views.ApproveProjectView.as_view(), name="approve"),
    path("reject/<int:project_id>/", views.RejectProjectView.as_view(), name="reject"),
]
