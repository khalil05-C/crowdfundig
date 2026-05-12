from django.urls import path

from . import views

app_name = "support"

urlpatterns = [
    path("", views.SupportHomeView.as_view(), name="home"),
    path("ticket/<int:pk>/", views.SupportTicketDetailView.as_view(), name="detail"),
    path("admin/", views.SupportAdminListView.as_view(), name="admin_list"),
    path("admin/ticket/<int:pk>/", views.SupportAdminDetailView.as_view(), name="admin_detail"),
]
