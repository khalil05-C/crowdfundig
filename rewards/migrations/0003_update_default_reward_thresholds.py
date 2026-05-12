from decimal import Decimal

from django.db import migrations


def update_default_reward_thresholds(apps, schema_editor):
    """Keep built-in rewards aligned with the configured contributor levels."""
    Reward = apps.get_model("rewards", "Reward")
    thresholds = {
        "Bronze Supporter": Decimal("50.00"),
        "Silver Supporter": Decimal("100.00"),
        "Gold Supporter": Decimal("250.00"),
        "VIP Supporter": Decimal("500.00"),
        "T-shirt officiel": Decimal("250.00"),
    }

    for title, minimum_amount in thresholds.items():
        Reward.objects.filter(title=title).update(minimum_amount=minimum_amount)


class Migration(migrations.Migration):

    dependencies = [
        ("rewards", "0002_reward_type_image_defaults"),
    ]

    operations = [
        migrations.RunPython(update_default_reward_thresholds, migrations.RunPython.noop),
    ]
