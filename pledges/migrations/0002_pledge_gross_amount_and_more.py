import pledges.models
from decimal import Decimal, ROUND_HALF_UP
from django.db import migrations, models


def populate_commission_fields(apps, schema_editor):
    """Backfill commission fields for existing pledges."""
    Pledge = apps.get_model("pledges", "Pledge")
    rate = Decimal("0.01")
    money_quantum = Decimal("0.01")

    for pledge in Pledge.objects.all():
        gross_amount = Decimal(str(pledge.amount)).quantize(money_quantum, rounding=ROUND_HALF_UP)
        commission_amount = (gross_amount * rate).quantize(money_quantum, rounding=ROUND_HALF_UP)
        net_amount = (gross_amount - commission_amount).quantize(money_quantum, rounding=ROUND_HALF_UP)

        pledge.gross_amount = gross_amount
        pledge.platform_commission_rate = rate
        pledge.platform_commission_amount = commission_amount
        pledge.project_net_amount = net_amount
        pledge.save(
            update_fields=[
                "gross_amount",
                "platform_commission_rate",
                "platform_commission_amount",
                "project_net_amount",
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        ('pledges', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pledge',
            name='gross_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='pledge',
            name='platform_commission_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='pledge',
            name='platform_commission_rate',
            field=models.DecimalField(decimal_places=4, default=pledges.models.get_platform_commission_rate, max_digits=5),
        ),
        migrations.AddField(
            model_name='pledge',
            name='project_net_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.RunPython(populate_commission_fields, migrations.RunPython.noop),
    ]
