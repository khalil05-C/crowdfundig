from django.urls import path

from . import views

app_name = "rewards"

urlpatterns = [
    path("create/<slug:project_slug>/", views.RewardCreateView.as_view(), name="create"),
    path("delete/<int:reward_id>/", views.RewardDeleteView.as_view(), name="delete"),
]
