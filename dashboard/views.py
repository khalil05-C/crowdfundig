from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.models import User
from notifications.models import Notification
from notifications.services import create_notification
from pledges.models import Pledge
from projects.models import Project


class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_staff or request.user.role == "admin":
            return AdminDashboardView.as_view()(request)
        return OwnerDashboardView.as_view()(request)


class OwnerDashboardView(LoginRequiredMixin, View):
    template_name = "dashboard/index.html"

    def get(self, request):
        projects = request.user.projects.all()
        completed_pledges = Pledge.objects.filter(project__owner=request.user, status=Pledge.Status.COMPLETED)
        total_gross = sum(pledge.gross_amount for pledge in completed_pledges)
        total_commission = sum(pledge.platform_commission_amount for pledge in completed_pledges)
        total_net = sum(pledge.project_net_amount for pledge in completed_pledges)

        for project in projects:
            project_completed_pledges = project.pledges.filter(status=Pledge.Status.COMPLETED)
            project.gross_collected = sum(pledge.gross_amount for pledge in project_completed_pledges)
            project.commission_collected = sum(pledge.platform_commission_amount for pledge in project_completed_pledges)
            project.net_available = sum(pledge.project_net_amount for pledge in project_completed_pledges)

        context = {
            "projects": projects,
            "total_projects": projects.count(),
            "total_pledges": completed_pledges.count(),
            "total_raised": total_gross,
            "total_commission": total_commission,
            "total_net_available": total_net,
            "notifications": request.user.notifications.order_by("-created_at")[:5],
            "total_notifications": request.user.notifications.filter(is_read=False).count(),
        }
        return render(request, self.template_name, context)


class AdminDashboardView(LoginRequiredMixin, View):
    template_name = "dashboard/admin.html"

    def get(self, request):
        completed_pledges = Pledge.objects.filter(status=Pledge.Status.COMPLETED)
        stats = {
            "total_users": User.objects.count(),
            "total_projects": Project.objects.count(),
            "active_projects": Project.objects.filter(status=Project.Status.ACTIVE).count(),
            "pending_projects": Project.objects.filter(status=Project.Status.PENDING).count(),
            "total_pledges": completed_pledges.count(),
            "total_raised": sum(p.gross_amount for p in completed_pledges),
            "total_commission": sum(p.platform_commission_amount for p in completed_pledges),
            "total_net": sum(p.project_net_amount for p in completed_pledges),
        }
        funded_projects = Project.objects.filter(status=Project.Status.FUNDED).order_by("-current_amount")[:5]
        for project in funded_projects:
            project.net_received = sum(
                pledge.project_net_amount for pledge in project.pledges.filter(status=Pledge.Status.COMPLETED)
            )

        context = {
            "stats": stats,
            "pending_projects": Project.objects.filter(status=Project.Status.PENDING)
            .select_related("owner", "category")
            .order_by("created_at"),
            "funded_projects": funded_projects,
            "recent_users": User.objects.order_by("-date_joined")[:8],
        }
        return render(request, self.template_name, context)


class AdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff and request.user.role != "admin":
            messages.error(request, "Acces refuse.")
            return redirect("/dashboard/")
        return super().dispatch(request, *args, **kwargs)


class ApproveProjectView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request, project_id):
        return self.approve(request, project_id)

    def post(self, request, project_id):
        return self.approve(request, project_id)

    def approve(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        project.status = Project.Status.ACTIVE
        project.save(update_fields=["status"])

        create_notification(
            recipient=project.owner,
            notification_type="project_approved",
            title="Votre projet a ete approuve !",
            message=f'Votre projet "{project.title}" est maintenant en ligne.',
            link=f"/projects/{project.slug}/",
        )

        messages.success(request, f'Projet "{project.title}" approuve !')
        return redirect("/dashboard/")


class RejectProjectView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request, project_id):
        return self.reject(request, project_id)

    def post(self, request, project_id):
        return self.reject(request, project_id)

    def reject(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        project.status = Project.Status.CANCELLED
        project.save(update_fields=["status"])

        create_notification(
            recipient=project.owner,
            notification_type="project_rejected",
            title="Votre projet a ete refuse",
            message=f'Votre projet "{project.title}" n\'a pas ete approuve.',
            link=f"/projects/{project.slug}/",
        )

        messages.warning(request, f'Projet "{project.title}" refuse.')
        return redirect("/dashboard/")
