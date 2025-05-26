from django.forms import EmailField
from rest_framework.serializers import ModelSerializer, CharField
from rest_framework.exceptions import ValidationError

from .models import Notification, User


class UserSerializer(ModelSerializer):
    email = EmailField()
    password = CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'image', 'language', 'format_24h', 'date_format', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise ValidationError('User with this email already exists.')
        return value


class UserCreateSerializer(ModelSerializer):
    password = CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'first_name', 'last_name', 'image', 'language', 'format_24h', 'date_format', 'created_at', 'updated_at']
        read_only_fields = ['id', 'image', 'language', 'format_24h', 'date_format', 'created_at', 'updated_at']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise ValidationError('User with this email already exists.')
        return value


class UserDetailSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'image']


from projects.serializers import ProjectDetailSerializer


class NotificationSerializer(ModelSerializer):
    project = ProjectDetailSerializer(many=False, read_only=True)

    class Meta:
        model = Notification
        fields = '__all__'