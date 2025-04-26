from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import ListModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Q

from .models import Project, Collaborator, Record
from .serializers import CollaboratorSerializer, ProjectDetailSerializer, ProjectSerializer, CollaboratorCreateSerializer, RecordSerializer
from .permissions import HasProjectPermission, IsAdmin, IsAnyRole
from users.models import Notification


class ProjectViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, HasProjectPermission]

    def get_queryset(self):
        user = self.request.user

        if self.action == 'destroy':
            return Project.objects.filter(created_by=user)
        elif self.action == 'list':
            base_filter = Q(created_by=user)
        elif self.action == 'collab':
            base_filter = Q(collaborators__user=user)
        else:
            return Project.objects.filter(Q(created_by=user) | Q(collaborators__user=user))

        name = self.request.query_params.get('name')
        if name:
            base_filter &= Q(name__icontains=name)
        return Project.objects.filter(base_filter)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_serializer_class(self):
        if self.action in ['list', 'collab']:
            return ProjectDetailSerializer
        return ProjectSerializer

    @action(detail=False, methods=['GET'])
    def collab(self, request):
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