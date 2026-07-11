from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Branch",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=120, unique=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="BusinessProfile",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("business_name", models.CharField(blank=True, default="", max_length=200)),
                ("commercial_registration_number", models.CharField(blank=True, default="", max_length=100)),
                ("vat_no", models.CharField(blank=True, default="", max_length=100)),
                ("address", models.CharField(blank=True, default="", max_length=300)),
                ("phone_number", models.CharField(blank=True, default="", max_length=60)),
                ("email", models.EmailField(blank=True, default="", max_length=254)),
                ("currency_code", models.CharField(blank=True, default="OMR", max_length=10)),
                ("currency_symbol", models.CharField(blank=True, default="ff", max_length=10)),
                ("exchange_rates", models.JSONField(blank=True, default=dict)),
                ("exchange_rates_updated_at", models.DateTimeField(blank=True, null=True)),
                ("logo", models.ImageField(blank=True, null=True, upload_to="business/logo/")),
            ],
            options={
                "verbose_name": "Business Profile",
                "verbose_name_plural": "Business Profile",
            },
        ),
        migrations.CreateModel(
            name="DocumentNumbering",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("doc_type", models.CharField(max_length=40, unique=True)),
                ("prefix", models.CharField(blank=True, default="DS", max_length=20)),
                ("separator", models.CharField(blank=True, default="-", max_length=5)),
                ("padding", models.PositiveIntegerField(default=6)),
                ("next_number", models.PositiveIntegerField(default=1)),
            ],
            options={
                "ordering": ["doc_type"],
            },
        ),
        migrations.CreateModel(
            name="DatabaseProfile",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("provider", models.CharField(choices=[("POSTGRES", "PostgreSQL"), ("NEON", "Neon")], default="POSTGRES", max_length=20)),
                ("host", models.CharField(blank=True, default="", max_length=200)),
                ("port", models.PositiveIntegerField(default=5432)),
                ("database_name", models.CharField(blank=True, default="", max_length=200)),
                ("username", models.CharField(blank=True, default="", max_length=200)),
                ("password", models.CharField(blank=True, default="", max_length=200)),
                ("sslmode", models.CharField(blank=True, default="require", max_length=30)),
                ("is_active", models.BooleanField(default=False)),
            ],
            options={
                "verbose_name": "Database Profile",
                "verbose_name_plural": "Database Profile",
            },
        ),
    ]
