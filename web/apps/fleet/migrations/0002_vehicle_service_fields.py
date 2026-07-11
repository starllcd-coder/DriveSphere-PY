from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("fleet", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="vehicle",
            name="last_service_odometer",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="service_interval_km",
            field=models.PositiveIntegerField(default=10000),
        ),
    ]
