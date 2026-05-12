from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, View

from MiseAJour.models import Comment, ProjectUpdate
from notifications.models import Notification
from notifications.services import create_notification
from projects.models import Project


class AddUpdateView(LoginRequiredMixin, TemplateView):
    template_name = "MiseAJour/MiseAJour_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, slug=kwargs["project_slug"], owner=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        return context

    def post(self, request, *args, **kwargs):
        update = ProjectUpdate.objects.create(
            project=self.project,
            author=request.user,
            title=request.POST.get("title"),
            content=request.POST.get("content"),
            is_public=request.POST.get("is_public") == "on",
        )
        backers = (
            self.project.pledges.filter(status="completed", backer__isnull=False)
            .select_related("backer")
            .values_list("backer", flat=True)
            .distinct()
        )
        for backer_id in backers:
            from accounts.models import User

            backer = User.objects.get(pk=backer_id)
            create_notification(
                recipient=backer,
                notification_type=Notification.Type.PROJECT_UPDATED,
                title=f"Nouvelle mise a jour : {self.project.title}",
                message=update.title,
                link=f"/projects/{self.project.slug}/",
            )
        messages.success(request, "Mise a jour publiee !")
        return redirect("projects:project_detail", slug=self.project.slug)


class AddCommentView(LoginRequiredMixin, View):
    def post(self, request, project_slug):
        project = get_object_or_404(Project, slug=project_slug)
        content = request.POST.get("content", "").strip()
        parent_id = request.POST.get("parent_id")

        if content:
            Comment.objects.create(
                project=project,
                author=request.user,
                content=content,
                parent_id=parent_id or None,
            )
            messages.success(request, "Commentaire ajoute !")

        return redirect("projects:project_detail", slug=project.slug)


class EditCommentView(LoginRequiredMixin, View):
    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id, author=request.user)
        content = request.POST.get("content", "").strip()

        if content:
            comment.content = content
            comment.save()
            messages.success(request, "Commentaire modifie !")

        return redirect("projects:project_detail", slug=comment.project.slug)


class DeleteCommentView(LoginRequiredMixin, View):
    def get(self, request, comment_id):
        return self.delete_comment(request, comment_id)

    def post(self, request, comment_id):
        return self.delete_comment(request, comment_id)

    def delete_comment(self, request, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id)

        if request.user == comment.author or request.user.is_staff:
            project_slug = comment.project.slug
            comment.delete()
            messages.success(request, "Commentaire supprime.")
            return redirect("projects:project_detail", slug=project_slug)

        messages.error(request, "Action non autorisee.")
        return redirect("/")
