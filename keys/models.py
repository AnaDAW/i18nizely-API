from django.db import models


class Key(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='keys/', blank=True, null=True)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='keys')
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('name', 'project')

    def __str__(self):
        return self.name