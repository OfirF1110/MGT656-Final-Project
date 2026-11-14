import os
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

class Command(BaseCommand):
    help = "Create/update the grader admin and member accounts from environment variables, plus their demo contacts."

    def handle(self, *args, **options):
        User = get_user_model()
        accounts = []
        for role in ("ADMIN", "MEMBER"):
            username = os.environ.get(f"GRADER_{role}_USERNAME", "").strip()
            password = os.environ.get(f"GRADER_{role}_PASSWORD", "")
            if not username or not password:
                raise CommandError(f"Set GRADER_{role}_USERNAME and GRADER_{role}_PASSWORD.")
            if len(username) > 150:
                raise CommandError("Grader username must be at most 150 characters.")
            try:
                validate_password(password, User(username=username))
            except ValidationError as exc:
                raise CommandError(f"Invalid {role.lower()} password: {'; '.join(exc.messages)}") from exc
            accounts.append((username, password, role == "ADMIN"))
        if accounts[0][0].casefold() == accounts[1][0].casefold():
            raise CommandError("Admin and member usernames must differ.")
        from contacts.demo import seed_demo_contacts

        demo_added = 0
        with transaction.atomic():
            for username, password, admin in accounts:
                user, created = User.objects.get_or_create(username=username)
                if not created and not user.check_password(password):
                    raise CommandError("Existing account has a different password; refusing to overwrite it.")
                user.is_active = True
                user.is_staff = admin
                user.is_superuser = admin
                if created:
                    user.set_password(password)
                user.save()
                demo_added += seed_demo_contacts(user)
        self.stdout.write(self.style.SUCCESS(
            f"Grader accounts ready. Demo contacts added: {demo_added}. No credentials printed."
        ))
