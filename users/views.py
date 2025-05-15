from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.mixins import ListModelMixin, DestroyModelMixin
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Value
from django.db.models.functions import Concat

from .models import User, Notification
from .serializers import UserCreateSerializer, UserDetailSerializer, UserSerializer, NotificationSerializer


class UserViewSet(ModelViewSet):
    pagination_class = None

    def get_queryset(self):
        name = self.request.query_params.get('name')
        if self.action == 'list' and name:
            return User.objects.annotate(
                name=Concat('first_name', Value(' '), 'last_name')
            ).filter(name__icontains=name)
        return User.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'list':
            return UserDetailSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'profile':
            return super().get_permissions()
        return []

    @action(detail=False, methods=['GET', 'PUT', 'PATCH', 'DELETE'])
    def profile(self, request, *args, **kwargs):
        instance = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        elif request.method == 'PUT' or request.method == 'PATCH':
            serializer = self.get_serializer(instance, data=request.data, partial=(request.method == 'PATCH'))
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            if getattr(instance, '_prefetched_objects_cache', None):
                instance._prefetched_objects_cache = {}
            return Response(serializer.data)
        elif request.method == 'DELETE':
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)



class NotificationViewSet(GenericViewSet, ListModelMixin, DestroyModelMixin):
    serializer_class = NotificationSerializer
    pagination_class = None

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)