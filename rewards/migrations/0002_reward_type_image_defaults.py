# Generated for contributor rewards.

from decimal import Decimal

from django.db import migrations, models


def create_default_rewards(apps, schema_editor):
    """Seed the standard badges and T-shirt for existing projects."""
    Project = apps.get_model("projects", "Project")
    Reward = apps.get_model("rewards", "Reward")

    defaults = [
        ("Bronze Supporter", "Badge Bronze Supporter affiche sur le profil du contributeur.", Decimal("50.00"), "badge"),
        ("Silver Supporter", "Badge Silver Supporter affiche sur le profil du contributeur.", Decimal("100.00"), "badge"),
        ("Gold Supporter", "Badge Gold Supporter affiche sur le profil du contributeur.", Decimal("250.00"), "badge"),
        ("VIP Supporter", "Badge VIP Supporter affiche sur le profil du contributeur.", Decimal("500.00"), "badge"),
        ("T-shirt officiel", "Cadeau physique reserve aux contributions de 250 MAD et plus.", Decimal("250.00"), "physical"),
    ]

    for project in Project.objects.all():
        for title, description, minimum_amount, reward_type in defaults:
            Reward.objects.get_or_create(
                project=project,
                title=title,
                defaults={
                    "description": description,
                    "minimum_amount": minimum_amount,
                    "reward_type": reward_type,
                    "is_active": True,
                },
            )


class Migration(migrations.Migration):

    dependencies = [
        ("rewards", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="reward",
            name="reward_type",
            field=models.CharField(
                choices=[("badge", "Badge"), ("physical", "Cadeau physique")],
                default="badge",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="reward",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="rewards/"),
        ),
        migrations.AlterModelOptions(
            name="reward",
            options={"ordering": ["minimum_amount", "title"]},
        ),
        migrations.RunPython(create_default_rewards, migrations.RunPython.noop),
    ]
