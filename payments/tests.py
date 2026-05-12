from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import User
from pledges.models import Pledge
from projects.models import Category, Project

from .models import Payment
from .services import StripeCheckoutSession


class StripePaymentTest(TestCase):
    """Tests for the Stripe card payment flow."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner_pay@test.com",
            email="owner_pay@test.com",
            password="TestPass123",
            role="project_owner",
        )
        self.backer = User.objects.create_user(
            username="backer_pay@test.com",
            email="backer_pay@test.com",
            password="TestPass123",
            role="contributor",
        )
        self.category = Category.objects.create(name="Pay", slug="pay")
        self.project = Project.objects.create(
            title="Projet paiement",
            slug="projet-paiement",
            short_description="Test paiement",
            description="Test paiement",
            owner=self.owner,
            category=self.category,
            goal_amount=Decimal("1000.00"),
            end_date=timezone.now() + timedelta(days=30),
            status=Project.Status.ACTIVE,
        )
        self.pledge = Pledge.objects.create(
            backer=self.backer,
            project=self.project,
            amount=Decimal("100.00"),
            status=Pledge.Status.PENDING,
        )

    @override_settings(STRIPE_PUBLIC_KEY="pk_test_123", STRIPE_SECRET_KEY="sk_test_123")
    @patch("payments.views.create_stripe_checkout_session")
    def test_stripe_payment_creates_checkout_session(self, create_session):
        """Posting Stripe creates an initiated payment and redirects to Stripe Checkout."""
        create_session.return_value = StripeCheckoutSession(
            id="cs_test_123",
            url="https://checkout.stripe.com/c/pay/cs_test_123",
            payment_intent="pi_test_123",
        )

        self.client.force_login(self.backer)
        response = self.client.post(
            f"/payments/pay/{self.pledge.pk}/",
            {"payment_method": Payment.Method.STRIPE},
        )
        payment = Payment.objects.get(pledge=self.pledge)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://checkout.stripe.com/c/pay/cs_test_123")
        self.assertEqual(payment.method, Payment.Method.STRIPE)
        self.assertEqual(payment.status, Payment.Status.INITIATED)
        self.assertEqual(payment.stripe_session_id, "cs_test_123")
        self.assertEqual(payment.stripe_payment_intent_id, "pi_test_123")

    @override_settings(STRIPE_PUBLIC_KEY="", STRIPE_SECRET_KEY="")
    def test_stripe_payment_without_keys_returns_to_payment_page(self):
        """Posting Stripe without keys does not create a fake Stripe payment."""
        self.client.force_login(self.backer)
        response = self.client.post(
            f"/payments/pay/{self.pledge.pk}/",
            {"payment_method": Payment.Method.STRIPE},
        )

        self.assertRedirects(response, f"/payments/pay/{self.pledge.pk}/")
        self.assertFalse(Payment.objects.filter(pledge=self.pledge).exists())

    @override_settings(STRIPE_PUBLIC_KEY="pk_test_123", STRIPE_SECRET_KEY="sk_test_123")
    @patch("payments.views.create_stripe_checkout_session")
    def test_stripe_success_confirms_payment(self, create_session):
        """Stripe success marks the payment and pledge as completed."""
        create_session.return_value = StripeCheckoutSession(
            id="cs_test_123",
            url="https://checkout.stripe.com/c/pay/cs_test_123",
            payment_intent="pi_test_123",
        )

        self.client.force_login(self.backer)
        self.client.post(
            f"/payments/pay/{self.pledge.pk}/",
            {"payment_method": Payment.Method.STRIPE},
        )

        response = self.client.get(f"/payments/stripe/success/{self.pledge.pk}/")
        self.pledge.refresh_from_db()
        payment = Payment.objects.get(pledge=self.pledge)
        self.project.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(payment.status, Payment.Status.COMPLETED)
        self.assertEqual(self.pledge.status, Pledge.Status.COMPLETED)
        self.assertEqual(self.project.current_amount, Decimal("100.00"))
