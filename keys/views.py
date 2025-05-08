from django.shortcuts import get_object_or_404
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from projects.permissions import IsAdminOrDeveloper
from projects.models import Project, Record
from translations.models import Translation
from .models import Key
from .serializers import KeyCreateSerializer, KeySerializer


class KeyViewSet(GenericViewSet, ListModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin):
    serializer_class = KeySerializer
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

    def perform_create(self, serializer):
        project = get_object_or_404(Project, id=self.kwargs['project_pk'])
        Record.objects.create(
            type=1,
            user=self.request.user,
            project=project
        )
        translation = serializer.validated_data.pop('translation')
        key = serializer.save(project=project, created_by=self.request.user)
        if translation:
            Translation.objects.create(
                key=key,
                created_by=self.request.user,
                language=project.main_language,
                text=translation
            )

    def perform_update(self, serializer):
        instance = self.get_object()
        Record.objects.create(
            type=3,
            user=self.request.user,
            project=instance.project
        )
        serializer.save()

    def perform_destroy(self, instance):
        Record.objects.create(
            type=2,
            user=self.request.user,
            project=instance.project
        )
        return super().perform_destroy(instance)