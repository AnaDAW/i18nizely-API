from django.db import models
from django.contrib.postgres.fields import ArrayField


class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='created_projects')
    main_language = models.CharField(max_length=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_language_codes(self) -> list:
        language_codes = []
        for lang in self.languages.all():
            language_codes.append(lang.code)
        return language_codes


class Language(models.Model):
    code = models.CharField(max_length=2)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='languages')
    translation_count = models.IntegerField(default=0)
    reviewed_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ('code', 'project')

    def __str__(self):
        return self.code


class Collaborator(models.Model):
    class Role(models.IntegerChoices):
        ADMIN = 1
        DEVELOPER = 2
        REVIEWER = 3
        TRANSLATOR = 4

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='collaborating_projects')
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='collaborators')
    roles = ArrayField(models.IntegerField(choices=Role.choices), max_length=3, default=list)

    class Meta:
        unique_together = ('user', 'project')


class Record(models.Model):
    class Type(models.IntegerChoices):
        CREATE_KEY = 1
        DELETE_KEY = 2
        EDIT_KEY = 3
        IMPORT_KEYS = 4
        EDIT_TRANSLATION = 5
        REVIEW_TRANSLATION = 6

    type = models.IntegerField(choices=Type.choices)
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='record')
    created_at = models.DateTimeField(auto_now_add=True)
