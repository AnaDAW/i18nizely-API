from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.serializers import ModelSerializer

from .models import Project, Collaborator, Record
from users.serializers import UserDetailSerializer


class CollaboratorSerializer(ModelSerializer):
    user = UserDetailSerializer(many=False, read_only=True)

    class Meta:
        model = Collaborator
        fields = '__all__'
        read_only_fields = ['id', 'project', 'user']


class CollaboratorCreateSerializer(ModelSerializer):
    class Meta:
        model = Collaborator
        fields = '__all__'
        read_only_fields = ['id', 'project']

    def validate_user(self, value):
        project = get_object_or_404(Project, id=self.context['request'].parser_context['kwargs'].get('project_pk'))
        if project.created_by == value:
            raise ValidationError('The owner of the project can\'t be a collaborator.')
        return value

    def validate_roles(self, value):
        if 1 in value:
            return [1]
        return value


class ProjectSerializer(ModelSerializer):
    created_by = UserDetailSerializer(many=False, read_only=True)
    collaborators = CollaboratorSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class ProjectDetailSerializer(ModelSerializer):
    created_by = UserDetailSerializer(many=False, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'created_by']


class RecordSerializer(ModelSerializer):
    user = UserDetailSerializer(many=False, read_only=True)

    class Meta:
        model = Record
        fields = '__all__'