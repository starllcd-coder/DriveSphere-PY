from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_auditlog"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="metadata",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
