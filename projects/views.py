from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.text import slugify
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from rewards.models import Reward

from .models import Category, Project


def unique_project_slug(title, project_id=None):
    base_slug = slugify(title) or "projet"
    slug = base_slug
    counter = 1

    queryset = Project.objects.all()
    if project_id:
        queryset = queryset.exclude(pk=project_id)

    while queryset.filter(slug=slug).exists():
        counter += 1
        slug = f"{base_slug}-{counter}"

    return slug


class ProjectListView(ListView):
    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"

    def get_queryset(self):
        queryset = Project.objects.filter(status=Project.Status.ACTIVE).select_related("category", "owner")

        self.category_slug = self.request.GET.get("category")
        if self.category_slug:
            queryset = queryset.filter(category__slug=self.category_slug)

        self.search_query = self.request.GET.get("q")
        if self.search_query:
            queryset = queryset.filter(title__icontains=self.search_query)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(is_active=True)
        context["selected_category"] = self.category_slug
        context["search_query"] = self.search_query
        return context


class ProjectDetailView(DetailView):
    model = Project
    template_name = "projects/project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        queryset = Project.objects.select_related("category", "owner").prefetch_related(
            "project_updates", "comments__replies"
        )
        user = self.request.user

        if user.is_authenticated and (user.is_staff or getattr(user, "role", "") == "admin"):
            return queryset

        if user.is_authenticated:
            return queryset.filter(Q(status=Project.Status.ACTIVE) | Q(owner=user))

        return queryset.filter(status=Project.Status.ACTIVE)

    def get_object(self, queryset=None):
        project = super().get_object(queryset)
        Project.objects.filter(pk=project.pk).update(views_count=project.views_count + 1)
        project.views_count += 1
        Reward.ensure_default_rewards(project)
        return project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["rewards"] = self.object.rewards.filter(is_active=True).order_by("minimum_amount", "title")
        user = self.request.user
        context["can_admin_delete_project"] = user.is_authenticated and (
            user.is_staff or getattr(user, "role", "") == "admin"
        )
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    template_name = "projects/project_form.html"
    fields = [
        "title",
        "short_description",
        "description",
        "category",
        "goal_amount",
        "end_date",
        "funding_type",
        "cover_image",
        "video_url",
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["category"].queryset = Category.objects.filter(is_active=True)
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.slug = unique_project_slug(form.instance.title)
        form.instance.status = (
            Project.Status.PENDING
            if self.request.POST.get("action") == "submit"
            else Project.Status.DRAFT
        )
        messages.success(self.request, "Projet cree avec succes !")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("projects:project_detail", kwargs={"slug": self.object.slug})


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    template_name = "projects/project_form.html"
    fields = ProjectCreateView.fields

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["category"].queryset = Category.objects.filter(is_active=True)
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(is_active=True)
        context["is_update"] = True
        return context

    def form_valid(self, form):
        form.instance.slug = unique_project_slug(form.instance.title, project_id=self.object.pk)
        form.instance.status = (
            Project.Status.PENDING
            if self.request.POST.get("action") == "submit"
            else Project.Status.DRAFT
        )
        messages.success(self.request, "Projet mis a jour avec succes !")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("projects:project_detail", kwargs={"slug": self.object.slug})


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project

    def is_admin_user(self):
        user = self.request.user
        return user.is_staff or getattr(user, "role", "") == "admin"

    def get_queryset(self):
        queryset = Project.objects.prefetch_related("rewards")

        if self.is_admin_user():
            return queryset

        return queryset.filter(owner=self.request.user)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.status == Project.Status.ACTIVE and not self.is_admin_user():
            raise PermissionDenied("Vous n'avez pas l'autorisation de supprimer ce projet.")

        self.delete_project_files(self.object)
        self.object.delete()
        messages.success(request, "Projet supprime avec succes.")
        return redirect(self.get_success_url())

    def delete_project_files(self, project):
        files_to_delete = []

        if project.cover_image:
            files_to_delete.append(project.cover_image)

        for reward in project.rewards.all():
            if reward.image:
                files_to_delete.append(reward.image)

        for file_field in files_to_delete:
            file_field.delete(save=False)

    def get_success_url(self):
        return reverse("projects:project_list")
