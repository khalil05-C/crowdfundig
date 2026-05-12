from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, TemplateView

from projects.models import Project
from rewards.models import Reward
from notifications.models import Notification
from notifications.services import create_notification

from .forms import PledgeForm
from .models import Pledge


class CreatePledgeView(LoginRequiredMixin, TemplateView):
    template_name = "pledges/create_pledge.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, slug=kwargs["project_slug"], status=Project.Status.ACTIVE)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        Reward.ensure_default_rewards(self.project)
        context["project"] = self.project
        context["form"] = kwargs.get("form") or PledgeForm(project=self.project)
        context["rewards"] = self.project.rewards.filter(is_active=True).order_by("minimum_amount", "title")
        context["quick_amounts"] = [50, 100, 250, 500]
        return context

    def post(self, request, *args, **kwargs):
        form = PledgeForm(request.POST, project=self.project)
        if not form.is_valid():
            messages.error(request, "Merci de corriger les informations de contribution.")
            return self.render_to_response(self.get_context_data(form=form))

        pledge = form.save(commit=False)
        pledge.backer = request.user
        pledge.project = self.project
        pledge.status = Pledge.Status.PENDING
        pledge.save()

        create_notification(
            recipient=request.user,
            notification_type=Notification.Type.DONATION_CREATED,
            title="Donation creee",
            message=f"Votre donation de {pledge.amount} MAD pour {self.project.title} a ete creee.",
            link=f"/pledges/history/",
        )
        create_notification(
            recipient=self.project.owner,
            notification_type=Notification.Type.PLEDGE_RECEIVED,
            title="Nouvelle contribution",
            message=f"{request.user.get_full_name()} a contribue {pledge.amount} MAD a votre projet {self.project.title}.",
            link=f"/projects/{self.project.slug}/",
        )
        if pledge.reward:
            create_notification(
                recipient=request.user,
                notification_type=Notification.Type.REWARD_SELECTED,
                title="Recompense selectionnee",
                message=f"Vous avez selectionne la recompense : {pledge.reward.title}.",
                link=f"/pledges/history/",
            )

        messages.success(request, f"Contribution de {pledge.amount} MAD creee. Finalisez le paiement.")
        return redirect("payments:process_payment", pledge_id=pledge.pk)


class PledgeHistoryView(LoginRequiredMixin, ListView):
    template_name = "pledges/history.html"
    context_object_name = "pledges"

    def get_queryset(self):
        return self.request.user.pledges.select_related("project", "reward").order_by("-created_at")
