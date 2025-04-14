from django.shortcuts import get_object_or_404
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated

from projects.permissions import IsAdminOrDeveloper
from projects.models import Project, Record
from .models import Key
from .serializers import KeySerializer


class KeyViewSet(GenericViewSet, CreateModelMixin, UpdateModelMixin, DestroyModelMixin):
    serializer_class = KeySerializer
    permission_classes = [IsAuthenticated, IsAdminOrDeveloper]

    def get_queryset(self):
        return Key.objects.filter(project=self.kwargs['project_pk'])

    def perform_create(self, serializer):
        project = get_object_or_404(Project, id=self.kwargs['project_pk'])
        Record.objects.create(
            type=1,
            user=self.request.user,
            project=project
        )
        serializer.save(project=project, created_by=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        Record.objects.create(
            type=3,
            user=self.request.user,
            project=instance.project
        )
        return super().perform_update(serializer)

    def perform_destroy(self, instance):
        Record.objects.create(
            type=2,
            user=self.request.user,
            project=instance.project
        )
        return super().perform_destroy(instance)