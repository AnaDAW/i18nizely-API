from datetime import datetime
from django.shortcuts import get_object_or_404
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from keys.models import Key
from projects.serializers import LanguageSerializer
from .permissions import IsCommentOwner
from .models import Translation, Version, Comment
from projects.models import Language, Record
from .serializers import TranslationCreateSerializer, TranslationReviewSerializer, TranslationSerializer, VersionSerializer, CommentSerializer
from projects.permissions import IsAdminOrTranslator, IsAnyRole


class TranslationViewSet(GenericViewSet, CreateModelMixin, UpdateModelMixin):
    permission_classes = [IsAuthenticated, IsAdminOrTranslator]

    def get_queryset(self):
        return Translation.objects.filter(key=self.kwargs['key_pk'])

    def get_serializer_class(self):
        if self.action == 'review':
            return TranslationReviewSerializer
        elif self.action == 'create':
            return TranslationCreateSerializer
        return TranslationSerializer

    def send_notification(self, project_id: int, type: str, data):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'project_{project_id}',
            {
                'type': 'send_notification',
                'data': {
                    'type': f'translation.{type}',
                    'data': data
                }
            }
        )

    def perform_create(self, serializer):
        key = get_object_or_404(Key, id=self.kwargs['key_pk'])
        language = Language.objects.get(project=key.project, code=serializer.validated_data.get('language'))
        language.translation_count += 1
        language.save()
        serializer.save(key=key, created_by=self.request.user)
        self.send_notification(project_id=key.project.id, type='language', data=LanguageSerializer(language).data)
        self.send_notification(project_id=key.project.id, type='create', data=serializer.data)

    def perform_update(self, serializer):
        instance = self.get_object()
        language = instance.key.project.languages.get(code=instance.language)
        if self.action == 'review':
            is_reviewed = self.request.data.get('is_reviewed')
            if is_reviewed and not instance.is_reviewed:
                Record.objects.create(
                    type=6,
                    user=self.request.user,
                    project=instance.key.project
                )
                language.reviewed_count += 1
                language.save()
                serializer.save(reviewed_by=self.request.user, reviewed_at=datetime.now())
            elif not is_reviewed and instance.is_reviewed:
                language.reviewed_count -= 1
                language.save()
                serializer.save(reviewed_by=None, reviewed_at=None)
        else:
            Version.objects.create(
                text=instance.text,
                translation=instance,
                created_by=instance.created_by,
                created_at=instance.updated_at
            )
            Record.objects.create(
                type=5,
                user=self.request.user,
                project=instance.key.project
            )
            if instance.is_reviewed:
                language.reviewed_count -= 1
                language.save()
            serializer.save(
                is_reviewed=False,
                reviewed_at=None,
                reviewed_by=None,
                updated_at=datetime.now()
            )
            self.send_notification(project_id=instance.key.project.id, type='version', data=self.get_serializer(instance).data)
        self.send_notification(project_id=instance.key.project.id, type='language', data=LanguageSerializer(language).data)
        self.send_notification(project_id=instance.key.project.id, type='update', data=serializer.data)

    @action(detail=True, methods=['PATCH'])
    def review(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        return Response(serializer.data)


class VersionViewSet(GenericViewSet, ListModelMixin):
    serializer_class = VersionSerializer
    permission_classes = [IsAuthenticated, IsAnyRole]
    pagination_class = None

    def get_queryset(self):
        return Version.objects.filter(translation=self.kwargs['translation_pk'])


class CommentViewSet(GenericViewSet, ListModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsAnyRole, IsCommentOwner]
    pagination_class = None

    def get_queryset(self):
        return Comment.objects.filter(translation=self.kwargs['translation_pk'])

    def send_notification(self, project_id: int, type: str, data):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'project_{project_id}',
            {
                'type': 'send_notification',
                'data': {
                    'type': f'comment.{type}',
                    'data': data
                }
            }
        )

    def perform_create(self, serializer):
        translation = get_object_or_404(Translation, id=self.kwargs['translation_pk'])
        serializer.save(translation=translation, created_by=self.request.user)
        self.send_notification(project_id=serializer.instance.translation.key.project.id, type='create', data=serializer.data)
    
    def perform_update(self, serializer):
        serializer.save()
        self.send_notification(project_id=serializer.instance.translation.key.project.id, type='update', data=serializer.data)
    
    def perform_destroy(self, instance):
        instance.delete()
        self.send_notification(project_id=instance.translation.key.project.id, type='destroy', data=instance.id)