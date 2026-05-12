from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, View

from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    template_name = "notifications/list.html"
    context_object_name = "notifications"

    def get_queryset(self):
        return self.request.user.notifications.order_by("-created_at")


class MarkAllReadView(LoginRequiredMixin, View):
    def get(self, request):
        request.user.notifications.filter(is_read=False).update(is_read=True)
        return redirect("/notifications/")

    def post(self, request):
        return self.get(request)


class MarkReadView(LoginRequiredMixin, View):
    """Mark a single notification as read."""

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.mark_as_read()
        return redirect("/notifications/")

    def get(self, request, pk):
        return self.post(request, pk)
