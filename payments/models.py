from django.db import models
from django.conf import settings
from decimal import Decimal

class Payment(models.Model):

    class Status(models.TextChoices):
        INITIATED  = 'initiated',  'Initiée'
        COMPLETED  = 'completed',  'Complétée'
        FAILED     = 'failed',     'Échouée'
        REFUNDED   = 'refunded',   'Remboursée'

    class Method(models.TextChoices):
        STRIPE        = 'stripe',        'Carte bancaire Stripe'
        BANK_TRANSFER = 'bank_transfer', 'Virement bancaire'
        CMI           = 'cmi',           'CMI (Maroc)'

    pledge         = models.OneToOneField('pledges.Pledge', on_delete=models.CASCADE, related_name='payment')
    amount         = models.DecimalField(max_digits=10, decimal_places=2)
    method         = models.CharField(max_length=20, choices=Method.choices)
    status         = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIATED)
    transaction_id = models.CharField(max_length=200, unique=True)
    stripe_session_id = models.CharField(max_length=255, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    platform_fee   = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    net_amount     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paiement {self.transaction_id} – {self.amount} MAD"

    def calculate_fees(self):
        fee_rate         = Decimal('0.05')
        self.platform_fee = round(self.amount * fee_rate, 2)
        self.net_amount   = self.amount - self.platform_fee
        self.save()

class Withdrawal(models.Model):

    class Status(models.TextChoices):
        PENDING   = 'pending',   'En attente'
        APPROVED  = 'approved',  'Approuvée'
        PROCESSED = 'processed', 'Traitée'
        REJECTED  = 'rejected',  'Rejetée'

    project_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='withdrawals'
    )
    project       = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='withdrawals'
    )
    amount        = models.DecimalField(max_digits=12, decimal_places=2)
    bank_rib      = models.CharField(max_length=24)
    status        = models.CharField(
        max_length=20, choices=Status.choices,
        default=Status.PENDING
    )
    admin_notes   = models.TextField(blank=True)
    requested_at  = models.DateTimeField(auto_now_add=True)
    processed_at  = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Retrait {self.amount} MAD – {self.project.title}"
