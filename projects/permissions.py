from rest_framework.permissions import BasePermission
from projects.models import Collaborator, Project


class HasProjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Project):
            return False
        
        if obj.created_by == request.user:
            return True
        
        try:
            collaborator = Collaborator.objects.get(user=request.user, project=obj)
        except Collaborator.DoesNotExist:
            return False

        if view.action == 'retrieve':
            return True
        elif view.action in ['update', 'partial_update']:
            return collaborator.role == Collaborator.Role.ADMIN
        
        return False


class ProjectRolePermission(BasePermission):
    allowed_roles = []

    def has_permission(self, request, view):
        project_id = view.kwargs.get('project_pk', None)
        if not project_id:
            return False
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return False
        
        return self.has_role_permission(view.action, 'list', project, request.user)


    def has_object_permission(self, request, view, obj):
        project = None
        if hasattr(obj, 'project'):
            project = obj.project
        elif hasattr(obj, 'key'):
            project = obj.key.project
        elif hasattr(obj, 'translation'):
            project = obj.translation.key.project

        if not project:
            return False

        return self.has_role_permission(view.action, 'retrieve', project, request.user)


    def has_role_permission(self, action, action_name,  project, user):
        if project.created_by == user:
            return True

        try:
            collaborator = Collaborator.objects.get(user=user, project=project)
        except Collaborator.DoesNotExist:
            return False

        if action == action_name:
            return True

        return collaborator.role in self.allowed_roles


class IsAdmin(ProjectRolePermission):
    allowed_roles = [Collaborator.Role.ADMIN]

class IsAdminOrDeveloper(ProjectRolePermission):
    allowed_roles = [Collaborator.Role.ADMIN, Collaborator.Role.DEVELOPER]

class IsAdminOrTranslator(ProjectRolePermission):
    allowed_roles = [Collaborator.Role.ADMIN, Collaborator.Role.TRANSLATOR]

class IsAdminOrReviewer(ProjectRolePermission):
    allowed_roles = [Collaborator.Role.ADMIN, Collaborator.Role.REVIEWER]

class IsAnyRole(ProjectRolePermission):
    allowed_roles = [Collaborator.Role.ADMIN, Collaborator.Role.DEVELOPER, Collaborator.Role.TRANSLATOR, Collaborator.Role.REVIEWER]