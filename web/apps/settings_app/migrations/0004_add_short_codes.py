from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("settings_app", "0003_business_profile_bilingual_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="branch",
            name="code",
            field=models.CharField(blank=True, default="", max_length=10),
        ),
        migrations.AddField(
            model_name="businessprofile",
            name="short_code",
            field=models.CharField(blank=True, default="", max_length=10),
        ),
        migrations.AddField(
            model_name="documentnumbering",
            name="doc_code",
            field=models.CharField(blank=True, default="", max_length=10),
        ),
    ]
