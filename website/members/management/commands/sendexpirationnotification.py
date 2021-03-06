from django.core.management.base import BaseCommand

from members import emails


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry-run",
            default=False,
            help="Dry run instead of sending e-mail",
        )

    def handle(self, *args, **options):
        emails.send_expiration_announcement(bool(options["dry-run"]))
