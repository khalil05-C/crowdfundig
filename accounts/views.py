from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View

from accounts.models import User


def get_user_badges(user):
    """Return badges earned from all completed pledges, never only the latest pledge."""
    completed_pledges = user.pledges.filter(status="completed").select_related("project")
    badges = []
    seen_badges = set()

    for pledge in completed_pledges:
        badge = pledge.earned_badge
        if badge and badge.title not in seen_badges:
            badges.append(badge)
            seen_badges.add(badge.title)

    return badges


class LoginView(View):
    template_name = "accounts/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("/dashboard/")
        return render(request, self.template_name)

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("/dashboard/")

        email = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Bienvenue {user.first_name} !")
            return redirect(request.GET.get("next", "/dashboard/"))

        messages.error(request, "Email ou mot de passe incorrect.")
        return render(request, self.template_name)


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, "Vous etes deconnecte.")
        return redirect("/")


class RegisterView(View):
    template_name = "accounts/register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("/dashboard/")
        return render(request, self.template_name)

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("/dashboard/")

        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        role = request.POST.get("role")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, self.template_name)

        if User.objects.filter(email=email).exists():
            messages.error(request, "Cet email est deja utilise.")
            return render(request, self.template_name)

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
            role=role,
        )
        login(request, user)
        messages.success(request, f"Bienvenue {first_name} !")
        return redirect("/dashboard/")


class ProfileView(LoginRequiredMixin, View):
    template_name = "accounts/profile.html"

    def get(self, request):
        return render(request, self.template_name, {"badges": get_user_badges(request.user)})

    def post(self, request):
        user = request.user
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.phone = request.POST.get("phone", user.phone)
        user.notification_preference = request.POST.get(
            "notification_preference",
            user.notification_preference,
        )
        user.bio = request.POST.get("bio", user.bio)

        if request.FILES.get("avatar"):
            user.avatar = request.FILES["avatar"]

        user.save()
        messages.success(request, "Profil mis a jour !")
        return redirect("/accounts/profile/")
