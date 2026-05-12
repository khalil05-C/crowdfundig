from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from fundrise_ma.views import SetLanguageView
from projects.models import Category


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(is_active=True)
        return context


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("lang/<str:lang>/", SetLanguageView.as_view(), name="set_language"),
    path("comment-ca-marche/", TemplateView.as_view(template_name="pages/how_it_works.html"), name="how_it_works"),
    path("support/", include("support_tickets.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("projects/", include("projects.urls")),
    path("pledges/", include("pledges.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("notifications/", include("notifications.urls")),
    path("rewards/", include("rewards.urls")),
    path("updates/", include("MiseAJour.urls")),
    path("payments/", include("payments.urls")),
]

handler404 = "fundrise_ma.views.custom_404"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
