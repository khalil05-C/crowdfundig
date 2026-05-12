from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .forms import SupportMessageForm, SupportTicketForm
from .models import SupportTicket


class AdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff and getattr(request.user, "role", "") != "admin":
            messages.error(request, "Acces reserve a l'administration.")
            return redirect("support:home")
        return super().dispatch(request, *args, **kwargs)


class SupportHomeView(LoginRequiredMixin, View):
    template_name = "support_tickets/home.html"

    def get(self, request):
        tickets = request.user.support_tickets.all()
        return render(request, self.template_name, {"form": SupportTicketForm(), "tickets": tickets})

    def post(self, request):
        form = SupportTicketForm(request.POST, request.FILES)
        tickets = request.user.support_tickets.all()

        if not form.is_valid():
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")
            return render(request, self.template_name, {"form": form, "tickets": tickets})

        ticket = form.save(commit=False)
        ticket.user = request.user
        ticket.save()
        messages.success(request, "Ticket cree avec succes. Vous pouvez maintenant suivre la conversation.")
        return redirect("support:detail", pk=ticket.pk)


class SupportTicketDetailView(LoginRequiredMixin, View):
    template_name = "support_tickets/detail.html"

    def get_ticket(self, request, pk):
        return get_object_or_404(SupportTicket, pk=pk, user=request.user)

    def get(self, request, pk):
        ticket = self.get_ticket(request, pk)
        return render(request, self.template_name, {"ticket": ticket, "form": SupportMessageForm()})

    def post(self, request, pk):
        ticket = self.get_ticket(request, pk)
        form = SupportMessageForm(request.POST, request.FILES)

        if not form.is_valid():
            messages.error(request, "Le message ne peut pas etre vide.")
            return render(request, self.template_name, {"ticket": ticket, "form": form})

        message = form.save(commit=False)
        message.ticket = ticket
        message.author = request.user
        message.save()

        if ticket.status == SupportTicket.Status.CLOSED:
            ticket.status = SupportTicket.Status.OPEN
            ticket.save(update_fields=["status", "updated_at"])

        messages.success(request, "Message envoye.")
        return redirect("support:detail", pk=ticket.pk)


class SupportAdminListView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "support_tickets/admin_list.html"

    def get(self, request):
        tickets = SupportTicket.objects.select_related("user")
        status = request.GET.get("status")
        priority = request.GET.get("priority")

        if status:
            tickets = tickets.filter(status=status)
        if priority:
            tickets = tickets.filter(priority=priority)

        return render(
            request,
            self.template_name,
            {
                "tickets": tickets,
                "statuses": SupportTicket.Status.choices,
                "priorities": SupportTicket.Priority.choices,
                "selected_status": status,
                "selected_priority": priority,
            },
        )


class SupportAdminDetailView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "support_tickets/admin_detail.html"

    def get_ticket(self, pk):
        return get_object_or_404(SupportTicket.objects.select_related("user"), pk=pk)

    def get(self, request, pk):
        ticket = self.get_ticket(pk)
        return render(
            request,
            self.template_name,
            {"ticket": ticket, "form": SupportMessageForm(), "statuses": SupportTicket.Status.choices},
        )

    def post(self, request, pk):
        ticket = self.get_ticket(pk)

        if "status" in request.POST:
            status = request.POST.get("status")
            if status in SupportTicket.Status.values:
                ticket.status = status
                ticket.save(update_fields=["status", "updated_at"])
                messages.success(request, "Statut du ticket mis a jour.")
            return redirect("support:admin_detail", pk=ticket.pk)

        form = SupportMessageForm(request.POST, request.FILES)
        if not form.is_valid():
            messages.error(request, "Le message ne peut pas etre vide.")
            return render(
                request,
                self.template_name,
                {"ticket": ticket, "form": form, "statuses": SupportTicket.Status.choices},
            )

        message = form.save(commit=False)
        message.ticket = ticket
        message.author = request.user
        message.save()

        if ticket.status == SupportTicket.Status.OPEN:
            ticket.status = SupportTicket.Status.IN_PROGRESS
            ticket.save(update_fields=["status", "updated_at"])

        messages.success(request, "Reponse envoyee.")
        return redirect("support:admin_detail", pk=ticket.pk)
