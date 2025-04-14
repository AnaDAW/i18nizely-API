from rest_framework.serializers import ModelSerializer, ValidationError

from .models import Key
from translations.serializers import TranslationDetailSerializer
from users.serializers import UserDetailSerializer


class KeySerializer(ModelSerializer):
    translations = TranslationDetailSerializer(many=True, read_only=True)
    created_by = UserDetailSerializer(many=False, read_only=True)

    class Meta:
        model = Key
        fields = '__all__'
        read_only_fields = ['id', 'project', 'created_by', 'created_at', 'updated_at']

    def validate_name(self, value):
        if ' ' in value:
            raise ValidationError('The key can\'t have spaces.')
        return value

    def validate_name(self, value):
        project = self.context['request'].parser_context['kwargs'].get('project_pk')
        if Key.objects.filter(name=value, project=project).exists():
            raise ValidationError('Key with this name already exists.')
        return value