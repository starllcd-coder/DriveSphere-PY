from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="idempotency_key",
            field=models.CharField(blank=True, max_length=80, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="refund",
            name="idempotency_key",
            field=models.CharField(blank=True, max_length=80, null=True, unique=True),
        ),
    ]
