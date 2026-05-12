from decimal import Decimal

from django.db import models


class Reward(models.Model):
    """Reward offered to contributors for a project."""

    class RewardType(models.TextChoices):
        BADGE = "badge", "Badge"
        PHYSICAL = "physical", "Cadeau physique"

    BADGE_LEVELS = [
        ("Bronze Supporter", Decimal("200.00")),
        ("Silver Supporter", Decimal("500.00")),
        ("Gold Supporter", Decimal("1000.00")),
        ("VIP Supporter", Decimal("2500.00")),
    ]

    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="rewards"
    )
    title = models.CharField(max_length=150)
    description = models.TextField()
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reward_type = models.CharField(
        max_length=20,
        choices=RewardType.choices,
        default=RewardType.BADGE,
    )
    quantity_available = models.PositiveIntegerField(null=True, blank=True)
    quantity_claimed = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="rewards/", blank=True, null=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    ships_internationally = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["minimum_amount", "title"]

    def __str__(self):
        return f"{self.title} ({self.minimum_amount} MAD)"

    @property
    def name(self):
        """Backward-friendly alias for the reward title."""
        return self.title

    @property
    def is_badge(self):
        """Return True when this reward is a supporter badge."""
        return self.reward_type == self.RewardType.BADGE

    @property
    def is_physical(self):
        """Return True when this reward is a physical gift."""
        return self.reward_type == self.RewardType.PHYSICAL

    @property
    def is_available(self):
        """Return True when the reward can still be selected."""
        return self.quantity_available is None or self.quantity_available > 0

    def is_eligible_for(self, amount):
        """Return True when the contribution amount can unlock this reward."""
        return (
            self.is_active
            and self.is_available
            and Decimal(str(amount)) >= self.minimum_amount
        )

    def claim(self):
        """Reserve one unit of this reward when a contributor selects it."""
        if not self.is_available:
            return False

        if self.quantity_available is not None:
            self.quantity_available -= 1

        self.quantity_claimed += 1
        self.save(update_fields=["quantity_available", "quantity_claimed"])
        return True

    @classmethod
    def ensure_default_rewards(cls, project):
        """Create the standard badge and T-shirt rewards for a project if missing."""
        defaults = [
            {
                "title": title,
                "description": f"Badge {title} affiche sur le profil du contributeur.",
                "minimum_amount": amount,
                "reward_type": cls.RewardType.BADGE,
            }
            for title, amount in cls.BADGE_LEVELS
        ]
        defaults.append(
            {
                "title": "T-shirt officiel",
                "description": "Cadeau physique reserve aux contributions de 1000 MAD et plus.",
                "minimum_amount": Decimal("1000.00"),
                "reward_type": cls.RewardType.PHYSICAL,
            }
        )

        for data in defaults:
            reward, created = cls.objects.get_or_create(
                project=project,
                title=data["title"],
                defaults=data,
            )
            if not created and reward.reward_type == data["reward_type"]:
                update_fields = []
                if reward.minimum_amount != data["minimum_amount"]:
                    reward.minimum_amount = data["minimum_amount"]
                    update_fields.append("minimum_amount")
                if update_fields:
                    reward.save(update_fields=update_fields)

    @classmethod
    def available_for_amount(cls, project, amount):
        """Return active rewards available for a project and contribution amount."""
        cls.ensure_default_rewards(project)
        return (
            cls.objects.filter(
                project=project,
                is_active=True,
                minimum_amount__lte=amount,
            )
            .filter(
                models.Q(quantity_available__isnull=True)
                | models.Q(quantity_available__gt=0)
            )
            .order_by("minimum_amount", "title")
        )

    @classmethod
    def badge_for_amount(cls, project, amount):
        """Return the best badge unlocked by the given contribution amount."""
        cls.ensure_default_rewards(project)
        return (
            cls.objects.filter(
                project=project,
                is_active=True,
                reward_type=cls.RewardType.BADGE,
                minimum_amount__lte=amount,
            )
            .order_by("-minimum_amount")
            .first()
        )
