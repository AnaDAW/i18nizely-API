from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import ListModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .models import Project, Collaborator, Record
from .serializers import CollaboratorSerializer, ProjectDetailSerializer, ProjectSerializer, CollaboratorCreateSerializer, RecordSerializer
from .permissions import HasProjectPermission, IsAdmin, IsAnyRole
from users.models import Notification


class ProjectViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, HasProjectPermission]

    def get_queryset(self):
        user_id = self.request.user
        return Project.objects.filter(Q(created_by=user_id) | Q(collaborators__user=user_id))

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectDetailSerializer
        return ProjectSerializer


class CollaboratorViewSet(GenericViewSet, CreateModelMixin, UpdateModelMixin, DestroyModelMixin):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return Collaborator.objects.filter(project=self.kwargs['project_pk'])

    def perform_create(self, serializer):
        project = get_object_or_404(Project, id=self.kwargs['project_pk'])
        Notification.objects.create(
            user=serializer.validated_data.get('user'),
            type=2,
            project=project
        )
        serializer.save(project=project)

    def get_serializer_class(self):
        if self.action == 'create':
            return CollaboratorCreateSerializer
        return CollaboratorSerializer


class RecordViewSet(GenericViewSet, ListModelMixin):
    serializer_class = RecordSerializer
    permission_classes = [IsAuthenticated, IsAnyRole]

    def get_queryset(self):
        return Record.objects.filter(project=self.kwargs['project_pk'])