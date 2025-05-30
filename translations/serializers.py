from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.serializers import ModelSerializer, BooleanField, CharField

from projects.models import Project

from .models import Translation, Version, Comment
from users.serializers import UserDetailSerializer


class TranslationSerializer(ModelSerializer):
    created_by = UserDetailSerializer(many=False, read_only=True)
    reviewed_by = UserDetailSerializer(many=False, read_only=True)

    class Meta:
        model = Translation
        fields = '__all__'
        read_only_fields = ['id', 'language', 'key', 'is_reviewed', 'reviewed_by', 'reviewed_at', 'created_by', 'created_at', 'updated_at']


class TranslationCreateSerializer(ModelSerializer):
    text = CharField(required=True)
    created_by = UserDetailSerializer(many=False, read_only=True)
    reviewed_by = UserDetailSerializer(many=False, read_only=True)

    class Meta:
        model = Translation
        fields = '__all__'
        read_only_fields = ['id', 'key', 'is_reviewed', 'reviewed_by', 'reviewed_at', 'created_by', 'created_at', 'updated_at']

    def validate_language(self, value):
        key = self.context['request'].parser_context['kwargs'].get('key_pk')
        if Translation.objects.filter(key=key, language=value).exists():
            raise ValidationError('Translation with this language already exists.')
        project = get_object_or_404(Project, id=self.context['request'].parser_context['kwargs'].get('project_pk'))
        languages = project.get_language_codes()
        if value not in languages:
            raise ValidationError(f'Language \'{value}\' is not enabled for this project.')
        return value


class TranslationReviewSerializer(ModelSerializer):
    is_reviewed = BooleanField(required=True)
    created_by = UserDetailSerializer(many=False, read_only=True)
    reviewed_by = UserDetailSerializer(many=False, read_only=True)

    class Meta:
        model = Translation
        fields = '__all__'
        read_only_fields = ['id', 'language', 'text', 'key', 'reviewed_by', 'reviewed_at', 'created_by', 'created_at', 'updated_at']


class TranslationDetailSerializer(ModelSerializer):
    created_by = UserDetailSerializer(many=False, read_only=True)
    reviewed_by = UserDetailSerializer(many=False, read_only=True)

    class Meta:
        model = Translation
        fields = '__all__'


class VersionSerializer(ModelSerializer):
    created_by = UserDetailSerializer(many=False, read_only=True)

    class Meta:
        model = Version
        fields = '__all__'


class CommentSerializer(ModelSerializer):
    created_by = UserDetailSerializer(many=False, read_only=True)

    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ['id', 'translation', 'created_by', 'created_at', 'updated_at']