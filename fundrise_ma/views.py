from django.shortcuts import redirect, render
from django.views import View


def custom_404(request, exception):
    return render(request, "404.html", status=404)


class SetLanguageView(View):
    def get(self, request, lang):
        request.session["site_language"] = "ar" if lang == "ar" else "fr"
        return redirect(request.META.get("HTTP_REFERER", "/"))
