from django.urls import path

from . import views

app_name = "MiseAJour"

urlpatterns = [
    path("update/<slug:project_slug>/", views.AddUpdateView.as_view(), name="add_update"),
    path("comment/<slug:project_slug>/", views.AddCommentView.as_view(), name="add_comment"),
    path("comment/edit/<int:comment_id>/", views.EditCommentView.as_view(), name="edit_comment"),
    path("comment/delete/<int:comment_id>/", views.DeleteCommentView.as_view(), name="delete_comment"),
]
