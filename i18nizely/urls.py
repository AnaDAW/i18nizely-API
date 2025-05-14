"""
URL configuration for i18nizely project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_nested.routers import DefaultRouter, NestedDefaultRouter

from users.views import NotificationViewSet, UserViewSet
from projects.views import ProjectViewSet, CollaboratorViewSet, RecordViewSet
from keys.views import KeyViewSet
from translations.views import TranslationViewSet, VersionViewSet, CommentViewSet


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'projects', ProjectViewSet, basename='project')

project_router = NestedDefaultRouter(router, r'projects', lookup='project')
project_router.register(r'collaborators', CollaboratorViewSet, basename='project-collaborators')
project_router.register(r'record', RecordViewSet, basename='project-record')
project_router.register(r'keys', KeyViewSet, basename='project-keys')

key_router = NestedDefaultRouter(project_router, r'keys', lookup='key')
key_router.register(r'translations', TranslationViewSet, basename='key-translations')

translation_router = NestedDefaultRouter(key_router, r'translations', lookup='translation')
translation_router.register(r'versions', VersionViewSet, basename='translation-versions')
translation_router.register(r'comments', CommentViewSet, basename='translation-comments')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(project_router.urls)),
    path('', include(key_router.urls)),
    path('', include(translation_router.urls)),
    path('auth/login/', TokenObtainPairView.as_view()),
    path('auth/refresh/', TokenRefreshView.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # only for development