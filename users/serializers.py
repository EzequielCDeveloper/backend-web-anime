from rest_framework import serializers
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer principal para el modelo User (gestión administrativa en UserApiViewSet).
    
    CORRECCIÓN DE SEGURIDAD 1:
    La contraseña está configurada como `write_only=True` y se elimina explícitamente en
    `to_representation()`. De esta forma NUNCA se expone el hash de contraseña en ninguna
    respuesta de la API (GET /users/, GET /auth/me/, POST, PUT, PATCH).
    
    CORRECCIÓN DE SEGURIDAD 2:
    En el método `update`, solo se actualiza la contraseña si viene explícitamente en los datos
    validados (`validated_data`). Si no viene contraseña, se conserva la contraseña existente
    del usuario en lugar de asignarle la del usuario autenticado (falla grave del manual).
    """
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        style={'input_type': 'password'},
        help_text="Contraseña (solo escritura, jamás se retorna en la respuesta)."
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'telefono',
            'password',
            'is_active',
            'is_staff',
            'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'email': {'required': True},
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        # Solo modificar la contraseña si se envió una no vacía
        if password:
            user.set_password(password)
            user.save()
        return user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Doble candado defensivo: eliminar cualquier rastro de password
        data.pop('password', None)
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer específico para el perfil personal del usuario autenticado (/api/v1/auth/me/).
    
    CORRECCIÓN DE SEGURIDAD (MASS ASSIGNMENT & ESCALADA DE PRIVILEGIOS - CWE-915):
    Los campos sensibles de autorización e integridad ('is_staff', 'is_active', 'id', 'date_joined')
    están blindados en `read_only_fields`.
    Un usuario común autenticado jamás podrá auto-asignarse privilegios de staff o administrador
    mediante peticiones PUT o PATCH maliciosas.
    """
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        style={'input_type': 'password'},
        help_text="Contraseña (solo escritura, jamás se retorna en la respuesta)."
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'telefono',
            'password',
            'is_active',
            'is_staff',
            'date_joined',
        ]
        read_only_fields = ['id', 'is_staff', 'is_active', 'date_joined']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'email': {'required': True},
        }

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('password', None)
        return data


class RegisterUserSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro público de nuevos usuarios.
    Permite omitir el username, autogenerándolo de forma única y segura a partir del email.
    """
    username = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Nombre de usuario (opcional; si se omite, se autogenera de forma única desde el email)."
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Contraseña de al menos 8 caracteres."
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'},
        help_text="Confirmación de contraseña (opcional pero validada si se provee)."
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'telefono', 'password', 'password_confirm']
        read_only_fields = ['id']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        if password_confirm is not None and password != password_confirm:
            raise serializers.ValidationError({"password_confirm": "Las contraseñas no coinciden."})
        return attrs

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        return value

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        username = validated_data.pop('username', '').strip()
        user = User(username=username, **validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('password', None)
        data.pop('password_confirm', None)
        return data
