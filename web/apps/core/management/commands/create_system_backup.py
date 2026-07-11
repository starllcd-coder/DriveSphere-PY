from datetime import timedelta
import os
from pathlib import Path
import zipfile

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Create a timestamped backup zip (database + media files)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--retention-days",
            type=int,
            default=int(os.getenv("BACKUP_RETENTION_DAYS", "14")),
            help="Delete backup files older than this many days.",
        )

    def handle(self, *args, **options):
        retention_days = max(int(options["retention_days"]), 1)
        now = timezone.now()

        backup_dir = Path(settings.BASE_DIR) / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        filename = f"drivesphere-backup-{now.strftime('%Y%m%d-%H%M%S')}.zip"
        target = backup_dir / filename

        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
            db_name = settings.DATABASES.get("default", {}).get("NAME")
            if db_name:
                db_path = Path(db_name)
                if not db_path.is_absolute():
                    db_path = Path(settings.BASE_DIR) / db_path
                if not db_path.exists():
                    alt_path = Path(settings.BASE_DIR).parent / Path(db_name)
                    if alt_path.exists():
                        db_path = alt_path
                if db_path.exists():
                    zf.write(db_path, arcname=f"db/{db_path.name}")

            media_root = Path(settings.MEDIA_ROOT)
            if media_root.exists():
                for item in media_root.rglob("*"):
                    if item.is_file():
                        arcname = Path("media") / item.relative_to(media_root)
                        zf.write(item, arcname=str(arcname))

        cutoff = now - timedelta(days=retention_days)
        removed = 0
        for candidate in backup_dir.glob("drivesphere-backup-*.zip"):
            try:
                if timezone.datetime.fromtimestamp(
                    candidate.stat().st_mtime, tz=timezone.get_current_timezone()
                ) < cutoff:
                    candidate.unlink(missing_ok=True)
                    removed += 1
            except Exception:
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f"Backup created: {target} (retention={retention_days}d, removed={removed})"
            )
        )
