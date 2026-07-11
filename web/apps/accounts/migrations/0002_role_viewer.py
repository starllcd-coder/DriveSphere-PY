from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="role",
            name="code",
            field=models.CharField(
                choices=[
                    ("ADMIN", "Admin"),
                    ("MANAGER", "Manager"),
                    ("AGENT", "Agent"),
                    ("MECHANIC", "Mechanic"),
                    ("ACCOUNTANT", "Accountant"),
                    ("VIEWER", "Viewer"),
                ],
                max_length=30,
                unique=True,
            ),
        ),
    ]
