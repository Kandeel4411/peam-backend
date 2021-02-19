import factory
from factory.django import DjangoModelFactory
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email: str = factory.Faker("email")
    first_name: str = factory.Faker("first_name")
    last_name: str = factory.Faker("last_name")
    username: str = factory.Faker("first_name")
    password: str = factory.Faker("password")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our custom call."""
        user = super()._create(model_class, *args, **kwargs)

        # Setting password correctly
        user.set_password(kwargs["password"])
        user.save()

        EmailAddress._default_manager.create(  # Verify user's email
            user=user,
            email=user.email,
            primary=True,
            verified=True,
        )

        return user
