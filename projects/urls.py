from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="project_list"),
    path("create/", views.ProjectCreateView.as_view(), name="project_create"),
    path("<slug:slug>/edit/", views.ProjectUpdateView.as_view(), name="project_update"),
    path("<slug:slug>/delete/", views.ProjectDeleteView.as_view(), name="project_delete"),
    path("<slug:slug>/", views.ProjectDetailView.as_view(), name="project_detail"),
]
