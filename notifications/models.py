from django.conf import settings
from django.db import models


class Notification(models.Model):
    """In-app notification delivered to a user."""

    class Type(models.TextChoices):
        DONATION_CREATED = "donation_created", "Donation creee"
        PAYMENT_CONFIRMED = "payment_confirmed", "Paiement confirme"
        REWARD_SELECTED = "reward_selected", "Recompense selectionnee"
        PLEDGE_RECEIVED = "pledge_received", "Nouvelle contribution"
        PROJECT_FUNDED = "project_funded", "Projet finance"
        PROJECT_UPDATED = "project_updated", "Mise a jour projet"
        PROJECT_APPROVED = "project_approved", "Projet approuve"
        PROJECT_REJECTED = "project_rejected", "Projet refuse"
        COMMENT_REPLY = "comment_reply", "Reponse commentaire"

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=30, choices=Type.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.URLField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} -> {self.recipient}"

    def mark_as_read(self):
        """Mark this notification as read."""
        self.is_read = True
        self.save(update_fields=["is_read"])
