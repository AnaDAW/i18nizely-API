from datetime import datetime
from django.shortcuts import get_object_or_404
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from keys.models import Key
from .permissions import IsCommentOwner
from .models import Translation, Version, Comment
from projects.models import Record
from .serializers import TranslationCreateSerializer, TranslationReviewSerializer, TranslationSerializer, VersionSerializer, CommentSerializer
from projects.permissions import IsAdminOrTranslator, IsAnyRole


class TranslationViewSet(GenericViewSet, CreateModelMixin, UpdateModelMixin):
    permission_classes = [IsAuthenticated, IsAdminOrTranslator]

    def get_queryset(self):
        return Translation.objects.filter(key=self.kwargs['key_pk'])

    def perform_create(self, serializer):
        key = get_object_or_404(Key, id=self.kwargs['key_pk'])
        serializer.save(key=key, created_by=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        if self.action == 'review':
            is_reviewed = self.request.data.get('is_reviewed')
            if is_reviewed:
                Record.objects.create(
                    type=6,
                    user=self.request.user,
                    project=instance.key.project
                )
                serializer.save(reviewed_by=self.request.user, reviewed_at=datetime.now())
            else:
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
            serializer.save(
                is_reviewed=False,
                reviewed_at=None,
                reviewed_by=None,
                updated_at=datetime.now()
            )

    def get_serializer_class(self):
        if self.action == 'review':
            return TranslationReviewSerializer
        elif self.action == 'create':
            return TranslationCreateSerializer
        return TranslationSerializer

    @action(detail=True, methods=['PATCH'])
    def review(self, request, project_pk=None, key_pk=None, pk=None):
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

    def get_queryset(self):
        return Version.objects.filter(translation=self.kwargs['translation_pk'])


class CommentViewSet(GenericViewSet, ListModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsAnyRole, IsCommentOwner]

    def get_queryset(self):
        return Comment.objects.filter(translation=self.kwargs['translation_pk'])

    def perform_create(self, serializer):
        translation = get_object_or_404(Translation, id=self.kwargs['translation_pk'])
        serializer.save(translation=translation, created_by=self.request.user)