from datetime import datetime
from django.db import models


class Translation(models.Model):
    text = models.TextField()
    language = models.CharField(max_length=2)
    key = models.ForeignKey('keys.Key', on_delete=models.CASCADE, related_name='translations')
    is_reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='review_set')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(default=datetime.now)

    class Meta:
        unique_together = ('key', 'language')

    def __str__(self):
        return self.text


class Version(models.Model):
    text = models.TextField()
    translation = models.ForeignKey('translations.Translation', on_delete=models.CASCADE, related_name='versions')
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField()


class Comment(models.Model):
    text = models.TextField()
    translation = models.ForeignKey('translations.Translation', on_delete=models.CASCADE, related_name='comments')
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text
