from django.urls import path

from . import views

app_name = "pledges"

urlpatterns = [
    path("create/<slug:project_slug>/", views.CreatePledgeView.as_view(), name="create_pledge"),
    path("history/", views.PledgeHistoryView.as_view(), name="history"),
]
