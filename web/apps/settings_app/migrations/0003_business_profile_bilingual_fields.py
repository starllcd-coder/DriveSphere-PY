from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("settings_app", "0002_alter_branch_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="businessprofile",
            name="business_name_ar",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="businessprofile",
            name="address_ar",
            field=models.CharField(blank=True, default="", max_length=300),
        ),
        migrations.AddField(
            model_name="businessprofile",
            name="phone_number_ar",
            field=models.CharField(blank=True, default="", max_length=60),
        ),
        migrations.AddField(
            model_name="businessprofile",
            name="email_ar",
            field=models.EmailField(blank=True, default="", max_length=254),
        ),
        migrations.AddField(
            model_name="businessprofile",
            name="website",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="businessprofile",
            name="website_ar",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
    ]
