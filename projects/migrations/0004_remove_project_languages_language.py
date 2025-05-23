# Generated by Django 5.2 on 2025-05-08 22:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0003_alter_collaborator_roles'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='languages',
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=2)),
                ('count', models.IntegerField(default=0)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='languages', to='projects.project')),
            ],
        ),
    ]
