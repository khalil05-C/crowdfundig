from django.db.models.signals import post_save
from django.dispatch import receiver
from pledges.models import Pledge
from notifications.models import Notification

@receiver(post_save, sender=Pledge)
def notify_on_pledge(sender, instance, created, **kwargs):
    """Notifier le porteur quand une contribution est reçue."""
    if created and instance.status == 'completed':
        backer_name = 'Anonyme' if instance.is_anonymous else instance.backer.get_full_name()
        Notification.objects.create(
            recipient         = instance.project.owner,
            notification_type = 'pledge_received',
            title             = 'Nouvelle contribution reçue !',
            message           = f'{backer_name} a contribué {instance.amount} MAD à votre projet "{instance.project.title}".',
            link              = f'/projects/{instance.project.slug}/'
        )