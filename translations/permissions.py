from rest_framework.permissions import BasePermission

from projects.models import Collaborator
from .models import Comment


class IsCommentOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Comment):
            return False
        
        if view.action == 'destroy':
            project = obj.translation.key.project
            if project.created_by == request.user:
                return True

            collaborator = Collaborator.objects.get(user=request.user, project=project)
            if Collaborator.Role.ADMIN in collaborator.roles:
                return True

        if view.action in ['update', 'partial_update', 'destroy']:
            return obj.created_by == request.user

        return True