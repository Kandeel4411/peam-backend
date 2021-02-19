from django.db import transaction
from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError
from allauth.account.models import EmailAddress


class Command(createsuperuser.Command):
    help = "Crate a superuser, and allow password to be provided"

    def add_arguments(self, parser) -> None:
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "--password",
            dest="password",
            default=None,
            help="Specifies the password for the superuser.",
        )

    def handle(self, *args, **options) -> None:
        password: str = options.get("password")
        email: str = options.get("email")
        username: str = options.get("username")
        database: str = options.get("database")

        if password and not username:
            raise CommandError("--username is required if specifying --password")
        if email and EmailAddress._default_manager.filter(email=email).exists():
            raise CommandError("User with given email already exists.")

        with transaction.atomic():
            super(Command, self).handle(*args, **options)

            user = self.UserModel._default_manager.db_manager(database).get(username=username)

            if email:
                # Verify user's email
                EmailAddress._default_manager.create(
                    user=user,
                    email=user.email,
                    primary=True,
                    verified=True,
                )

            if password:
                user.set_password(password)
                user.save()
