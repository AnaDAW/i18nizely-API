from datetime import datetime
import json, io
from zipfile import ZipFile
from django.shortcuts import get_object_or_404
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from projects.permissions import IsAdminOrDeveloper
from projects.models import Project, Record, Language
from projects.serializers import LanguageSerializer
from translations.models import Translation, Version
from .models import Key
from .serializers import KeyCreateSerializer, KeySerializer
from users.models import User


class KeyViewSet(GenericViewSet, ListModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin):
    permission_classes = [IsAuthenticated, IsAdminOrDeveloper]

    def get_queryset(self):
        name = self.request.query_params.get('name')
        if name:
            return Key.objects.filter(Q(project=self.kwargs['project_pk']) & Q(name__icontains=name))
        return Key.objects.filter(project=self.kwargs['project_pk'])

    def get_serializer_class(self):
        if self.action == 'create':
            return KeyCreateSerializer
        return KeySerializer

    def send_notification(self, project_id: int, type: str, data):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'project_{project_id}',
            {
                'type': 'send_notification',
                'data': {
                    'type': f'key.{type}',
                    'data': data
                }
            }
        )

    def perform_create(self, serializer):
        project = get_object_or_404(Project, id=self.kwargs['project_pk'])
        Record.objects.create(
            type=1,
            user=self.request.user,
            project=project
        )
        translation = serializer.validated_data.pop('translation')
        serializer.save(project=project, created_by=self.request.user)
        Translation.objects.create(
            key=serializer.instance,
            created_by=self.request.user,
            language=project.main_language,
            text=translation
        )
        language = project.languages.get(code=project.main_language)
        language.translation_count += 1
        language.save()
        self.send_notification(project_id=project.id, type='language', data=LanguageSerializer(language).data)
        self.send_notification(project_id=project.id, type='create', data=serializer.data)

    def perform_update(self, serializer):
        instance = self.get_object()
        Record.objects.create(
            type=3,
            user=self.request.user,
            project=instance.project
        )
        serializer.save()
        self.send_notification(project_id=instance.project.id, type='update', data=serializer.data)

    def perform_destroy(self, instance):
        project = instance.project
        Record.objects.create(
            type=2,
            user=self.request.user,
            project=project
        )
        translations = instance.translations.all()
        languages = []
        for trans in translations:
            lang = project.languages.get(code=trans.language)
            lang.translation_count -= 1
            lang.save()
            languages.append(lang)
        self.send_notification(project_id=project.id, type='languages', data=LanguageSerializer(languages, many=True).data)
        self.send_notification(project_id=project.id, type='destroy', data=instance.id)
        instance.delete()
    
    @action(detail=False, methods=['POST'], url_path='import')
    def import_keys(self, request, *args, **kwargs):
        files = request.FILES
        if not files:
            return Response({'detail': 'No files sent.'}, status=status.HTTP_400_BAD_REQUEST)
        project = get_object_or_404(Project, id=kwargs['project_pk'])
        languages = project.get_language_codes()
        saved_keys = []
        for lang in files:
            if lang not in languages:
                continue
            try:
                content = json.load(files[lang])
                saved_keys = self.save_keys(request.user, project, lang, content)
            except Exception as e:
                return Response({'detail': 'File type not allowed.', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(saved_keys, many=True)
        self.send_notification(project_id=project.id, type='languages', data=LanguageSerializer(project.languages.all(), many=True).data)
        self.send_notification(project_id=project.id, type='import', data=serializer.data)
        return Response(serializer.data)

    def save_keys(self, user: User, project: Project, lang: str, body: dict, key_name: str = ''):
        saved_keys = []
        for key in body:
            if key[0] == '@':
                continue
            formated_key = self.format_key(key)
            key_name += formated_key
            if isinstance(body[key], str):
                if not body[key]:
                    continue
                try:
                    language = project.languages.get(code=lang)
                    actual_key = project.keys.get(name=key_name)
                    actual_trans = actual_key.translations.get(language=lang)
                    if actual_trans.text != body[key]:
                        self.update_translation(actual_trans, user, project, language, body[key])
                        saved_keys.append(actual_key)
                except Key.DoesNotExist:
                    new_key = self.create_key(key_name, user, project, language, lang, body[key])
                    saved_keys.append(new_key)
                except Translation.DoesNotExist:
                    self.create_translation(actual_key, user, language, lang, body[key])
                    saved_keys.append(actual_key)
            elif isinstance(body[key], dict):
                key_name += '.'
                nested_keys = self.save_keys(user, project, lang, body[key], key_name)
                saved_keys.extend(nested_keys)
                key_name = key_name[:-1]
            key_name = key_name.replace(formated_key, '')
        return set(saved_keys)

    def format_key(self, key: str) -> str :
        formated_key = ''
        for c in key:
            if c == '_':
                formated_key += '.'
                continue
            if c.isupper():
                formated_key += '-'
            formated_key += c.lower()
        return formated_key

    def update_translation(self, translation: Translation, user: User, project: Project, language: Language, text: str):
        Version.objects.create(
            text=translation.text,
            translation=translation,
            created_by=translation.created_by,
            created_at=translation.updated_at
        )
        Record.objects.create(
            type=5,
            user=user,
            project=project
        )
        if translation.is_reviewed:
            language.reviewed_count -= 1
            language.save()
            translation.is_reviewed = False
            translation.reviewed_at = None
            translation.reviewed_by = None
        translation.text = text
        translation.updated_at = datetime.now()
        translation.save()
    
    def create_key(self, key_name: str, user: User, project: Project, language: Language, lang: str, text: str):
        Record.objects.create(
            type=1,
            user=user,
            project=project
        )
        key = Key.objects.create(
            name=key_name,
            project=project,
            created_by=user
        )
        self.create_translation(key, user, language, lang, text)
        return key
    
    def create_translation(self, key: Key, user: User, language: Language, lang: str, text: str):
        Translation.objects.create(
            text=text,
            language=lang,
            key=key,
            created_by=user
        )
        language.translation_count += 1
        language.save()

    @action(detail=False, methods=['GET'], url_path='export')
    def export_keys(self, request, *args, **kwargs):
        file_types = request.query_params.getlist('file_type')
        languages = request.query_params.getlist('languages')
        only_reviewed = request.query_params.get('only_reviewed') in ['True', 'true', '1']
        project = get_object_or_404(Project, id=kwargs['project_pk'])
        if not languages:
            languages = project.get_language_codes()
        if not file_types:
            file_types = ['json', 'arb']
        buffer = io.BytesIO()
        writer = ZipFile(buffer, 'w')
        for type in file_types:
            for lang in languages:
                file = self.format_file(type, project, lang, only_reviewed)
                if file:
                    writer.writestr(f'{lang}.{type}', file)
        buffer_size = buffer.tell()
        writer.close()
        if buffer_size == 0:
            response = Response(status=status.HTTP_204_NO_CONTENT)
        else:
            buffer.seek(0)
            response = HttpResponse(buffer.getvalue(), content_type='application/zip')
            filename = project.name.replace(' ', '-')
            response['Content-Disposition'] = f'attachment; filename="{filename}.zip"'
        buffer.close()
        return response
    
    def format_file(self, file_type: str, project: Project, lang: str, only_reviewed: bool):
        formated_file = {}
        keys = project.keys.all()
        for key in keys:
            name_list = key.name.split('.')
            translation = key.translations.filter(language=lang).first()
            if not translation or (only_reviewed and not translation.is_reviewed):
                continue
            text = translation.text
            if not text:
                continue
            if file_type == 'json':
                self.format_json(formated_file, name_list, text)
            elif file_type == 'arb':
                self.format_arb(formated_file, name_list, text)
        if not formated_file:
            return
        return json.dumps(formated_file, indent=2).encode('utf-8')

    def format_json(self, file: dict, name_list: list, translation: str):
        if len(name_list) == 1:
            file[name_list[0]] = translation
        else:
            name_dict = file
            for name in name_list[:-1]:
                if name not in name_dict or not isinstance(name_dict[name], dict):
                    name_dict[name] = {}
                name_dict = name_dict[name]
            name_dict[name_list[-1]] = translation

    def format_arb(self, file: dict, name_list: list, translation: str):
            key_name = ''
            for name in name_list:
                word_list = name.split('-')
                key_name += word_list.pop(0)
                for word in word_list:
                    key_name += word[0].upper()
                    key_name += word[1:]
                key_name += '_'
            key_name = key_name[:-1]
            file[key_name] = translation