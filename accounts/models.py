from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):

    class Role(models.TextChoices):
        CONTRIBUTOR   = 'contributor',    'Contributeur'
        PROJECT_OWNER = 'project_owner',  'Porteur de projet'
        ADMIN         = 'admin',          'Administrateur'

    class NotificationPreference(models.TextChoices):
        EMAIL = "email", "Email"
        PHONE = "phone", "Telephone"
        BOTH = "both", "Email et telephone"

    email      = models.EmailField(unique=True)
    role       = models.CharField(max_length=20, choices=Role.choices, default=Role.CONTRIBUTOR)
    phone      = models.CharField(max_length=20, blank=True)
    notification_preference = models.CharField(
        max_length=10,
        choices=NotificationPreference.choices,
        default=NotificationPreference.EMAIL,
    )
    bio        = models.TextField(blank=True)
    avatar     = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
