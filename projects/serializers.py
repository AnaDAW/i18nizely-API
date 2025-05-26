from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.serializers import ModelSerializer, CharField, ListField

from utils.language_util import LanguageUtil

from .models import Language, Project, Collaborator, Record
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


class LanguageSerializer(ModelSerializer):
    class Meta:
        model = Language
        fields = '__all__'


class ProjectSerializer(ModelSerializer):
    created_by = UserDetailSerializer(many=False, read_only=True)
    collaborators = CollaboratorSerializer(many=True, read_only=True)
    languages = LanguageSerializer(many=True, read_only=True)
    language_codes = ListField(child=CharField(max_length=2), write_only=True, required=True)

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def validate_main_language(self, value):
        if not value in LanguageUtil.language_codes:
            raise ValidationError('The language is not supported or not exists.')
        return value

    def validate_language_codes(self, value):
        languages = []
        for lang in value:
            if lang in LanguageUtil.language_codes:
                languages.append(lang)
        if not languages:
            raise ValidationError('Languages not supported or not exists.')
        return languages


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