from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import ListModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Language, Project, Collaborator, Record
from .serializers import CollaboratorSerializer, ProjectDetailSerializer, ProjectSerializer, CollaboratorCreateSerializer, RecordSerializer
from .permissions import HasProjectPermission, IsAdmin, IsAnyRole
from users.models import Notification


class ProjectViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, HasProjectPermission]

    def get_queryset(self):
        user = self.request.user
        if self.action == 'list':
            base_filter = Q(created_by=user)
        elif self.action == 'collab':
            base_filter = Q(collaborators__user=user)
        else:
            return Project.objects.filter(Q(created_by=user) | Q(collaborators__user=user)).distinct()
        name = self.request.query_params.get('name')
        if name:
            base_filter &= Q(name__icontains=name)
        return Project.objects.filter(base_filter)

    def send_notification(self, project_id: int, type: str, data):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'project_{project_id}',
            {
                'type': 'send_notification',
                'data': {
                    'type': f'project.{type}',
                    'data': data
                }
            }
        )

    def perform_create(self, serializer):
        languages = serializer.validated_data.pop('language_codes')
        languages.append(serializer.validated_data.get('main_language'))
        serializer.save(created_by=self.request.user)
        for lang in set(languages):
            Language.objects.create(
                code=lang,
                project=serializer.instance
            )

    def perform_update(self, serializer):
        instance = self.get_object()
        if serializer.validated_data.get('language_codes'):
            languages = serializer.validated_data.pop('language_codes')
            main_language = serializer.validated_data.get('main_language')
            if main_language:
                languages.append(main_language)
            else:
                languages.append(instance.main_language)
            actual_languages = instance.get_language_codes()
            for lang in actual_languages:
                if not lang in languages:
                    instance.languages.get(code=lang).delete()
                    keys = instance.keys.all()
                    for key in keys:
                        key.translations.filter(language=lang).delete()
            for lang in set(languages):
                if not lang in actual_languages:
                    Language.objects.create(
                        code=lang,
                        project=instance
                    )
        serializer.save()
        self.send_notification(project_id=serializer.instance.id, type='update', data=serializer.data)

    def perform_destroy(self, instance):
        user = self.request.user
        if instance.created_by == user:
            self.send_notification(project_id=instance.id, type='destroy', data=instance.id)
            instance.delete()
        else:
            collaborator = instance.collaborators.get(user=user)
            collaborator.user.notifications.filter(project=instance).delete()
            self.send_notification(project_id=instance.id, type='collab', data=collaborator.id)
            collaborator.delete()

    def get_serializer_class(self):
        if self.action in ['list', 'collab']:
            return ProjectDetailSerializer
        return ProjectSerializer

    @action(detail=False, methods=['GET'])
    def collab(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CollaboratorViewSet(GenericViewSet, CreateModelMixin, UpdateModelMixin, DestroyModelMixin):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return Collaborator.objects.filter(project=self.kwargs['project_pk'])

    def send_notification(self, project_id: int, type: str, data):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'project_{project_id}',
            {
                'type': 'send_notification',
                'data': {
                    'type': f'collaborator.{type}',
                    'data': data
                }
            }
        )

    def perform_create(self, serializer):
        project = get_object_or_404(Project, id=self.kwargs['project_pk'])
        Notification.objects.create(
            user=serializer.validated_data.get('user'),
            type=2,
            project=project
        )
        serializer.save(project=project)
        self.send_notification(project_id=project.id, type='create', data=serializer.data)

    def perform_destroy(self, instance):
        project = get_object_or_404(Project, id=self.kwargs['project_pk'])
        instance.user.notifications.filter(project=project).delete()
        self.send_notification(project_id=project.id, type='destroy', data=instance.id)
        instance.delete()

    def perform_update(self, serializer):
        serializer.save()
        self.send_notification(project_id=serializer.instance.project.id, type='update', data=serializer.data)

    def get_serializer_class(self):
        if self.action == 'create':
            return CollaboratorCreateSerializer
        return CollaboratorSerializer


class RecordViewSet(GenericViewSet, ListModelMixin):
    serializer_class = RecordSerializer
    permission_classes = [IsAuthenticated, IsAnyRole]
    pagination_class = None

    def get_queryset(self):
        return Record.objects.filter(project=self.kwargs['project_pk'])