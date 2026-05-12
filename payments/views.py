from decimal import Decimal, InvalidOperation
import uuid

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import TemplateView, View

from pledges.models import Pledge
from projects.models import Project
from notifications.models import Notification
from notifications.services import create_notification

from .models import Payment, Withdrawal
from .services import create_stripe_checkout_session, is_stripe_configured


def confirm_pledge_payment(pledge, transaction_id, user):
    """Complete a pledge payment and send the related notifications."""
    previous_amount = pledge.project.current_amount
    pledge.complete_payment(transaction_id)

    create_notification(
        recipient=user,
        notification_type=Notification.Type.PAYMENT_CONFIRMED,
        title="Paiement confirme",
        message=f"Votre paiement de {pledge.amount} MAD pour {pledge.project.title} est confirme.",
        link="/pledges/history/",
    )

    if previous_amount < pledge.project.goal_amount <= pledge.project.current_amount:
        create_notification(
            recipient=pledge.project.owner,
            notification_type=Notification.Type.PROJECT_FUNDED,
            title="Objectif atteint",
            message=f"Votre projet {pledge.project.title} a atteint son objectif.",
            link=f"/projects/{pledge.project.slug}/",
        )


class ProcessPaymentView(LoginRequiredMixin, TemplateView):
    template_name = "payments/process.html"

    def dispatch(self, request, *args, **kwargs):
        self.pledge = get_object_or_404(Pledge, pk=kwargs["pledge_id"], backer=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pledge"] = self.pledge
        context["stripe_public_key"] = settings.STRIPE_PUBLIC_KEY
        context["stripe_available"] = is_stripe_configured()
        return context

    def post(self, request, *args, **kwargs):
        if hasattr(self.pledge, "payment"):
            if self.pledge.payment.status == Payment.Status.FAILED:
                self.pledge.payment.delete()
            else:
                messages.info(request, "Cette contribution a deja un paiement.")
                return redirect("projects:project_detail", slug=self.pledge.project.slug)

        method = request.POST.get("payment_method", Payment.Method.BANK_TRANSFER)
        if method not in Payment.Method.values:
            method = Payment.Method.BANK_TRANSFER

        payment = Payment.objects.create(
            pledge=self.pledge,
            amount=self.pledge.amount,
            method=method,
            status=Payment.Status.INITIATED if method == Payment.Method.STRIPE else Payment.Status.COMPLETED,
            transaction_id=str(uuid.uuid4()),
        )

        if method == Payment.Method.STRIPE:
            if not is_stripe_configured():
                payment.delete()
                messages.error(
                    request,
                    "Stripe n'est pas encore configure. Merci de choisir une autre methode de paiement.",
                )
                return redirect("payments:process_payment", pledge_id=self.pledge.pk)

            success_url = request.build_absolute_uri(
                reverse("payments:stripe_success", kwargs={"pledge_id": self.pledge.pk})
            )
            cancel_url = request.build_absolute_uri(
                reverse("payments:stripe_cancel", kwargs={"pledge_id": self.pledge.pk})
            )
            try:
                stripe_session = create_stripe_checkout_session(self.pledge, success_url, cancel_url)
            except Exception:
                payment.delete()
                messages.error(
                    request,
                    "Impossible d'ouvrir Stripe Checkout pour le moment. Verifiez les cles Stripe.",
                )
                return redirect("payments:process_payment", pledge_id=self.pledge.pk)

            payment.stripe_session_id = stripe_session.id
            payment.stripe_payment_intent_id = stripe_session.payment_intent
            payment.save(update_fields=["stripe_session_id", "stripe_payment_intent_id"])
            return redirect(stripe_session.url)

        payment.calculate_fees()
        confirm_pledge_payment(self.pledge, payment.transaction_id, request.user)

        messages.success(request, f"Paiement de {self.pledge.amount} MAD confirme !")
        return redirect("projects:project_detail", slug=self.pledge.project.slug)


class StripeSuccessView(LoginRequiredMixin, View):
    """Handle the return from Stripe Checkout after a successful card payment."""

    def get(self, request, pledge_id):
        pledge = get_object_or_404(Pledge, pk=pledge_id, backer=request.user)
        payment = get_object_or_404(Payment, pledge=pledge, method=Payment.Method.STRIPE)

        if payment.status != Payment.Status.COMPLETED:
            payment.status = Payment.Status.COMPLETED
            payment.save(update_fields=["status"])
            payment.calculate_fees()
            confirm_pledge_payment(pledge, payment.transaction_id, request.user)

        messages.success(request, "Paiement Stripe confirme !")
        return redirect("projects:project_detail", slug=pledge.project.slug)


class StripeCancelView(LoginRequiredMixin, View):
    """Handle cancellation from Stripe Checkout."""

    def get(self, request, pledge_id):
        pledge = get_object_or_404(Pledge, pk=pledge_id, backer=request.user)
        payment = get_object_or_404(Payment, pledge=pledge, method=Payment.Method.STRIPE)

        if payment.status == Payment.Status.INITIATED:
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status"])

        messages.warning(request, "Paiement Stripe annule.")
        return redirect("payments:process_payment", pledge_id=pledge.pk)


class WithdrawalRequestView(LoginRequiredMixin, TemplateView):
    template_name = "payments/withdrawal.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, slug=kwargs["project_slug"], owner=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        return context

    def post(self, request, *args, **kwargs):
        try:
            amount = Decimal(request.POST.get("amount", "0"))
        except InvalidOperation:
            messages.error(request, "Montant invalide.")
            return redirect("payments:withdrawal", project_slug=self.project.slug)

        bank_rib = request.POST.get("bank_rib", "").replace(" ", "")

        if amount <= 0 or amount > self.project.current_amount:
            messages.error(request, "Le montant demande n'est pas disponible.")
            return redirect("payments:withdrawal", project_slug=self.project.slug)

        if not bank_rib.isdigit() or len(bank_rib) != 24:
            messages.error(request, "Le RIB doit contenir exactement 24 chiffres.")
            return redirect("payments:withdrawal", project_slug=self.project.slug)

        Withdrawal.objects.create(
            project_owner=request.user,
            project=self.project,
            amount=amount,
            bank_rib=bank_rib,
        )
        messages.success(request, "Demande de retrait envoyee ! Traitement sous 3-5 jours ouvres.")
        return redirect("/dashboard/")
