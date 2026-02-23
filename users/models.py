from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """
    Extension of the built-in User model.
    Keeps profile-level data so we can later plug in
    django-allauth or social auth without changing core models.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.display_name or self.user.get_username()

