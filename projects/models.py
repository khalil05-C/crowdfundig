from django.conf import settings
from django.db import models
from urllib.parse import parse_qs, urlparse

class Category(models.Model):
    name       = models.CharField(max_length=100)
    slug       = models.SlugField(unique=True)
    color      = models.CharField(max_length=7, default='#3498db')
    is_active  = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Project(models.Model):

    class Status(models.TextChoices):
        DRAFT     = 'draft',     'Brouillon'
        PENDING   = 'pending',   'En attente'
        ACTIVE    = 'active',    'Actif'
        FUNDED    = 'funded',    'Financé'
        FAILED    = 'failed',    'Non financé'
        CANCELLED = 'cancelled', 'Annulé'

    class FundingType(models.TextChoices):
        ALL_OR_NOTHING = 'all_or_nothing', 'Tout ou rien'
        FLEXIBLE       = 'flexible',       'Flexible'

    title             = models.CharField(max_length=200)
    slug              = models.SlugField(unique=True, max_length=220)
    short_description = models.CharField(max_length=300)
    description       = models.TextField()
    owner             = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects')
    category          = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='projects')
    goal_amount       = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount    = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    funding_type      = models.CharField(max_length=20, choices=FundingType.choices, default=FundingType.ALL_OR_NOTHING)
    end_date          = models.DateTimeField()
    status            = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    cover_image       = models.ImageField(upload_to='projects/covers/', blank=True, null=True)
    video_url         = models.URLField(blank=True)
    views_count       = models.PositiveIntegerField(default=0)
    backers_count     = models.PositiveIntegerField(default=0)
    created_at        = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def progress_percent(self):
        if self.goal_amount == 0:
            return 0
        return min(int((self.current_amount / self.goal_amount) * 100), 100)

    @property
    def days_remaining(self):
        from django.utils import timezone
        delta = self.end_date - timezone.now()
        return max(delta.days, 0)

    @property
    def video_embed_url(self):
        if not self.video_url:
            return ""

        parsed_url = urlparse(self.video_url)
        hostname = parsed_url.hostname or ""
        path = parsed_url.path.strip("/")
        video_id = ""

        if hostname.endswith("youtu.be"):
            video_id = path.split("/")[0]
        elif "youtube.com" in hostname:
            if path == "watch":
                video_id = parse_qs(parsed_url.query).get("v", [""])[0]
            elif path.startswith("embed/"):
                video_id = path.split("/")[1]
            elif path.startswith("shorts/"):
                video_id = path.split("/")[1]

        if video_id:
            return f"https://www.youtube.com/embed/{video_id}"

        return self.video_url
