from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("pay/<int:pledge_id>/", views.ProcessPaymentView.as_view(), name="process_payment"),
    path("stripe/success/<int:pledge_id>/", views.StripeSuccessView.as_view(), name="stripe_success"),
    path("stripe/cancel/<int:pledge_id>/", views.StripeCancelView.as_view(), name="stripe_cancel"),
    path("withdrawal/<slug:project_slug>/", views.WithdrawalRequestView.as_view(), name="withdrawal"),
]
