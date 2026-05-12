from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models


def get_platform_commission_rate():
    """Return the platform commission rate configured in Django settings."""
    return Decimal(str(getattr(settings, "PLATFORM_COMMISSION_RATE", Decimal("0.01"))))


class Pledge(models.Model):
    """Contribution made by a backer to a project."""

    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        COMPLETED = "completed", "Complétée"
        FAILED = "failed", "Échouée"
        REFUNDED = "refunded", "Remboursée"
        CANCELLED = "cancelled", "Annulée"

    backer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="pledges")
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="pledges")
    reward = models.ForeignKey("rewards.Reward", on_delete=models.SET_NULL, null=True, blank=True, related_name="pledges")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    project_net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    platform_commission_rate = models.DecimalField(max_digits=5, decimal_places=4, default=get_platform_commission_rate)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_id = models.CharField(max_length=200, blank=True)
    is_anonymous = models.BooleanField(default=False)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.backer} -> {self.project} : {self.amount} MAD"

    @property
    def earned_badge(self):
        """Return the supporter badge unlocked by this pledge amount."""
        from rewards.models import Reward

        return Reward.badge_for_amount(self.project, self.amount)

    def calculate_platform_commission(self):
        """Calculate gross amount, platform commission and project net amount."""
        money_quantum = Decimal("0.01")
        self.gross_amount = Decimal(str(self.amount)).quantize(money_quantum, rounding=ROUND_HALF_UP)
        self.platform_commission_rate = get_platform_commission_rate()
        self.platform_commission_amount = (self.gross_amount * self.platform_commission_rate).quantize(
            money_quantum,
            rounding=ROUND_HALF_UP,
        )
        self.project_net_amount = (self.gross_amount - self.platform_commission_amount).quantize(
            money_quantum,
            rounding=ROUND_HALF_UP,
        )

    def save(self, *args, **kwargs):
        """Calculate commission, attach a badge and reserve selected reward stock."""
        is_new = self.pk is None
        self.calculate_platform_commission()

        if self.project_id and not self.reward_id:
            from rewards.models import Reward

            self.reward = Reward.badge_for_amount(self.project, self.amount)

        super().save(*args, **kwargs)

        if is_new and self.reward_id:
            self.reward.claim()

    def complete_payment(self, payment_id):
        """Mark the pledge as paid and update project funding counters."""
        if self.status == self.Status.COMPLETED:
            return

        self.status = self.Status.COMPLETED
        self.payment_id = payment_id
        self.save()
        self.project.current_amount += self.amount
        self.project.backers_count += 1
        self.project.save()
