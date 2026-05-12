from decimal import Decimal

from django.db import migrations


BADGE_THRESHOLDS = {
    "Bronze Supporter": Decimal("200.00"),
    "Silver Supporter": Decimal("500.00"),
    "Gold Supporter": Decimal("1000.00"),
    "VIP Supporter": Decimal("2500.00"),
}


def reset_badges_to_current_thresholds(apps, schema_editor):
    """Update default badge thresholds and reassign already granted badges."""
    Reward = apps.get_model("rewards", "Reward")
    Pledge = apps.get_model("pledges", "Pledge")
    Project = apps.get_model("projects", "Project")

    for project in Project.objects.all():
        for title, minimum_amount in BADGE_THRESHOLDS.items():
            Reward.objects.update_or_create(
                project=project,
                title=title,
                defaults={
                    "description": f"Badge {title} affiche sur le profil du contributeur.",
                    "minimum_amount": minimum_amount,
                    "reward_type": "badge",
                    "is_active": True,
                },
            )

    badge_titles = list(BADGE_THRESHOLDS.keys())
    badge_pledges = Pledge.objects.filter(reward__reward_type="badge").select_related(
        "project",
        "reward",
    )

    for pledge in badge_pledges:
        amount = Decimal(str(pledge.amount))
        matching_title = None

        for title, minimum_amount in sorted(BADGE_THRESHOLDS.items(), key=lambda item: item[1], reverse=True):
            if amount >= minimum_amount:
                matching_title = title
                break

        if matching_title is None:
            pledge.reward = None
        else:
            pledge.reward = Reward.objects.filter(
                project_id=pledge.project_id,
                title=matching_title,
                reward_type="badge",
                is_active=True,
            ).first()

        pledge.save(update_fields=["reward"])

    # If an old badge was removed from a small contribution, keep physical rewards untouched.
    Pledge.objects.filter(
        reward__isnull=False,
        reward__title__in=badge_titles,
        amount__lt=Decimal("200.00"),
    ).update(reward=None)


class Migration(migrations.Migration):

    dependencies = [
        ("rewards", "0003_update_default_reward_thresholds"),
        ("pledges", "0002_pledge_gross_amount_and_more"),
    ]

    operations = [
        migrations.RunPython(reset_badges_to_current_thresholds, migrations.RunPython.noop),
    ]
