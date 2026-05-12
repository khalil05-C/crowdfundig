from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings


@dataclass
class StripeCheckoutSession:
    """Small adapter around Stripe Checkout session data."""

    id: str
    url: str
    payment_intent: str = ""


def amount_to_stripe_cents(amount):
    """Convert a Decimal money amount to Stripe minor units."""
    return int((Decimal(str(amount)) * Decimal("100")).quantize(Decimal("1")))


def is_stripe_configured():
    """Return True when the project has the keys needed to open Stripe Checkout."""
    return bool(
        getattr(settings, "STRIPE_PUBLIC_KEY", "")
        and getattr(settings, "STRIPE_SECRET_KEY", "")
    )


def create_stripe_checkout_session(pledge, success_url, cancel_url):
    """Create a Stripe Checkout session."""
    if not is_stripe_configured():
        raise RuntimeError("Stripe n'est pas configure.")

    try:
        import stripe
    except ImportError:
        raise RuntimeError("Le package Stripe n'est pas installe.")

    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": settings.STRIPE_CURRENCY,
                    "product_data": {
                        "name": f"Contribution - {pledge.project.title}",
                    },
                    "unit_amount": amount_to_stripe_cents(pledge.amount),
                },
                "quantity": 1,
            }
        ],
        metadata={
            "pledge_id": str(pledge.pk),
            "project_id": str(pledge.project_id),
            "backer_id": str(pledge.backer_id),
        },
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return StripeCheckoutSession(
        id=session.id,
        url=session.url,
        payment_intent=getattr(session, "payment_intent", "") or "",
    )
