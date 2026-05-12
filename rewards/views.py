from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, View

from projects.models import Project

from .forms import RewardForm
from .models import Reward


class RewardCreateView(LoginRequiredMixin, TemplateView):
    template_name = "rewards/reward_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, slug=kwargs["project_slug"], owner=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        context["form"] = kwargs.get("form") or RewardForm()
        return context

    def post(self, request, *args, **kwargs):
        form = RewardForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(request, "Merci de corriger le formulaire de recompense.")
            return self.render_to_response(self.get_context_data(form=form))

        reward = form.save(commit=False)
        reward.project = self.project
        reward.save()
        messages.success(request, "Recompense ajoutee !")
        return redirect("projects:project_detail", slug=self.project.slug)


class RewardDeleteView(LoginRequiredMixin, View):
    def post(self, request, reward_id):
        return self.delete_reward(request, reward_id)

    def get(self, request, reward_id):
        return self.delete_reward(request, reward_id)

    def delete_reward(self, request, reward_id):
        reward = get_object_or_404(Reward, pk=reward_id, project__owner=request.user)
        project_slug = reward.project.slug
        reward.delete()
        messages.success(request, "Recompense supprimee !")
        return redirect("projects:project_detail", slug=project_slug)
