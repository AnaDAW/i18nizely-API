from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class DateFormat(models.IntegerChoices):
        DMY = 1
        MDY = 2

    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    image = models.ImageField(upload_to='avatars/', blank=True, null=True)
    language = models.CharField(max_length=2, default='en')
    format_24h = models.BooleanField(default=True)
    date_format = models.IntegerField(choices=DateFormat.choices, default=DateFormat.DMY)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email


class Notification(models.Model):
    class Type(models.IntegerChoices):
        COMMENT = 1
        INVITATION = 2

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='notifications')
    type = models.IntegerField(choices=Type.choices)
    is_read = models.BooleanField(default=False)
    comment = models.ForeignKey('translations.Comment', on_delete=models.CASCADE, null=True)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)